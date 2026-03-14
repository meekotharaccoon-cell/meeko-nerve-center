#Authored by Daniel F MacDonald and ChatGPT aka The Generals
#Gemini, docstring-ing and added code enhancements.
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
# ╔══════════════════════════════════════════════════════════╗
# ║                  📡 DISCORD AGENT V3 📡                  ║
# ║     Matrix-Compatible · Swarm Speaker · Relay-Class     ║
# ╚══════════════════════════════════════════════════════════╝

import threading
import discord as discord_real
from discord.ext import commands
import asyncio

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        self.discord_client = None
        self.bot = None

        # Inject full tree_node so BootAgent sees config
        self.directives = self.tree_node

        self.inbox_paths=['incoming']
        path = os.path.join(self.path_resolution["comm_path_resolved"], "incoming")
        os.makedirs(path, exist_ok=True)
        self.inbox_paths.append(path)

        # Local config for this agent
        config = self.directives.get("config", {})
        self.token = config.get("bot_token")
        channel_id = config.get("channel_id")
        if channel_id is not None:
            self.channel_id = int(channel_id)
        else:
            self.channel_id = 0
        self.name = "DiscordAgentV3e"

    def worker_pre(self):
        self.log("[DISCORD] Worker alive, idling.")

    def worker(self, config:dict = None, identity:IdentityObject = None):

        interruptible_sleep(self, 2320)

    def post_boot(self):
        self.log("[DISCORD] Payload watcher thread starting...")

        self.log("[DISCORD] Starting client thread...")
        threading.Thread(target=self.start_discord_client, daemon=True).start()

    def start_discord_client(self):
        def runner():
            try:
                print("[DISCORD] Setting up event loop...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                intents = discord_real.Intents.default()
                intents.messages = True
                intents.message_content = True

                self.bot = commands.Bot(command_prefix="!", intents=intents)

                @self.bot.event
                async def on_ready():
                    print("[ON_READY] Triggered!")
                    self.log(f"[DISCORD] Connected as {self.bot.user}")
                    for guild in self.bot.guilds:
                        for channel in guild.text_channels:
                            print(f"[DEBUG] {channel.name} — {channel.id}")
                    try:
                        channel = await self.bot.fetch_channel(self.channel_id)
                        await channel.send("DiscordAgent V3e online and responding.")
                    except Exception as e:
                        self.log(f"[DISCORD][ERROR] Channel access failed: {e}")

                async def run_bot():
                    print("[DISCORD] run_bot() starting...")
                    await self.bot.start(self.token)

                loop.create_task(run_bot())
                loop.run_forever()

            except Exception as e:
                self.log(f"[DISCORD][ERROR] Client thread failed: {e}")
                import traceback
                traceback.print_exc()

        # Launch in a dedicated thread
        threading.Thread(target=runner, daemon=True).start()

    def cmd_send_alert_msg(self, content: dict, packet, identity: IdentityObject = None):
        """
        Receives a unified alert packet and renders the best format available.
        """
        # Check if rich embed data exists
        if content.get("embed_data"):
            # Use the new logic to send a rich embed
            self.send_embed_from_data(content["embed_data"])
        else:
            # Fall back to sending plain text for older/simpler alerts
            message_to_send = content.get("formatted_msg") or content.get("msg") or "[SWARM] No content."
            self.send_text_message(message_to_send)

    def send_text_message(self, message: str):
        try:
            self.send_to_discord(message)
            self.log("[DISCORD] Message relayed successfully.")
        except Exception as e:
            self.log(f"[DISCORD][ERROR] Failed to relay message: {e}")

    def send_to_discord(self, message):
        if not self.bot or not self.channel_id:
            self.log("[DISCORD][ERROR] Bot not ready or channel ID missing.")
            return
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(message), self.bot.loop)
            else:
                self.log("[DISCORD][ERROR] Channel not found.")
        except Exception as e:
            self.log(f"[DISCORD][ERROR] Discord delivery failed: {e}")

    def send_embed_from_data(self, content: dict):
        """
        Receives embed data and renders it in a Discord channel.
        This method replaces the old cmd_send_alert_msg.
        """
        if not self.bot or not self.channel_id:
            self.log("[DISCORD][ERROR] Bot not ready or channel ID missing.")
            return

        try:
            # Convert color string to a discord.Color object, default to blurple
            color_str = content.get("color", "blurple")
            color_obj = getattr(discord_real.Color, color_str, discord_real.Color.default)()

            # Create the embed object directly from the packet's content
            embed = discord_real.Embed(
                title=content.get("title", "Swarm Alert"),
                description=content.get("description", "No details provided."),
                color=color_obj
            )
            embed.set_footer(text=content.get("footer", ""))

            # Send the embed
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(embed=embed), self.bot.loop)
            else:
                self.log(f"[DISCORD][ERROR] Channel {self.channel_id} not found.")

        except Exception as e:
            self.log(f"[DISCORD][ERROR] Failed to send embed: {e}")
            import traceback
            traceback.print_exc()

    def format_message(self, data: dict):
        """Builds a detailed message from embed_data if present."""
        return data.get("formatted_msg") or data.get("msg") or "[SWARM] No content."

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
