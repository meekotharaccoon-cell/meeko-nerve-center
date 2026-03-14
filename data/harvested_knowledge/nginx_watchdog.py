# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import requests
import subprocess
import time
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from datetime import datetime
from matrixswarm.core.mixin.agent_summary_mixin import AgentSummaryMixin
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent, AgentSummaryMixin):
    """
    A watchdog agent that monitors an Nginx web server. It checks if the service is active
    and listening on critical ports (e.g., 80, 443), attempts to restart it upon failure,
    and sends alerts and reports about its operational status.
    """
    def __init__(self):
        """Initializes the NginxWatchdog agent, setting up configuration and statistics."""
        super().__init__()
        self.name = "NginxWatchdog"
        cfg = self.tree_node.get("config", {})
        self.interval = cfg.get("check_interval_sec", 10)
        self.service_name = cfg.get("service_name", "nginx")
        self.ports = cfg.get("ports", [80, 443])
        self.restart_limit = cfg.get("restart_limit", 3)
        self.failed_restart_count = 0
        self.disabled = False
        self.alerts = {}
        self.alert_cooldown = cfg.get("alert_cooldown", 300)
        self.alert_role = cfg.get("alert_to_role", None)
        self.report_role = cfg.get("report_to_role", None)
        self.stats = {
            "date": self.today(),
            "uptime_sec": 0,
            "downtime_sec": 0,
            "restarts": 0,
            "last_state": None,
            "last_status_change": time.time(),
        }
        self.last_alerts = {}

    def today(self):
        """
        Returns the current date as a string in YYYY-MM-DD format.

        Returns:
            str: The current date.
        """
        return datetime.now().strftime("%Y-%m-%d")

    def is_nginx_running(self):
        """
        Checks if the Nginx service is active using systemd.

        Returns:
            bool: True if the service is active, False otherwise.
        """
        try:
            result = subprocess.run(["systemctl", "is-active", "--quiet", self.service_name], check=False)
            return result.returncode == 0
        except Exception as e:
            self.log(f"[SENTINEL][ERROR] systemctl failed: {e}")
            return False

    def are_ports_open(self):
        """
        Checks if the configured Nginx ports are open and listening.

        Returns:
            bool: True if all specified ports are listening, False otherwise.
        """
        try:
            out = subprocess.check_output(["ss", "-ltn"])
            for port in self.ports:
                if f":{port}".encode() not in out:
                    return False
            return True
        except Exception:
            return False

    def restart_nginx(self):
        """
        Attempts to restart the Nginx service. If restart attempts fail repeatedly,
        it disables itself to prevent a restart loop.
        """
        if self.disabled:
            self.log("[SENTINEL][DISABLED] Agent is disabled after repeated restart failures.")
            return
        try:
            subprocess.run(["systemctl", "restart", self.service_name], check=True)
            self.log("[SENTINEL] ✅ Nginx successfully restarted.")
            self.failed_restart_count = 0
            self.stats["restarts"] += 1
            self.post_restart_check()
        except Exception as e:
            self.failed_restart_count += 1
            self.log(f"[SENTINEL][FAIL] Restart failed: {e}")
            if self.failed_restart_count >= self.restart_limit:
                self.disabled = True
                self.send_simple_alert("💀 Nginx watchdog disabled after repeated restart failures.")

    def update_status_metrics(self, is_running):
        """
        Updates the uptime and downtime statistics based on the current service status.

        Args:
            is_running (bool): The current running state of the service.
        """
        now = time.time()
        last = self.stats.get("last_state")
        elapsed = now - self.stats.get("last_status_change", now)
        if last is not None:
            if last:
                self.stats["uptime_sec"] += elapsed
            else:
                self.stats["downtime_sec"] += elapsed
        self.stats["last_state"] = is_running
        self.stats["last_status_change"] = now

    def should_alert(self, key):
        """
        Determines if an alert should be sent based on a cooldown to prevent alert fatigue.

        Args:
            key (str): A unique key for the type of alert.

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
        is listening on its designated ports.
        """
        time.sleep(5)
        if not self.are_ports_open():
            self.log(f"[SENTINEL][CRIT] Nginx restarted but ports {self.ports} are still not listening.")
            self.send_simple_alert(f"🚨 Nginx restarted but ports {self.ports} are still not open.")

    def send_simple_alert(self, message):
        """
        Sends a formatted, human-readable alert to agents with the designated alert role.

        Args:
            message (str): The core message of the alert.
        """
        if not self.alert_role:
            return
        alert_nodes = self.get_nodes_by_role(self.alert_role)
        if not alert_nodes:
            self.log("[SENTINEL][ALERT] No alert-compatible agents found.")
            return

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_send_alert_msg"})
        try:
            server_ip = requests.get("https://api.ipify.org").text.strip()
        except Exception:
            server_ip = "Unknown"
        pk2 = self.get_delivery_packet("notify.alert.general")
        pk2.set_data({
            "server_ip": server_ip,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "universal_id": self.command_line_args.get("universal_id"),
            "level": "critical",
            "msg": message,
            "formatted_msg": f"📣 Swarm Message\n{message}",
            "cause": "Nginx Sentinel Alert",
            "origin": self.command_line_args.get("universal_id")
        })
        pk1.set_packet(pk2, "content")
        for node in alert_nodes:
            self.pass_packet(pk1, node["universal_id"])

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
        if not self.report_role:
            return
        report_nodes = self.get_nodes_by_role(self.report_role)
        if not report_nodes:
            return

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_ingest_status_report"})
        pk2 = self.get_delivery_packet("standard.status.event.packet")
        pk2.set_data({
            "source_agent": self.command_line_args.get("universal_id"),
            "service_name": "nginx",
            "status": status,
            "details": details,
            "severity": severity,
            "metrics": metrics if metrics is not None else {}
        })
        pk1.set_packet(pk2, "content")
        for node in report_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def worker(self, config:dict = None, identity:IdentityObject = None):
        """
        The main worker loop. It performs the health check, handles state changes,
        triggers restarts, and sends reports as needed.

        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
            identity (IdentityObject, optional): Identity object for the agent. Defaults to None.
        """
        self.maybe_roll_day("nginx")
        is_healthy = self.is_nginx_running() and self.are_ports_open()
        last_state = self.stats.get("last_state")

        # First run: establish baseline
        if last_state is None:
            self.log(f"[SENTINEL] Establishing baseline status for {self.service_name}...")
            self.stats["last_state"] = is_healthy
            self.stats["last_status_change"] = time.time()
            interruptible_sleep(self, self.interval)
            return

        # If state changed (UP/DOWN)
        if is_healthy != last_state:
            self.update_status_metrics(is_healthy)
            if is_healthy:
                self.log(f"[SENTINEL] ✅ {self.service_name} has recovered.")
                self.send_simple_alert(f"✅ {self.service_name.capitalize()} has recovered and is now online.")
                self.send_data_report("RECOVERED", "INFO", "Service is back online and ports are open.")
            else:
                self.log(f"[SENTINEL] ❌ {self.service_name} is NOT healthy.")
                diagnostics = self.collect_nginx_diagnostics()
                if self.should_alert("nginx-down"):
                    self.send_simple_alert(f"❌ {self.service_name.capitalize()} is DOWN or not binding required ports.")
                self.send_data_report(
                    status="DOWN", severity="CRITICAL",
                    details=f"Service {self.service_name} is not running or required ports are not open.",
                    metrics=diagnostics
                )
                self.restart_nginx()
            self.stats["last_state"] = is_healthy
        else:
            # State stable, accumulate uptime/downtime
            self.update_status_metrics(is_healthy)
            if hasattr(self, "debug") and getattr(self.debug, "is_enabled", lambda: False)():
                self.log(f"[SENTINEL] {'✅' if is_healthy else '❌'} {self.service_name} status is stable.")

        interruptible_sleep(self, self.interval)

    def collect_nginx_diagnostics(self):
        """
        Gathers Nginx-specific diagnostics at the moment of failure, including
        systemd status and recent error log entries.

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
        for log_path in ["/var/log/nginx/error.log", "/var/log/nginx/error.log.1"]:
            if os.path.exists(log_path):
                try:
                    info['error_log'] = subprocess.check_output(["tail", "-n", "20", log_path], text=True)
                except Exception as e:
                    info['error_log'] = f"Error: {e}"
                break
        return info

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
