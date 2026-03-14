#Authored by Daniel F MacDonald and ChatGPT aka The Generals
#Gemini, docstring-ing and added code enhancements.
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import requests
import subprocess
import time
from datetime import datetime
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.mixin.agent_summary_mixin import AgentSummaryMixin
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent, AgentSummaryMixin):
    """
    A watchdog agent that monitors a MySQL/MariaDB service. It checks if the service is running
    and listening on its designated port, attempts to restart it upon failure, and sends alerts
    and structured data reports about its status.
    """
    def __init__(self):
        """Initializes the MySQLWatchdog agent, setting up configuration parameters and statistics tracking."""
        super().__init__()
        self.name = "MySQLWatchdog"
        self.last_restart = None
        self.failed_restart_count = 0
        self.disabled = False
        cfg = self.tree_node.get("config", {})
        self.interval = cfg.get("check_interval_sec", 20)
        self.mysql_port = cfg.get("mysql_port", 3306)
        self.socket_path = cfg.get("socket_path", "/var/run/mysqld/mysqld.sock")
        self.failed_restart_limit = cfg.get("restart_limit", 3)
        self.alert_role = cfg.get("alert_to_role", None)
        self.report_role = cfg.get("report_to_role", None)
        self.alert_cooldown = cfg.get("alert_cooldown", 300)
        self.alert_thresholds = cfg.get("alert_thresholds", {"uptime_pct_min": 90, "slow_restart_sec": 10})
        self.service_name = cfg.get("service_name", "mysql")
        self.comm_targets = cfg.get("comm_targets", [])
        self.stats = {
            "date": self.today(),
            "restarts": 0,
            "uptime_sec": 0,
            "downtime_sec": 0,
            "last_status": None,
            "last_status_change": time.time(),
            "last_state": None
        }
        self.last_alerts = {}

    def today(self):
        """
        Returns the current date as a string in YYYY-MM-DD format.

        Returns:
            str: The current date.
        """
        return datetime.now().strftime("%Y-%m-%d")

    def is_mysql_running(self):
        """
        Checks if the MySQL service is active using systemd.

        Returns:
            bool: True if the service is running, False otherwise.
        """
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "--quiet", self.service_name],
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            self.log(f"[WATCHDOG][ERROR] Failed to check MySQL status: {e}")
            return False

    def restart_mysql(self):
        """
        Attempts to restart the MySQL service. If restarts fail repeatedly,
        it disables itself to prevent a restart loop.
        """
        if self.disabled:
            self.log("[WATCHDOG][DISABLED] Agent is disabled due to repeated failures.")
            return

        self.log("[WATCHDOG] Attempting to restart MySQL...")
        try:
            subprocess.run(["systemctl", "restart", self.service_name], check=True)
            self.log("[WATCHDOG] ✅ MySQL successfully restarted.")
            self.post_restart_check()
            self.last_restart = time.time()
            self.stats["restarts"] += 1
            self.failed_restart_count = 0  # reset on success
        except Exception as e:
            self.failed_restart_count += 1
            self.log(f"[WATCHDOG][FAIL] Restart failed: {e}")
            if self.failed_restart_count >= self.failed_restart_limit:
                self.disabled = True
                self.send_simple_alert("🛑 MySQL watchdog disabled after repeated restart failures.")
                self.log("[WATCHDOG][DISABLED] Max restart attempts reached. Watchdog disabled.")

    def update_status_metrics(self, is_running):
        """
        Updates the uptime and downtime statistics based on the current service status.

        Args:
            is_running (bool): The current running state of the service.
        """
        now = time.time()
        last = self.stats.get("last_status")
        elapsed = now - self.stats.get("last_status_change", now)
        # If state changed (or first run), update timing
        if last is not None:
            if last:
                self.stats["uptime_sec"] += elapsed
            else:
                self.stats["downtime_sec"] += elapsed

        self.stats["last_status"] = is_running
        self.stats["last_status_change"] = now

    def is_socket_accessible(self):
        """
        Checks if the MySQL socket file exists.

        Returns:
            bool: True if the socket exists, False otherwise.
        """
        return os.path.exists(self.socket_path)

    def is_mysql_listening(self):
        """
        Checks if any process is listening on the configured MySQL port.

        Returns:
            bool: True if the port is being listened on, False otherwise.
        """
        try:
            out = subprocess.check_output(["ss", "-ltn"])
            return f":{self.mysql_port}".encode() in out
        except Exception as e:
            self.log(f"[WATCHDOG][ERROR] Failed to scan ports: {e}")
            return False

    def worker_pre(self):
        """Logs the systemd unit being watched before the main worker loop starts."""
        self.log(f"[WATCHDOG] Watching systemd unit: {self.service_name}")

    def worker(self, config: dict = None, identity: IdentityObject = None):
        """
        The main worker loop. It checks the health of the MySQL service, handles state
        changes (e.g., failure, recovery), triggers restarts, and sends alerts/reports.

        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
            identity (IdentityObject, optional): Identity object for the agent. Defaults to None.
        """
        # Handle daily summary/report roll
        self.maybe_roll_day("mysql")

        # Health check
        is_healthy = self.is_mysql_running() and self.is_mysql_listening()
        last_state = self.stats.get("last_state")

        # First run: establish baseline
        if last_state is None:
            self.log(f"[WATCHDOG] Establishing baseline status for {self.service_name}...")
            self.stats["last_state"] = is_healthy
            self.stats["last_status_change"] = time.time()
            interruptible_sleep(self, self.interval)
            return

        # If state changed
        if is_healthy != last_state:
            self.update_status_metrics(is_healthy)

            if is_healthy:
                # Service just recovered
                self.log(f"[WATCHDOG] ✅ {self.service_name} has recovered.")
                self.send_simple_alert(f"✅ {self.service_name.capitalize()} has recovered and is now online.")
                self.send_data_report("RECOVERED", "INFO", "Service is back online and ports are open.")
            else:
                # Service just failed
                self.log(f"[WATCHDOG] ❌ {self.service_name} is NOT healthy.")
                diagnostics = self.collect_mysql_diagnostics()
                if self.should_alert("mysql-down"):
                    self.send_simple_alert(f"❌ {self.service_name.capitalize()} is DOWN. Attempting restart...")
                self.send_data_report(
                    status="DOWN", severity="CRITICAL",
                    details=f"Service {self.service_name} is not running or ports are not open.",
                    metrics=diagnostics
                )
                self.restart_mysql()

            # Always update last_state after alert/report
            self.stats["last_state"] = is_healthy
        else:
            # Stable, just accumulate
            self.update_status_metrics(is_healthy)
            if hasattr(self, "debug") and getattr(self.debug, "is_enabled", lambda: False)():
                self.log(f"[WATCHDOG] {'✅' if is_healthy else '❌'} {self.service_name} status is stable.")

        interruptible_sleep(self, self.interval)

    def should_alert(self, key):
        """
        Determines if an alert should be sent based on a cooldown period to avoid alert fatigue.

        Args:
            key (str): A unique key for the alert type.

        Returns:
            bool: True if an alert should be sent, False otherwise.
        """
        now = time.time()
        last = self.last_alerts.get(key, 0)
        if now - last > self.alert_cooldown:
            self.last_alerts[key] = now
            return True
        return False

    def post_restart_check(self):
        """
        Performs a check after a restart attempt to ensure the service
        is listening on its port.
        """
        time.sleep(5)
        if not self.is_mysql_listening():
            self.log(f"[WATCHDOG][CRIT] MySQL restarted but port {self.mysql_port} is still not listening.")
            self.send_simple_alert(f"🚨 MySQL restarted but never began listening on port {self.mysql_port}.")

    def send_simple_alert(self, message):
        """
        Sends a formatted, human-readable alert to agents with the designated alert role.

        Args:
            message (str): The core alert message to send.
        """
        if not self.alert_role: return
        alert_nodes = self.get_nodes_by_role(self.alert_role)
        if not alert_nodes: return

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_send_alert_msg"})
        try: server_ip = requests.get("https://api.ipify.org").text.strip()
        except Exception: server_ip = "Unknown"
        pk2 = self.get_delivery_packet("notify.alert.general")
        pk2.set_data({
            "server_ip": server_ip, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "universal_id": self.command_line_args.get("universal_id"), "level": "critical",
            "msg": message, "formatted_msg": f"📦 MySQL Watchdog\n{message}",
            "cause": "MySQL Sentinel Alert", "origin": self.command_line_args.get("universal_id")
        })
        pk1.set_packet(pk2, "content")
        for node in alert_nodes: self.pass_packet(pk1, node["universal_id"])

    def send_data_report(self, status, severity, details="", metrics=None):
        """
        Sends a structured data packet with detailed status and diagnostic information
        to agents with the designated reporting role.

        Args:
            status (str): The current status (e.g., "DOWN", "RECOVERED").
            severity (str): The severity level (e.g., "CRITICAL", "INFO").
            details (str, optional): A human-readable description of the event.
            metrics (dict, optional): A dictionary of diagnostic information.
        """
        if not self.report_role: return
        report_nodes = self.get_nodes_by_role(self.report_role)
        if not report_nodes: return

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_ingest_status_report"})
        pk2 = self.get_delivery_packet("standard.status.event.packet")
        pk2.set_data({
            "source_agent": self.command_line_args.get("universal_id"),
            "service_name": "mysql", "status": status, "details": details,
            "severity": severity, "metrics": metrics if metrics is not None else {}
        })
        pk1.set_packet(pk2, "content")
        for node in report_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def collect_mysql_diagnostics(self):
        """
        Gathers MySQL-specific diagnostics, such as systemd status and recent log entries,
        at the moment of failure.

        Returns:
            dict: A dictionary containing diagnostic information.
        """
        info = {}
        # Get systemd status summary
        try:
            info['systemd_status'] = subprocess.check_output(
                ["systemctl", "status", self.service_name], text=True, stderr=subprocess.STDOUT
            ).strip()
        except Exception as e:
            info['systemd_status'] = f"Error: {e}"
        # Error log tail from common locations
        for log_path in ["/var/log/mysql/error.log", "/var/log/mariadb/mariadb.log"]:
            if os.path.exists(log_path):
                try: info['error_log'] = subprocess.check_output(["tail", "-n", "20", log_path], text=True)
                except Exception as e: info['error_log'] = f"Error: {e}"
                break
        return info

if __name__ == "__main__":
    agent = Agent()
    agent.boot()