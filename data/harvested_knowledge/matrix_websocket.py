import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
#Authored by Daniel F MacDonald and ChatGPT aka The Generals
import ssl
import time
import copy
import threading
import asyncio
import websockets
import json
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

from matrixswarm.core.boot_agent import BootAgent

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        self.AGENT_VERSION = "1.2.0"

        self.clients = set()
        config = self.tree_node.get("config", {})
        self.allowlist_ips = config.get("allowlist_ips", [])
        self.port = config.get("port", 8765)
        self.clients = set()
        self.loop = None
        self.websocket_ready = False
        swarm_root = self.path_resolution["install_path"]
        self.cert_dir = os.path.join(swarm_root, "certs", "socket_certs")
        self._stop_event = None
        self._thread = None
        self._config = None
        self._lock = threading.Lock()

    def post_boot(self):
        self.log(f"{self.NAME} v{self.AGENT_VERSION} – agent ready and active.")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        """
        Starts or restarts the WebSocket thread if config changes or thread is dead.
        """
        if config is None:
            config = self.tree_node.get("config", {})  # Default fallback

        with self._lock:
            if self._thread and self._thread.is_alive():
                if config == self._config:
                    # Config unchanged, thread alive — do nothing
                    return
                else:
                    self.log("[WS] Launching WebSocket thread... Or Config changed and restarting thread...")
                    self._stop_event.set()
                    self._thread.join(timeout=3)
            elif self._thread and not self._thread.is_alive():
                self.log("[WS] Previous thread is dead — restarting...")

            # Start new thread
            self._config = copy.deepcopy(config)  # Defensive copy
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self.start_socket_loop, daemon=True)
            self._thread.start()
            self.log("[WS] WebSocket thread started.")

    def start_socket_loop(self):
        try:
            self.log("[WS] Booting WebSocket TLS thread...")
            time.sleep(1)

            cert_path = os.path.join(self.cert_dir, "server.crt")
            key_path = os.path.join(self.cert_dir, "server.key")

            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                self.log(f"[WS][FATAL] Missing cert/key file at {cert_path} or {key_path}")
                self.running = False
                return

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop

            async def launch():
                self.log("[WS] Preparing SSL context...")
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)

                self.log(f"[WS] Attempting to bind WebSocket on port {self.port}...")
                server = await websockets.serve(
                    self.websocket_handler,
                    "0.0.0.0",
                    self.port,
                    ssl=ssl_context
                )

                self.websocket_ready = True
                self.log(f"[WS] SECURE WebSocket bound on port {self.port} (TLS enabled)")
                await server.wait_closed()

            loop.run_until_complete(launch())

            # Run the loop in a background task that watches the stop event
            async def monitor_stop():
                while not self._stop_event.is_set():
                    await asyncio.sleep(1)
                self.log("[WS] Stop event received — shutting down WebSocket server.")
                loop.stop()

            # Schedule the monitor coroutine
            loop.create_task(monitor_stop())

            loop.run_forever()
            loop.close()
            self.log("[WS] Event loop closed.")


        except Exception as e:
            self.log(f"[WS][FATAL] WebSocket startup failed", error=e, block="main_try")
            self.running = False

    def cmd_health_report(self, content, packet, identity:IdentityObject = None):
        self.log(f"[RELAY] Received health report for {content.get('target_universal_id', '?')}")

    async def websocket_handler(self, websocket):

        try:

            ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
            self.log(f"[WS][CONNECT] Client connected from IP: {ip}")

            if self.allowlist_ips and ip not in self.allowlist_ips:
                self.log(f"[WS][BLOCK] Connection from {ip} rejected (not in allowlist)")
                await websocket.close(reason="IP not allowed")
                return

            self.log("[WS][TRACE] >>> websocket_handler() CALLED <<<")
            self.log("[WS] HANDLER INIT - Client added")
            # Add the client securely to the clients set
            self.clients.add(websocket)
            self.log("[WS] HANDLER INIT - Client added")

            while True:
                self.log("[WS] Awaiting message...")

                try:
                    # Await a message from the client
                    message = await websocket.recv()
                    self.log(f"{repr(message)}")

                    # Attempt to decode JSON (if applicable)
                    try:

                        data = json.loads(message)

                        self.log(f"[WS][VALID MESSAGE] {data}")
                    except json.JSONDecodeError:
                        self.log("[WS][ERROR] Malformed JSON received")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
                        continue

                    # Respond with acknowledgment
                    await websocket.send(json.dumps({
                        "type": "ack",
                        "echo": message
                    }))

                except websockets.ConnectionClosed as cc:
                    # Handle a graceful client disconnection
                    self.log(f"[WS][DISCONNECT] Client disconnected gracefully: ({cc.code}) {cc.reason}")
                    break

                except Exception as e:
                    # Handle unexpected errors during message handling
                    self.log(f"[WS][ERROR] Unexpected error during message processing: {e}")
                    break

        finally:
            # Ensure client is removed from the set upon disconnect
            self.clients.discard(websocket)
            self.log(f"[WS] Client disconnected and removed. Active clients: {len(self.clients)}")

    def cmd_rpc_route(self, content, packet, identity:IdentityObject = None):
        try:
            self.log("Incoming routed RPC packet.")

            self.cmd_broadcast(content, content)
            self.log(f"Routed response_id={content.get('response_id')} status={content.get('status')}")
        except Exception as e:
            self.log(error=e)  # Optional: write full trace to logs

    def cmd_send_alert_msg(self, content, packet, identity:IdentityObject = None):
        try:
            # Format the alert message
            msg = content.get("formatted_msg") or content.get("msg") or "[SWARM] Alert received."

            # Construct GUI-style feed packet
            broadcast_packet = {
                "handler": "cmd_alert_to_gui",
                "origin": content.get("origin", "unknown"),
                "timestamp": time.time(),
                "content": {
                    "msg": msg,
                    "level": content.get("level", "info"),
                    "origin": content.get("origin", "unknown"),
                    "formatted_msg": msg
                }
            }

            # Dispatch it via WebSocket
            self.cmd_broadcast(broadcast_packet["content"], broadcast_packet)

            self.log("Alert message sent to GUI feed.")
        except Exception as e:
            self.log(error=e)  # Optional: write full trace to logs

    def cmd_alert_to_gui(self, content, packet, identity:IdentityObject = None):
        self.log(f"Dispatching alert to GUI: {content}")
        self.cmd_broadcast(content, packet)

    def cmd_broadcast(self, content, packet, identity:IdentityObject = None):
        if not hasattr(self, "loop") or self.loop is None:
            self.log("[WS][REFLEX][SKIP] Event loop not ready.")
            return

        if not getattr(self, "websocket_ready", False):
            self.log("[WS][REFLEX][WAITING] Socket not bound.")
            return

        try:
            self.log(f"[WS][REFLEX]{packet}")
            data = json.dumps(packet)
            dead = []
            for client in self.clients:
                try:
                    asyncio.run_coroutine_threadsafe(client.send(data), self.loop)
                except Exception:
                    dead.append(client)

            for c in dead:
                self.clients.discard(c)

            self.log(f"Broadcasted to {len(self.clients)} clients.")
        except Exception as e:
            self.log(error=e)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()