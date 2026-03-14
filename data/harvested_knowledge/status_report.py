import json
import asyncio
import time
def attach(agent, config):
    """
    Reflex handler for health_report messages.
    Sends them to all connected WebSocket clients.
    """

    def cmd_health_report(self, content, packet):
        self.log(f"[WS][HEALTH] Received health_report:\n{json.dumps(content, indent=2)}")
        self.forward_to_clients(packet)

    def forward_to_clients(self, packet):
        if not getattr(self, "websocket_ready", False):
            self.log("[WS][FORWARD][SKIP] Relay not ready.")
            return
        try:
            data = json.dumps(packet)

            dead = []
            for client in self.clients:
                try:
                    asyncio.run_coroutine_threadsafe(client.send(data), self.loop)
                except Exception:
                    dead.append(client)
            for c in dead:
                self.clients.discard(c)
            self.log(f"[WS][FORWARD] Relayed to {len(self.clients)} clients.")
        except Exception as e:
            self.log(f"[WS][FORWARD][ERROR] {e}")


    agent.log("[FACTORY] Reflex handler msg_health_report loaded.")

    def cmd_force_test(self, content, packet):
        self.log("[WS][FORCE] Reflex test triggered — sending fake ping to all clients.")

        self.log(f"[WS][FORCE] Connected clients: {len(self.clients)}")

        if not getattr(self, "websocket_ready", False) or not getattr(self, "clients", []):
            self.log("[WS][FORCE] Relay not ready or no clients connected.")
            return

        test_packet = {
            "type": "ack",
            "message": "reflex echo test",
            "source": "msg_force_test",
            "timestamp": time.time()
        }

        data = json.dumps(test_packet)
        for client in list(self.clients):
            try:
                asyncio.run_coroutine_threadsafe(client.send(data), self.loop)
            except Exception as e:
                self.log(f"[WS][FORCE-ERROR] {e}")

    # Attach methods to the agent
    agent.cmd_health_report = cmd_health_report.__get__(agent)

    agent.forward_to_clients = forward_to_clients.__get__(agent)

    agent.cmd_force_test = cmd_force_test.__get__(agent)