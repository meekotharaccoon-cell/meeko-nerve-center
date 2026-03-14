#Authored by Daniel F MacDonald and ChatGPT aka The Generals
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

from flask import Response
from flask import Flask, request, jsonify
import ssl
import json
import threading
import time
import base64

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.config import ENCRYPTION_CONFIG

from Crypto.Cipher import AES

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        self.AGENT_VERSION = "1.2.0"
        self.app = Flask(__name__)
        self.port = 65431

        config = self.tree_node.get("config", {})
        self.allowlist_ips = config.get("allowlist_ips", [])

        self.payload_dir = os.path.join(self.path_resolution['comm_path'], "matrix", "payload")
        swarm_root = self.path_resolution["install_path"]
        self.cert_path = os.path.join(swarm_root, "certs", "https_certs", "server.fullchain.crt")
        self.key_path = os.path.join(swarm_root, "certs", "https_certs", "server.key")
        self.client_ca = os.path.join(swarm_root, "certs", "https_certs", "rootCA.pem")
        self.local_tree_root = None
        #keep trying to start for infinity: false do max retries in method
        self.run_server_retries = True
        self._last_dir_request = 0
        self.configure_routes()

    def pre_boot(self):
        self.log("[PRE-BOOT] Matrix HTTPS Agent preparing routes and scanner.")
        threading.Thread(target=self.run_server, daemon=True).start()

    def post_boot(self):
        self.log(f"{self.NAME} v{self.AGENT_VERSION} – agent ready and active.")

    def process_command(self, data):
        self.log(f"[CMD] Received delegated command: {data}")

    def cert_exists(self):
        return os.path.exists(self.cert_path) and os.path.exists(self.key_path)

    def worker_pre(self):
        self.log("[MATRIX_HTTPS] Boot initialized. Port online, certs verified.")

    def worker_post(self):
        self.log("[MATRIX_HTTPS] HTTPS interface shutting down. The swarm will feel it.")

    def configure_routes(self):

        # matrix_https.py (inside MatrixHTTPS class)

        @self.app.route("/agents", methods=["GET"])
        def get_agent_list():
            try:

                ip = request.remote_addr or "unknown"

                if self.allowlist_ips and ip not in self.allowlist_ips:
                    self.log(f"Request from disallowed IP: {ip}", block="agents")
                    return jsonify({"status": "error", "message": "Access denied"}), 403

                self.log("[CMD] Getting Live Agent List")
                comm_path = self.path_resolution['comm_path']
                agents = []

                if os.path.exists(comm_path):
                    for name in os.listdir(comm_path):
                        path = os.path.join(comm_path, name)
                        if name.lower().startswith("new folder") or name.startswith("."):
                            continue
                        if os.path.isdir(path) and os.path.exists(os.path.join(path, "agent_tree.json")):
                            agents.append(name)

                return jsonify({"status": "ok", "agents": sorted(agents)})

            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/matrix/ping", methods=["GET"])
        def ping():

            ip = request.remote_addr or "unknown"

            if self.allowlist_ips and ip not in self.allowlist_ips:
                self.log(f"Request from disallowed IP: {ip}", block="ping")
                return jsonify({"status": "error", "message": "Access denied"}), 403

            return jsonify({"status": "ok"}), 200

        @self.app.route("/matrix", methods=["POST"])
        def receive_command():
            try:
                ip = request.remote_addr or "unknown"

                if self.allowlist_ips and ip not in self.allowlist_ips:
                    self.log(f"[MATRIX-HTTPS][BLOCKED] Request from disallowed IP: {ip}")
                    return jsonify({"status": "error", "message": "Access denied"}), 403

                self.log(f"[MATRIX-HTTPS][SOURCE-IP] Packet received from {ip}")
                payload = request.get_json()
                ctype = payload.get("handler")
                content = payload.get("content", {})
                timestamp = payload.get("timestamp", time.time())

                self.log(f"[MATRIX-HTTPS][RECEIVED] {ctype} from {ip} → {content}")

                # === 1. Matrix-HTTPS native commands ===
                if ctype == "cmd_get_log":
                    uid = content.get("universal_id")
                    if not uid:
                        return jsonify({"status": "error", "message": "Missing universal_id"}), 400

                    log_path = os.path.join(self.path_resolution["comm_path"], uid, "logs", "agent.log")

                    if os.path.exists(log_path):
                        try:
                            key_bytes = None
                            if self.debug.is_enabled() and ENCRYPTION_CONFIG.is_enabled():
                                self.log("[DEBUG] ENCRYPTION_CONFIG is_enabled = %s" % ENCRYPTION_CONFIG.is_enabled())
                            if ENCRYPTION_CONFIG.is_enabled():
                                swarm_key = ENCRYPTION_CONFIG.get_swarm_key()
                                key_bytes = base64.b64decode(swarm_key)
                                self.log(f"[DEBUG] Swarm key loaded: {swarm_key[:10]}...")

                            rendered_lines = []

                            with open(log_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    try:
                                        if key_bytes:
                                            line = decrypt_log_line(line, key_bytes)

                                        entry = json.loads(line)
                                        ts = entry.get("timestamp", "?")
                                        lvl = entry.get("level", "INFO")
                                        msg = entry.get("message", "")
                                        emoji = {
                                            "INFO": "🔹", "ERROR": "❌", "WARNING": "⚠️", "DEBUG": "🐞"
                                        }.get(lvl.upper(), "🔸")
                                        rendered_lines.append(f"{emoji} [{ts}] [{lvl}] {msg}")
                                    except Exception as e:
                                        rendered_lines.append(f"[MALFORMED] {line.strip()}")

                            output = "\n".join(rendered_lines[-250:])
                            #output = "\n".join(rendered_lines)

                            if self.debug.is_enabled():
                                self.log(f"[LOG-DELIVERY] ✅ Sent {len(rendered_lines)} lines for {uid}")

                            return Response(
                                json.dumps({"status": "ok", "log": output}, ensure_ascii=False),
                                status=200,
                                mimetype="application/json"
                            )

                        except Exception as e:
                            self.log(f"[HTTPS-LOG][ERROR] Could not process log for {uid}", error=e)
                            return jsonify({"status": "error", "message": str(e)}), 500

                    return #dir doesn't exist, yet

                elif ctype == "cmd_list_tree":

                    try:

                        #request a refresh of agent_tree_master after 5mins
                        if time.time() - self._last_dir_request > 60:  # 5-minute window
                            self._last_dir_request = time.time()

                            # request the agent_tree_master from Matrix
                            pl = {"origin": self.command_line_args['universal_id'],
                                  "handler": "cmd_deliver_agent_tree",
                                  "content": {"none": "none"},
                                  "timestamp": time.time()}

                            pk = self.get_delivery_packet("standard.command.packet", new=True)
                            pk.set_data(pl)

                            self.pass_packet(pk, "matrix")

                        football = self.get_football(type=self.FootballType.CATCH)
                        try:

                            fpath = os.path.join(self.path_resolution["comm_path_resolved"], 'directive', 'agent_tree_master.json')

                            if os.path.exists(fpath):
                                tree_path = {

                                    "path": self.path_resolution["comm_path"],
                                    "address": "matrix-https",
                                    "drop": "directive",
                                    "name": "agent_tree_master.json"

                                }

                                tp = self.load_directive(tree_path, football)
                                self.local_tree_root = tp.root.copy()


                            return jsonify({"status": "ok", "tree": self.local_tree_root}), 200

                        except Exception as e:

                            return jsonify( {"status": "error", "message": "Failed to load directive or invalid tree."}), 500


                    except Exception as e:

                        self.log(f"[LIST_TREE][ERROR] {str(e)}")

                        return jsonify({"status": "error", "message": str(e)}), 500

                    return

                elif ctype == "cmd_ping":
                    return jsonify({"status": "ok"}), 200

                # === 2. All other commands go to Matrix ===
                target = "matrix"

                payload['origin'] = self.command_line_args['universal_id']

                pk = self.get_delivery_packet("standard.command.packet", new=True)
                pk.set_data(payload)

                pk2 = self.get_delivery_packet("standard.general.json.packet", new=True)

                pk.set_packet(pk2,"content")

                self.pass_packet(pk, target)

                return jsonify({"status": "ok", "message": f"{ctype} routed to Matrix"})

            except Exception as e:
                self.log(f"[MATRIX-HTTPS][ERROR] {e}")

        def threaded_log_response(self, uid, client_response):
            try:
                log_path = os.path.join(self.path_resolution["comm_path"], uid, "logs", "agent.log")

                if not os.path.exists(log_path):
                    return client_response({"status": "error", "message": "Log not found"}, 404)

                key_bytes = None
                if ENCRYPTION_CONFIG.is_enabled():
                    swarm_key = ENCRYPTION_CONFIG.get_swarm_key()
                    key_bytes = base64.b64decode(swarm_key)

                rendered_lines = []

                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            if key_bytes:
                                line = self.decrypt_log_line(line, key_bytes)
                            entry = json.loads(line)
                            ts = entry.get("timestamp", "?")
                            lvl = entry.get("level", "INFO")
                            msg = entry.get("message", "")
                            emoji = {"INFO": "🔹", "ERROR": "❌", "WARNING": "⚠️", "DEBUG": "🐞"}.get(lvl.upper(), "🔸")
                            rendered_lines.append(f"{emoji} [{ts}] [{lvl}] {msg}")
                        except Exception:
                            rendered_lines.append(f"[MALFORMED] {line.strip()}")

                output = "\n".join(rendered_lines)
                self.log(f"[LOG-DELIVERY] ✅ Sent {len(rendered_lines)} lines for {uid}")
                return client_response({"status": "ok", "log": output}, 200)

            except Exception as e:
                self.log(f"[HTTPS-LOG][ERROR] Could not process log for {uid}: {e}")
                return client_response({"status": "error", "message": str(e)}, 500)

        def decrypt_log_line(line, key_bytes):
            try:
                blob = base64.b64decode(line.strip())
                nonce, tag, ciphertext = blob[:12], blob[12:28], blob[28:]
                cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
                return cipher.decrypt_and_verify(ciphertext, tag).decode()
            except Exception as e:
                return f"[DECRYPT-FAIL] {str(e)}"

    def run_server(self):
        retry_delay = 10  # seconds between retries
        max_retries = 5
        retries = 0

        while (retries < max_retries) or self.run_server_retries:

            try:
                self.log("[HTTPS] Starting run_server()...")

                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(cafile=self.client_ca)
                context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)

                self.log(f"[HTTPS] Listening on port {self.port}")
                self.app.run(host="0.0.0.0", port=self.port, ssl_context=context)

                break  # If server exits cleanly, stop the loop

            except Exception as e:
                self.log(f"[HTTPS][FAIL] Server failed to start or crashed", error=e)
                retries += 1
                self.log(f"[HTTPS][RETRY] Attempt {retries}/{max_retries} in {retry_delay}s")
                time.sleep(retry_delay)

        if retries >= max_retries:
            self.log("[HTTPS][ABORT] Max retries reached. Server not started.")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()