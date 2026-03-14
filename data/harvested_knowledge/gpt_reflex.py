import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import json
import time
from openai import OpenAI
from string import Template
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject
class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        try:
            config = self.tree_node.get("config", {})
            self.api_key = config.get("api_key", os.getenv("OPENAI_API_KEY"))
            self.model = config.get("model", "gpt-4")
            self.universal_id = self.command_line_args.get("universal_id", "gpt-reflex")
            self.inbox = Template(self.path_resolution["incoming_path_template"]).substitute(universal_id=self.universal_id)
            self.outbox = os.path.join(self.path_resolution["comm_path"], self.universal_id, "outbox")
            self.replies = os.path.join(self.path_resolution["comm_path"], self.universal_id, "replies")
            self.queue = os.path.join(self.path_resolution["comm_path"], self.universal_id, "queue")
            self.matrix_inbox = Template(self.path_resolution["incoming_path_template"]).substitute(universal_id="matrix")
            os.makedirs(self.inbox, exist_ok=True)
            os.makedirs(self.outbox, exist_ok=True)
            os.makedirs(self.replies, exist_ok=True)
            os.makedirs(self.queue, exist_ok=True)
            os.makedirs(self.inbox, exist_ok=True)
            os.makedirs(self.outbox, exist_ok=True)

            if not self.api_key:
                self.log("[GPT][ERROR] No OPENAI_API_KEY found in environment.")
            self.client = OpenAI(api_key=self.api_key)

            self.log(f"[GPT][BOOT] Inbox path: {self.inbox}")
            self.log(f"[GPT][BOOT] Outbox path: {self.outbox}")

        except Exception as e:
            self.log(error=e, block="main-try")



    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.log("[GPT][DEBUG] Entered worker() loop.")
        processed = 0
        try:
            if not os.path.exists(self.inbox):
                self.log(f"[GPT][ERROR] Inbox does not exist: {self.inbox}")
                return

            files = [f for f in os.listdir(self.inbox) if f.endswith(".msg")]
            self.log(f"[GPT][DEBUG] Found {len(files)} files in inbox.")

            for fname in files:
                full_path = os.path.join(self.inbox, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        payload = json.load(f)

                    prompt = payload.get("prompt", "")
                    mode = payload.get("mode", "markdown")
                    target = payload.get("target")

                    if not prompt:
                        self.log(f"[GPT][SKIP] No prompt in {fname}")
                        os.remove(full_path)
                        continue

                    self.log(f"[GPT] → Prompt received: {prompt[:50]}...")
                    response = self.ask_gpt(prompt)

                    intent = {}
                    base_id = fname.replace(".msg", "")
                    queue_path = os.path.join(self.queue, f"{base_id}.json")
                    if os.path.exists(queue_path):
                        try:
                            with open(queue_path) as qf:
                                intent = json.load(qf)
                            self.log(f"[QUEUE] Found and loaded intent for {base_id}")
                        except Exception as e:
                            self.log(f"[QUEUE][ERROR] Failed to load intent for {base_id}: {e}")

                    self.dispatch_reply(response, base_id, mode, intent)

                    processed += 1
                except Exception as e:
                    self.log(f"[GPT][ERROR] Failed to process {fname}: {e}")
                try:
                    os.remove(full_path)
                except Exception as e:
                    self.log(f"[GPT][WARN] Could not delete {fname}: {e}")
        except Exception as e:
            self.log(f"[GPT][CRITICAL] Worker crashed: {e}")

        self.log(f"[GPT_REFLEX][PROCESSED_MESSAGES] {processed}")

    def ask_gpt(self, prompt):
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return result.choices[0].message.content.strip()
        except Exception as e:
            self.log(f"[GPT][FAIL] OpenAI v1.x call failed: {e}")
            return "[GPT ERROR] Failed to generate response."

    def dispatch_reply(self, message, base_id, mode="markdown", intent=None):
        payload = {
            "response": message,
            "mode": mode,
            "ts": int(time.time()),
            "intent": intent or {}
        }
        path = os.path.join(self.replies, f"{base_id}.msg")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self.log(f"[REPLY] Response written to replies/{base_id}.msg")

    def dispatch_cmd(self, cmd):
        target = cmd["target"]
        action = cmd["command"]
        payload = {
            "command": action,
            "target": target,
            "reason": cmd.get("reason", "Autonomous GPT reflex trigger")
        }
        ts = int(time.time())
        path = os.path.join(self.matrix_inbox, f"gpt_reflex_cmd_{ts}.cmd")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self.log(f"[REFLEX] Dispatched .cmd to Matrix for {action} → {target}")

    def extract_command(self, message):
        try:
            msg = message.lower()
            if "kill" in msg and "oracle" in msg:
                return {"command": "kill", "target": "oracle-1", "reason": message}
            if "restart" in msg and "oracle" in msg:
                return {"command": "resume", "target": "oracle-1", "reason": message}
        except Exception:
            return None
        return None


if __name__ == "__main__":
    agent = Agent()
    agent.boot()