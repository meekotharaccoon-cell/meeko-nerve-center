
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import time
import json
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject
from matrixswarm.core.class_lib.time_utils.heartbeat_checker import last_heartbeat_delta
from matrixswarm.core.mixin.delegation import DelegationMixin
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep

class Agent(BootAgent, DelegationMixin):

    def __init__(self, path_resolution, command_line_args):
        super().__init__(path_resolution, command_line_args)
        self.orbits = {}
        self.pending_resurrections = {}
        self.label = self.command_line_args.get("universal_id", "UNKNOWN").upper()

    def worker_pre(self):
        self.log("[WATCHDOG-2] Agent initialized. Resurrection monitoring engaged.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.scan_once()
        interruptible_sleep(self, 5)

    def worker_post(self):
        self.log("[WATCHDOG-2] Agent shutdown. Resurrection attempts halted.")

    def scan_once(self):
        self.check_heartbeats()
        self.retry_failed_agents()

    def check_heartbeats(self):
        comm_path = self.path_resolution["comm_path"]
        now = time.time()
        timeout = 20

        for agent_id in os.listdir(comm_path):
            if agent_id in self.pending_resurrections:
                continue

            delta = last_heartbeat_delta(comm_path, agent_id)
            if delta is None:
                continue

            if delta > timeout:
                self.log(f"[{self.label}] {agent_id} missed heartbeat. Starting recovery.")
                self.pending_resurrections[agent_id] = {"attempts": 1, "last_seen": now}
                self.recover_agent(agent_id)
            else:
                self.log(f"[{self.label}] {agent_id} heartbeat OK ({int(delta)}s ago)")

    def retry_failed_agents(self):
        now = time.time()
        for agent_id, info in list(self.pending_resurrections.items()):
            if self.confirm_resurrection(agent_id):
                self.log(f"[WATCHDOG-2] Resurrection confirmed: {agent_id}")
                del self.pending_resurrections[agent_id]
            else:
                if info["attempts"] >= 3:
                    self.log(f"[WATCHDOG-2] {agent_id} failed to resurrect. Marked as fallen.")
                    del self.pending_resurrections[agent_id]
                elif now - info["last_seen"] > 20:
                    info["attempts"] += 1
                    info["last_seen"] = now
                    self.log(f"[WATCHDOG-2] Retrying resurrection: {agent_id} (attempt {info['attempts']})")
                    self.recover_agent(agent_id)

    def confirm_resurrection(self, agent_id):
        hello_path = os.path.join(self.path_resolution["comm_path"], agent_id, "hello.moto")
        if not os.path.isdir(hello_path):
            return False
        try:
            latest = max((os.path.getmtime(os.path.join(hello_path, f)) for f in os.listdir(hello_path)), default=0)
            return (time.time() - latest) < 15
        except:
            return False

    def recover_agent(self, universal_id):
        matrix_comm = os.path.join(self.path_resolution["comm_path"], "matrix", "incoming")
        os.makedirs(matrix_comm, exist_ok=True)
        request = {
            "action": "request_delegation",
            "requester": universal_id
        }
        filename = f"request_delegation_{int(time.time())}.cmd"
        full_path = os.path.join(matrix_comm, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(request, f, indent=2)
        self.log(f"[WATCHDOG-2] Recovery request dispatched for {universal_id} → {filename}")

    def process_command(self, command):
        try:
            action = command.get("action")
            if action == "die":
                self.log("[CMD] Watchdog-2 received die command.")
                self.running = False
            elif action == "update_delegates":
                self.process_update_delegates(command)
            else:
                self.log(f"[CMD] Unknown action: {action}")
        except Exception as e:
            self.log(f"[CMD-ERROR] {e}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()