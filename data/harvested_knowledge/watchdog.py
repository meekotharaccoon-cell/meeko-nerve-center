#Authored by Daniel F MacDonald
# ╔════════════════════════════════════════════════════════╗
# ║                   🧠 WATCHDOG AGENT 🧠                ║
# ║   Central Cortex · Tree Dispatcher · Prime Director    ║
# ║     Forged in the core of Hive Zero | v3.0 Directive   ║
# ║   ║
# ╚════════════════════════════════════════════════════════╝
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import time
import requests
import json
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.boot_agent import BootAgent

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        self.failure_count = 0

    def worker_pre(self):
        config = self.tree_node.get("config", {}) if 'tree_node' in globals() else {}
        self.ping_url = config.get("ping_url", "https://matrixswarm.com")
        self.check_interval = config.get("check_interval_sec", 60)
        self.timeout = config.get("timeout_sec", 5)
        self.max_failures = config.get("max_failures", 3)
        self.alert_action = config.get("alert_action", "notify_matrix")

        self.log(f"[WATCHDOG][CONFIG] Loaded: ping={self.ping_url}, interval={self.check_interval}s, timeout={self.timeout}s, max_failures={self.max_failures}, action={self.alert_action}")
        self.log("[WATCHDOG] WatchdogAgent initialized and watching.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.check_ping_once()
        interruptible_sleep(self, self.check_interval)

    def worker_post(self):
        self.log("[WATCHDOG] WatchdogAgent is shutting down. Signal loop terminated.")

    def check_ping_once(self):
        try:
            response = requests.get(self.ping_url, timeout=self.timeout)
            if response.status_code != 200:
                raise Exception(f"Bad status code: {response.status_code}")
            self.failure_count = 0
            self.log(f"[WATCHDOG][OK] {self.ping_url} is UP [200]")
        except Exception as e:
            self.failure_count += 1
            self.log(f"[WATCHDOG][FAIL] ({self.failure_count}/{self.max_failures}): {e}")
            if self.failure_count >= self.max_failures:
                self.handle_alert(str(e))
                self.failure_count = 0

    def handle_alert(self, error_message):
        alert = {
            "cmd": "alert",
            "source": "watchdog",
            "issue": "matrixswarm.com unreachable",
            "details": {
                "url": self.ping_url,
                "error": error_message,
                "universal_id": self.command_line_args["universal_id"],
                "uuid": self.command_line_args["install_name"],
                "timestamp": time.time()
            }
        }
        if self.alert_action == "notify_matrix":
            print(alert)
        elif self.alert_action == "log_only":
            self.log(f"[WATCHDOG][ALERT] (log_only): {json.dumps(alert)}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
