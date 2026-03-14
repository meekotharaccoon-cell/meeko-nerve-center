#Authored by Daniel F MacDonald and ChatGPT aka The Generals
#Gemini, docstring-ing and added code enhancements.

import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import subprocess
import time
import requests
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from datetime import datetime
from matrixswarm.core.mixin.agent_summary_mixin import AgentSummaryMixin
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent, AgentSummaryMixin):
    def __init__(self):
        super().__init__()
        self.name = "ApacheSentinel"
        cfg = self.tree_node.get("config", {})
        self.interval = cfg.get("check_interval_sec", 10)
        self.service_name = cfg.get("service_name", "httpd")  # or "httpd" on RHEL
        self.ports = cfg.get("ports", [80, 443])
        # New configuration to read both roles
        self.alert_role = cfg.get("alert_to_role", None) #Optional
        self.report_role = cfg.get("report_to_role", None)  # Optional
        self.restart_limit = cfg.get("restart_limit", 3)
        self.mod_status_url = cfg.get("mod_status_url", None)
        self.failed_restarts = 0
        self.disabled = False
        self.alerts = {}
        self.always_alert = bool(cfg.get("always_alert", 1))
        self.alert_cooldown = cfg.get("alert_cooldown", 300)
        self.last_status = None
        self.stats = {
            "date": self.today(),
            "uptime_sec": 0,
            "downtime_sec": 0,
            "restarts": 0,
            "last_state": None,
            "last_change": time.time()
        }
        # test writing summary
        #self.stats["date"] = "1900-01-01"

    def today(self):
        return datetime.now().strftime("%Y-%m-%d")

    def is_apache_running(self):
        try:
            result = subprocess.run(["systemctl", "is-active", "--quiet", self.service_name], check=False)
            return result.returncode == 0
        except Exception as e:
            self.log(f"[WATCHDOG][ERROR] systemctl failed: {e}")
            return False

    def are_ports_open(self):
        try:
            out = subprocess.check_output(["ss", "-ltn"])
            for port in self.ports:
                if f":{port}".encode() not in out:
                    return False
            return True
        except Exception:
            return False

    def restart_apache(self):
        if self.disabled:
            self.log("[WATCHDOG] Watchdog disabled. Restart skipped.")
            return
        try:
            subprocess.run(["systemctl", "restart", self.service_name], check=True)
            self.log("[WATCHDOG] ✅ Apache successfully restarted.")
            self.failed_restarts = 0
            self.stats["restarts"] += 1
        except Exception as e:
            self.failed_restarts += 1
            self.log(f"[WATCHDOG][FAIL] Restart failed: {e}")
            if self.failed_restarts >= self.restart_limit:
                self.disabled = True
                # Send a simple alert if configured
                if self.alert_role:
                    self.send_simple_alert("💀 Apache Watchdog disabled after repeated restart failures.")

                # Send a detailed data report if configured
                if self.report_role:
                    self.send_data_report("DISABLED", "INFO", "Watchdog has been disabled due to max restart failures.")

    def update_stats(self, running):
        now = time.time()
        elapsed = now - self.stats["last_change"]
        if self.stats["last_state"] is not None:
            if self.stats["last_state"]:
                self.stats["uptime_sec"] += elapsed
            else:
                self.stats["downtime_sec"] += elapsed
        self.stats["last_state"] = running
        self.stats["last_change"] = now

    def should_alert(self, key):
        if self.always_alert:
            return True
        now = time.time()
        last = self.alerts.get(key, 0)
        if now - last > self.alert_cooldown:
            self.alerts[key] = now
            return True
        return False

    def send_simple_alert(self, message=None):
        if not message:
            message = "🚨 APACHE REFLEX TERMINATION\n\nReflex loop failed (exit_code = -1)"

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
            "universal_id": self.command_line_args.get("universal_id", "unknown"),
            "level": "critical",
            "msg": message,
            "formatted_msg": f"📣 Apache Watchdog\n{message}",
            "cause": "Apache Sentinel Alert",
            "origin": self.command_line_args.get("universal_id", "unknown")
        })

        pk1.set_packet(pk2,"content")

        alert_nodes = self.get_nodes_by_role("hive.alert.send_alert_msg")
        if not alert_nodes:
            self.log("[WATCHDOG][ALERT] No alert-compatible agents found.")
            return

        for node in alert_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def send_data_report(self, status, severity, details="", metrics=None):
        """Sends a structured data packet for analysis, now with optional metrics."""
        if not self.report_role:
            return

        report_nodes = self.get_nodes_by_role(self.report_role)
        if not report_nodes:
            return

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_ingest_status_report"})

        pk2 = self.get_delivery_packet("standard.status.event.packet")

        # Include the diagnostic metrics in the packet's data payload.
        pk2.set_data({
            "source_agent": self.command_line_args.get("universal_id"),
            "service_name": "apache",
            "status": status,
            "details": details,
            "severity": severity,
            "metrics": metrics if metrics is not None else {}
        })

        pk1.set_packet(pk2, "content")

        for node in report_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def collect_apache_diagnostics(self):
        info = {}
        # Child process count
        try:
            ps = subprocess.check_output("ps -C apache2 -o pid=", shell=True).decode().strip().splitlines()
            info['child_count'] = len(ps)
        except Exception as e:
            info['child_count'] = f"Error: {e}"

        # Only check for mod_status if the URL is defined in the config.
        if self.mod_status_url:
            try:
                import requests
                r = requests.get(self.mod_status_url, timeout=2)
                r.raise_for_status()  # Raise an exception for bad status codes
                info['mod_status'] = r.text
            except Exception as e:
                info['mod_status'] = f"Error fetching mod_status: {e}"

        # Error log tail
        for log_path in ["/var/log/apache2/error.log", "/var/log/httpd/error_log"]:
            if os.path.exists(log_path):
                try:
                    out = subprocess.check_output(["tail", "-n", "20", log_path], text=True)
                    info['error_log'] = out
                except Exception as e:
                    info['error_log'] = f"Error: {e}"
                break

        return info

    def worker(self, config: dict = None, identity: IdentityObject = None):
        # This mixin method will reset stats daily, making the check below essential.
        self.maybe_roll_day("apache")

        is_healthy = self.is_apache_running() and self.are_ports_open()

        # --- Corrected Logic ---

        # On the first run of the day, last_state is None. Establish a baseline.
        if self.stats["last_state"] is None:
            self.log("[WATCHDOG] First run of the day. Establishing baseline status...")
            self.stats["last_state"] = is_healthy
            self.stats["last_change"] = time.time()
            # We return here to avoid sending any alerts on the first check.
            interruptible_sleep(self, self.interval)
            return

        last_state_was_healthy = self.stats["last_state"]

        # Only take action if the service state has actually changed.
        if is_healthy != last_state_was_healthy:
            self.update_stats(is_healthy)

            # Case 1: Service just recovered (it was down, now it's up)
            if is_healthy:
                self.log("[WATCHDOG] ✅ Service has recovered.")
                if self.alert_role:
                    self.send_simple_alert("✅ Apache has recovered and is now online.")
                if self.report_role:
                    self.send_data_report("RECOVERED", "INFO", "Service is back online and ports are open.")

            # Case 2: Service just went down (it was up, now it's down)
            else:
                self.log("[WATCHDOG] ❌ Apache is NOT healthy.")

                # --- MODIFICATION START ---
                # Collect diagnostics at the moment of failure.
                diagnostics = self.collect_apache_diagnostics()

                if self.alert_role and self.should_alert("apache-down"):
                    self.send_simple_alert("❌ Apache is DOWN or not binding required ports. Attempting restart...")

                if self.report_role:
                    self.send_data_report(
                        status="DOWN",
                        severity="CRITICAL",
                        details="Service is not running or ports are not binding.",
                        metrics=diagnostics
                    )

                self.restart_apache()

        # Case 3: Service state is unchanged
        else:
            self.log(f"[WATCHDOG] {'✅' if is_healthy else '❌'} Apache status is stable.")

        interruptible_sleep(self, self.interval)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()