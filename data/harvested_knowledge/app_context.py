import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import json
import time
from matrixswarm.core.boot_agent import BootAgent

class Agent(BootAgent):
    def __init__(self, ):
        super().__init__()

        self.codex_dir = os.path.join(self.path_resolution["comm_path"], "matrix", "codex", "apps")

    def worker_pre(self):
        self.log("[CONTEXT] AppContextAgent online. Awaiting deployment commands.")

    def worker(self, config:dict = None):
        pass  # passive agent, listens only

    def process_command(self, command):
        try:
            if command.get("command") == "spawn_app":
                app_name = command["payload"]["app"]
                path = os.path.join(self.codex_dir, f"{app_name}.json")
                if not os.path.exists(path):
                    self.log(f"[CONTEXT] Codex app file not found: {app_name}")
                    return

                with open(path, "r", encoding="utf-8") as f:
                    app_data = json.load(f)

                self.deploy_app(app_data)
        except Exception as e:
            self.log(f"[CONTEXT][ERROR] {e}")

    def deploy_app(self, app_data):
        app_name = app_data.get("app")
        for i, comp in enumerate(app_data.get("components", []), start=1):
            for j in range(comp["count"]):
                agent_type = comp["role"]
                universal_id = f"{agent_type}-{app_name}-{i}-{j}"
                spawn_cmd = {
                    "command": "spawn_agent",
                    "payload": {
                        "universal_id": universal_id,
                        "agent_name": agent_type,
                        "directives": {
                            "app": app_name
                        }
                    }
                }
                path = os.path.join(self.path_resolution["comm_path"], "matrix", "payload")
                fname = f"spawn_{universal_id}_{int(time.time())}.json"
                with open(os.path.join(path, fname), "w", encoding="utf-8") as f:
                    json.dump(spawn_cmd, f, indent=2)
                self.log(f"[CONTEXT] Spawned: {universal_id}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()