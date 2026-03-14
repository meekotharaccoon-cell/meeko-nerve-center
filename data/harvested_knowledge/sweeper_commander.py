# 🧹 SweepCommanderAgent — Autonomous Execution Unit
# Description: Sends prompts to OracleAgent, receives .cmd replies, and executes validated actions

import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import os
import json
import uuid

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        self.oracle_payload = os.path.join(self.path_resolution["comm_path"], "oracle-1", "payload")
        self.incoming_path = os.path.join(self.path_resolution["comm_path_resolved"], "incoming")
        os.makedirs(self.oracle_payload, exist_ok=True)
        os.makedirs(self.incoming_path, exist_ok=True)

    def worker_pre(self):
        self.log("[SWEEP] Agent activated. Awaiting cleanup directives.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.check_incoming_once()
        interruptible_sleep(self, 3)

    def worker_post(self):
        self.log("[SWEEP] Shutting down. No further directives expected.")

    def post_boot(self):
        self.log("[SWEEP] Boot complete. Dispatching prompt to Oracle.")
        self.send_prompt_to_oracle()

    def send_prompt_to_oracle(self):
        prompt_data = {
            "system_state": {
                "dead_pods": self.count_dead_pods(),
                "active_uuid": self.command_line_args["install_name"]
            },
            "reply_to": self.command_line_args["universal_id"]
        }
        fname = f"sweep_{uuid.uuid4().hex}.prompt"
        with open(os.path.join(self.oracle_payload, fname), "w", encoding="utf-8") as f:
            f.write(json.dumps(prompt_data, indent=2))
        self.log(f"[SWEEP] Prompt sent to Oracle: {fname}")

    def count_dead_pods(self):
        pod_root = self.path_resolution.get("pod_path", "/pod")
        return len([d for d in os.listdir(pod_root) if d.startswith("dead")])

    def check_incoming_once(self):
        for f in os.listdir(self.incoming_path):
            if not f.endswith(".cmd"):
                continue
            try:
                with open(os.path.join(self.incoming_path, f), "r", encoding="utf-8") as cmd_file:
                    cmd = json.load(cmd_file)
                    self.handle_command(cmd)
                os.remove(os.path.join(self.incoming_path, f))
            except Exception as e:
                self.log(f"[SWEEP][ERROR] Failed to parse {f}: {e}")

    def handle_command(self, cmd):
        source = cmd.get("source")
        if source != "oracle":
            self.log(f"[SWEEP] Ignoring command from unknown source: {source}")
            return

        action = cmd.get("action")
        target = cmd.get("target")

        if action == "purge_folder" and target:
            try:
                if os.path.exists(target):
                    for file in os.listdir(target):
                        fpath = os.path.join(target, file)
                        if os.path.isfile(fpath):
                            os.remove(fpath)
                    self.log(f"[SWEEP] Purged folder: {target}")
            except Exception as e:
                self.log(f"[SWEEP][ERROR] Failed to purge folder {target}: {e}")
        else:
            self.log(f"[SWEEP] Unknown or missing action: {action}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
