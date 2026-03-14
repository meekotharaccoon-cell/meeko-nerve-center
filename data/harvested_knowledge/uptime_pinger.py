import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import json
import time
import hashlib
import requests
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        config = self.tree_node.get("config", {})
        self.targets = config.get("targets", ["https://example.com"])
        self.interval = config.get("interval_sec", 30)
        self.alert_to = config.get("alert_to", "mailman-1")
        self.payload_out = os.path.join(self.path_resolution["comm_path"], self.alert_to, "payload")
        os.makedirs(self.payload_out, exist_ok=True)

    def worker_pre(self):
        self.log(f"[PINGER] Uptime monitor engaged. Interval: {self.interval}s")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.ping_once()
        interruptible_sleep(self, self.interval)

    def worker_post(self):
        self.log("[PINGER] Pinger shutting down. Final signal sent.")

    def ping_once(self):
        for url in self.targets:
            try:
                start = time.time()
                r = requests.get(url, timeout=5)
                elapsed = time.time() - start
                self.send_log(url, r.status_code, elapsed, r.ok)
            except Exception as e:
                self.send_log(url, "ERR", 0, False)

    def send_log(self, target, status_code, response_time, success):
        msg = f"{'UP' if success else 'DOWN'}: {target} [{status_code}] in {response_time:.2f}s" if success else f"DOWN: {target} [{status_code}]"
        payload = {
            "uuid": self.command_line_args["universal_id"],
            "timestamp": time.time(),
            "severity": "info" if success else "error",
            "msg": msg
        }
        hashval = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        filename = f"{int(time.time())}_{hashval}.json"
        with open(os.path.join(self.payload_out, filename), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
