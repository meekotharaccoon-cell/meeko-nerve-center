import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import os
import time
import json

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        config = self.tree_node.get("config", {})

        self.watch_path = config.get("watch_path", "/etc")
        self.mode = config.get("mode", "once")  # or "cycle"
        self.self_destruct = config.get("self_destruct", False)

        self.report_to = config.get("report_to", "mailman-1")
        self.out_dir = os.path.join(self.path_resolution["comm_path"], self.report_to, "payload")
        os.makedirs(self.out_dir, exist_ok=True)
        self.cycle_index = 0

    def worker_pre(self):
        self.log(f"[MIRROR] Mission start. Watching {self.watch_path} [mode: {self.mode}]")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        if self.mode != "cycle" and self.cycle_index > 0:
            interruptible_sleep(self, 10)
            return

        self.cycle_index += 1
        self.scan_and_log()

        if self.self_destruct and self.mode == "once":
            self.log("[MIRROR] Mission complete. Self-destruct initiated.")
            self.running = False

        if self.mode == "cycle":
            interruptible_sleep(self, 10)

    def worker_post(self):
        self.log(f"[MIRROR] Final cycle complete. Agent shutting down after {self.cycle_index} scan(s).")

    def scan_and_log(self):
        snapshot = []

        try:
            for root, dirs, files in os.walk(self.watch_path):
                for fname in files:
                    try:
                        path = os.path.join(root, fname)
                        stat = os.stat(path)
                        snapshot.append({
                            "file": path,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime
                        })
                    except Exception:
                        continue
        except Exception as e:
            self.log(f"[MIRROR][ERROR] Failed to scan {self.watch_path}: {e}")
            return

        payload = {
            "uuid": self.command_line_args["universal_id"],
            "timestamp": time.time(),
            "watch_path": self.watch_path,
            "file_count": len(snapshot),
            "files": snapshot[:50]
        }

        fname = f"mirror_{int(time.time())}.json"
        with open(os.path.join(self.out_dir, fname), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.log(f"[MIRROR] Snapshot complete. {len(snapshot)} files logged.")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()