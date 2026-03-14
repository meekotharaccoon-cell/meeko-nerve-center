import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import json
import time
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        self.payload_dir = os.path.join(self.path_resolution["comm_path_resolved"], "payload")
        os.makedirs(self.payload_dir, exist_ok=True)
        self.spawn_target = os.path.join(self.path_resolution["comm_path"], "matrix", "payload")
        os.makedirs(self.spawn_target, exist_ok=True)

    def worker_pre(self):
        msg = "[REACTOR] Initializing reflex protocol. Listening for Oracle decisions."
        print(msg)
        self.broadcast(msg)

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.check_oracle_triggers_once()
        interruptible_sleep(self, 2)

    def worker_post(self):
        self.log("[REACTOR] Shutting down. Reflexes deactivated.")

    def check_oracle_triggers_once(self):
        try:
            for fname in os.listdir(self.payload_dir):
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(self.payload_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    msg = json.load(f)

                action = msg.get("action_taken")
                classification = msg.get("classification")

                if classification == "threat" and action == "interrupted":
                    self.deploy_defense_agent("mirror-2", "filesystem_mirror")

                os.remove(fpath)
        except Exception as e:
            self.log(f"[REACTOR][ERROR] {e}")

    def deploy_defense_agent(self, universal_id, agent_name):
        spawn_payload = {
            "command": "spawn_agent",
            "payload": {
                "universal_id": universal_id,
                "agent_name": agent_name,
                "directives": {
                    "watch_path": "/etc",
                    "mode": "snapshot"
                }
            }
        }
        fname = f"reactor_spawn_{int(time.time())}.json"
        path = os.path.join(self.spawn_target, fname)
        #with open(path, "w") as f:
        #    json.dump(spawn_payload, f, indent=2)
        #self.log(f"[REACTOR] Dispatched spawn request for {agent_name} as {universal_id}.")

    def broadcast(self, message):
        try:
            mailman_dir = os.path.join(self.path_resolution["comm_path"], "mailman-1", "payload")
            os.makedirs(mailman_dir, exist_ok=True)
            payload = {
                "uuid": self.command_line_args.get("universal_id", "reactor-1"),
                "timestamp": time.time(),
                "severity": "info",
                "msg": message
            }
            fname = f"reactor_boot_{int(time.time())}.json"
            #with open(os.path.join(mailman_dir, fname), "w") as f:
            #    json.dump(payload, f, indent=2)
        except Exception as e:
            self.log(f"[REACTOR][ERROR] {e}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()

