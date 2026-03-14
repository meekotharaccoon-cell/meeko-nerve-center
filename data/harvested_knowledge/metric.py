import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import os
import time
import json
import hashlib
import psutil
import shutil

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        config = self.tree_node.get("config", {}) if 'tree_node' in globals() else {}

        self.report_to = config.get("report_to", "mailman-1")
        self.ask_oracle = config.get("oracle", "oracle-1")
        self.interval = config.get("interval_sec", 10)

        self.outbox = os.path.join(self.path_resolution["comm_path"], self.report_to, "payload")
        self.oracle_payload = os.path.join(self.path_resolution["comm_path"], self.ask_oracle, "payload")

        os.makedirs(self.outbox, exist_ok=True)
        os.makedirs(self.oracle_payload, exist_ok=True)

        self.history = []

    def worker_pre(self):
        self.log("[METRICS] Agent initialized. Beginning observation.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.collect_and_report()
        interruptible_sleep(self, self.interval)

    def worker_post(self):
        self.log("[METRICS] Agent shutting down. Final metrics recorded.")

    def collect_and_report(self):
        data = self.get_metrics()
        self.log_metrics(data)
        self.history.append(data)

        if len(self.history) >= 5:
            summary = {
                "cpu_avg": round(sum(d["cpu"] for d in self.history[-5:]) / 5, 2),
                "ram_avg": round(sum(d["ram_used_percent"] for d in self.history[-5:]) / 5, 2),
                "disk_min": round(min(d["disk_free_gb"] for d in self.history[-5:]), 2),
                "uptime": self.history[-1]["uptime_sec"]
            }
            self.query_oracle(summary)

    def get_metrics(self):
        cpu = os.getloadavg()[0]
        ram = psutil.virtual_memory().percent
        disk = shutil.disk_usage("/").free / (1024 ** 3)
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            uptime = float(f.readline().split()[0])
        return {
            "cpu": round(cpu, 2),
            "ram_used_percent": round(ram, 2),
            "disk_free_gb": round(disk, 2),
            "uptime_sec": int(uptime)
        }

    def log_metrics(self, data):
        payload = {
            "uuid": self.command_line_args["universal_id"],
            "timestamp": time.time(),
            "severity": "info",
            "msg": f"CPU: {data['cpu']}, RAM: {data['ram_used_percent']}%, Disk Free: {data['disk_free_gb']} GB, Uptime: {data['uptime_sec']} sec"
        }
        hashval = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        fname = f"{int(time.time())}_{hashval}.json"
        with open(os.path.join(self.outbox, fname), "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def query_oracle(self, summary):
        query = {
            "source": self.command_line_args["universal_id"],
            "query_type": "trend_analysis",
            "timestamp": time.time(),
            "payload": summary
        }
        fname = f"metrics_trend_query_{int(time.time())}.json"
        with open(os.path.join(self.oracle_payload, fname), "w", encoding="utf-8") as f:
            json.dump(query, f)
        self.log("[METRICS] Oracle query dispatched.")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
