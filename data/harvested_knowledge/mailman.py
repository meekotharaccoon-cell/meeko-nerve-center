# ╔════════════════════════════════════════════════════════╗
# ║                📬 MAILMAN AGENT                        ║
# ║  System Logger · Tally Tracker · Message Forwarder     ║
# ║  Spawned from Matrix | No excuses. Just receipts.      ║
# ╚════════════════════════════════════════════════════════╝
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import json
import time
import hashlib

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        base = self.path_resolution["comm_path_resolved"]
        self.payload_dir = os.path.join(base, "payload")
        self.mail_dir = os.path.join(base, "mail")
        self.tally_dir = os.path.join(base, "tally")
        self.incoming_dir = os.path.join(base, "incoming")
        for d in [self.payload_dir, self.mail_dir, self.tally_dir, self.incoming_dir]:
            os.makedirs(d, exist_ok=True)
        self.hash_cache = set()

    def worker_pre(self):
        self.log("[MAILMAN] Mailman v2.1 booted. Awaiting payloads.")

    def worker_post(self):
        self.log("[MAILMAN] Agent shutting down.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.process_payload_once()
        interruptible_sleep(self, 10)

    def process_payload_once(self):
        try:
            files = sorted(os.listdir(self.payload_dir))
            for file in files:
                if not file.endswith(".json"):
                    continue
                fullpath = os.path.join(self.payload_dir, file)
                try:
                    content = open(fullpath).read()
                    hashval = self.hash_msg(content)
                    if hashval in self.hash_cache:
                        os.remove(fullpath)
                        continue
                    self.hash_cache.add(hashval)
                    self.write_mail_file(hashval, content)
                    self.write_tally_file(hashval, content)
                    self.forward_to_incoming(hashval, content)
                    self.log(f"[MAILMAN] Logged: {hashval} -> {file}")
                    os.remove(fullpath)
                except Exception as e:
                    self.log(f"[MAILMAN][ERROR] Failed to process {file}: {e}")
        except Exception as loop_error:
            self.log(f"[MAILMAN][LOOP-ERROR] {loop_error}")

    def hash_msg(self, content):
        return hashlib.sha256(content.encode()).hexdigest()

    def write_mail_file(self, hashval, content):
        path = os.path.join(self.mail_dir, f"{hashval}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def write_tally_file(self, hashval, content):
        try:
            data = json.loads(content)
            entry = {
                "uuid": data.get("uuid", "unknown"),
                "timestamp": data.get("timestamp", time.time()),
                "severity": data.get("severity", "info")
            }
            path = os.path.join(self.tally_dir, f"{hashval}.msg")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f)
        except Exception as e:
            self.log(f"[MAILMAN][TALLY-ERROR] {e}")

    def forward_to_incoming(self, hashval, content):
        try:
            path = os.path.join(self.incoming_dir, f"{int(time.time())}_{hashval}.msg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self.log(f"[MAILMAN][FORWARD-ERROR] {e}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
