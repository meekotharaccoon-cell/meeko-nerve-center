# 📡 TelegramRelayAgent — Forwards Swarm Logs to Telegram
# Authored by Daniel F MacDonald and ChatGPT aka The Generals
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import requests
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        config = self.tree_node.get("config", {})

        self.token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.comm_folder = config.get("watch_comm", "mailman-1")
        path = os.path.join(self.path_resolution["comm_path_resolved"], "outgoing")
        os.makedirs(path, exist_ok=True)
        self.watch_path = os.path.join(self.path_resolution["comm_path_resolved"], "incoming")
        os.makedirs(self.watch_path, exist_ok=True)

    def worker_pre(self):
        self.log("[TELEGRAM] Telegram relay activated. Awaiting message drops...")

    def worker_post(self):
        self.log("[TELEGRAM] Relay shutting down. No more echoes for now.")

    def cmd_send_alert_msg(self, content, packet, identity:IdentityObject = None):
        try:
            message = self.format_message(content)
            self.send_to_telegram(message)
            self.log("[TELEGRAM] Message relayed successfully.")
        except Exception as e:
            self.log(f"[TELEGRAM][ERROR] Failed to relay message: {e}")

    def format_message(self, data: dict):
        """Builds a detailed message from embed_data if present."""
        embed = data.get("embed_data")
        if embed:
            # Construct a detailed message from the embed data
            title = embed.get('title', 'Swarm Alert')
            description = embed.get('description', 'No details.')
            footer = embed.get('footer', '')
            return f"*{title}*\n\n{description}\n\n_{footer}_"
        else:
            # Fallback for older alerts
            return data.get("formatted_msg") or data.get("msg") or "[SWARM] No content."

    def send_to_telegram(self, message):
        if not self.token or not self.chat_id:
            self.log("[TELEGRAM][ERROR] Missing bot_token or chat_id.")
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.chat_id, "text": message})
            self.log("[TELEGRAM] Message relayed.")
        except Exception as e:
            self.log(f"[TELEGRAM][ERROR] Telegram delivery failed: {e}")

def on_alarm(self, payload):
    msg = f"🚨 [{payload['level'].upper()}] {payload['universal_id']} — {payload['cause']}"
    self.send_message_to_platform(msg)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
