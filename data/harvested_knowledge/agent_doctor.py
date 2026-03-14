# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import time
import json
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep

class Agent(BootAgent):
    """
    The AgentDoctor is a diagnostic agent that monitors the health and status of all other agents in the swarm.
    It periodically checks for agent beacons to ensure they are alive and responsive, reporting any anomalies.
    """
    def __init__(self):
        """Initializes the AgentDoctor agent, setting its name and the maximum age for a beacon to be considered valid."""
        super().__init__()
        self.name = "AgentDoctor"
        self.max_allowed_beacon_age = 8  # seconds

    def pre_boot(self):
        """Logs a message indicating that the diagnostics module is armed and ready."""
        self.log("[DOCTOR] Swarm-wide diagnostics module armed.")

    def post_boot(self):
        """Logs messages indicating the start of monitoring and registration with the Matrix."""
        self.log("[DOCTOR] Monitoring active threads via intelligent beacon protocol.")
        self.log("[IDENTITY] Registering with Matrix...")
        #self.dispatch_identity_command()

    def is_phantom(self, agent_id):
        """
        Checks if an agent is a 'phantom'—meaning its communication directory exists, but its corresponding
        pod (and boot file) does not.

        Args:
            agent_id (str): The universal ID of the agent to check.

        Returns:
            bool: True if the agent is a phantom, False otherwise.
        """
        pod_root = self.path_resolution["pod_path"]
        for pod_id in os.listdir(pod_root):
            boot_file = os.path.join(pod_root, pod_id, "boot.json")
            try:
                with open(boot_file, encoding="utf-8") as f:
                    boot_data = json.load(f)
                    if boot_data.get("universal_id") == agent_id:
                        return False
            except:
                continue
        return True

    def read_poke_file(self, path):
        """
        Reads a 'poke' file which contains the last seen timestamp of an agent's thread.

        Args:
            path (str): The path to the poke file.

        Returns:
            dict: A dictionary containing the status and last seen time, or an error.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if raw.startswith("{"):
                    return json.loads(raw)
                else:
                    return {"status": "alive", "last_seen": float(raw)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def verify_agent_consciousness(self, agent_id, threads=("heartbeat","worker", "packet_listener")):
        """
        Verifies the status of an agent by checking the beacon files for its various threads.

        Args:
            agent_id (str): The universal ID of the agent to verify.
            threads (tuple, optional): A tuple of thread names to check. Defaults to ("heartbeat", "worker", "packet_listener").

        Returns:
            dict: A dictionary with the status of each checked thread.
        """
        comm_path = os.path.join(self.path_resolution["comm_path"], agent_id)
        beacon_dir = os.path.join(comm_path, "hello.moto")

        now = time.time()
        status_report = {}

        if not os.path.isdir(beacon_dir):
            self.log(f"[DOCTOR] Missing hello.moto folder for {agent_id}")
            for thread in threads:
                status_report[thread] = "❌ no beacon (no hello.moto)"
            return status_report

        for thread in threads:
            poke_file = os.path.join(beacon_dir, f"poke.{thread}")
            if not os.path.exists(poke_file):
                status_report[thread] = "❌ no beacon"
                continue

            beacon = self.read_poke_file(poke_file)
            status = beacon.get("status", "unknown")
            timeout = beacon.get("timeout", self.max_allowed_beacon_age)

            if status == "alive":
                age = round(now - beacon.get("last_seen", 0), 2)
                if age > timeout * 2:
                    status_report[thread] = f"💥 reflex expired ({age}s > {timeout}s)"
                elif age > timeout:
                    status_report[thread] = f"⚠️ stale ({age}s)"
                else:
                    status_report[thread] = f"✅ {age}s"
            elif status == "dead":
                err = beacon.get("error", "no error provided")
                status_report[thread] = f"💀 dead: {err}"
            elif status == "unused":
                status_report[thread] = f"🟦 unused"
            else:
                status_report[thread] = f"❓ unknown status"

        return status_report

    def worker(self, config:dict = None, identity:IdentityObject = None):
        """
        The main worker loop for the AgentDoctor. It periodically scans all agents in the swarm,
        checks their status, and logs a report.

        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
            identity (IdentityObject, optional): Identity object for the agent. Defaults to None.
        """
        self.log("[DOCTOR] Beginning swarm scan...")
        agents = self.get_agents_list()

        for agent_id in agents:
            if agent_id == self.command_line_args.get("universal_id"):
                continue

            if self.is_phantom(agent_id):
                self.log(f"🩺 {agent_id}\n  • 👻 phantom agent — comm exists, no pod detected")
                continue

            status = self.verify_agent_consciousness(agent_id)
            log_lines = [f"🩺 {agent_id}"]
            for thread, stat in status.items():
                log_lines.append(f"  • {thread:<16} {stat}")
            self.log("\n".join(log_lines))

        interruptible_sleep(self, 30)

    def get_agents_list(self):
        """
        Retrieves a list of all agent IDs from the communication directory.

        Returns:
            list: A list of agent universal IDs.
        """
        comm_path = self.path_resolution.get("comm_path", "/matrix/ai/latest/comm")
        agents = []
        for agent_id in os.listdir(comm_path):
            base = os.path.join(comm_path, agent_id)
            if not os.path.isdir(base):
                continue
            if os.path.isdir(os.path.join(base, "incoming")) or os.path.isdir(os.path.join(base, "hello.moto")):
                agents.append(agent_id)
        return agents


if __name__ == "__main__":
    agent = Agent()
    agent.boot()