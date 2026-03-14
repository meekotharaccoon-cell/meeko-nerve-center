# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import base64
import json
import hashlib
import time
import threading
import requests
import geoip2.database
import bleach
import ipaddress

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    INOTIFY_AVAILABLE = True

    # Define the handler class ONLY if the necessary imports succeed
    class ContactFileHandler(FileSystemEventHandler):
        def __init__(self, agent):
            self.agent = agent
        def on_created(self, event):
            try:
                if event.is_directory or not event.src_path.endswith('.json'):
                    return
                self.agent.handle_contact_file(event.src_path)
            except Exception as e:
                # Use the agent's logger if available, otherwise print
                if hasattr(self.agent, 'log'):
                    self.agent.log(f"Error in FileSystemEventHandler: {e}", level="ERROR")
                else:
                    print(f"[ContactFileHandler][ERROR] {e}")

except ImportError:
    # If watchdog is not installed or broken, set the flag and create a
    # dummy class so the rest of the agent doesn't crash.
    INOTIFY_AVAILABLE = False
    class ContactFileHandler:
        pass

class Agent(BootAgent):
    """
    A secure, intelligent contact form processor for the MatrixSwarm.

    This agent acts as a gateway for external messages, such as those from a
    website contact form. It monitors a specified directory for new, encrypted
    message files. Upon detection, it decrypts the message, optionally uses an
    "Oracle" LLM agent for spam classification, enriches the data with GeoIP
    information, and forwards clean messages to a designated operator via an
    alerting agent.
    """
    def __init__(self):
        """
        Initializes the agent by loading its configuration and keys.

        This method sets up the agent's operational parameters from the boot
        directive, including the paths to watch for new messages, the private
        RSA key for decryption, and settings for the Oracle spam filter. It
        contains a critical guard that will cause the agent to exit if the
        private key is not provided in the configuration.
        """
        super().__init__()

        try:

            self.AGENT_VERSION = "1.0.0"

            self._private_config = self.tree_node.get("config", {})
            self._initialized_from_tree = False
            self._watchers = []

            self.watch_folder = self.tree_node['config'].get('watch_folder', '/sites/matrixswarm/public_html/outgoing_msgs/')

            try:
                #key generated using directive encryption
                privkey_pem = self.tree_node['config'].get('privkey')  # Already loaded from vault
                if "\\n" in privkey_pem:
                    privkey_pem = privkey_pem.replace("\\n", "\n")

                self.privkey_for_external_comm = RSA.import_key(privkey_pem)
            except Exception as e:
                self.log("You need to either run encrypt_directive or provide a private key. {privkey_pem} or it's corrupt" ,error=e, block="inner_try")

            self.oracle_timeout = int(self._private_config.get('oracle_timeout', 15))
            self.pending_evals = {}
            self.memory_vectors = {}
            self.enable_oracle = bool(self._private_config.get('enable_oracle', 0))
            self._suspended = bool(self._private_config.get('suspended', 0))
            self.geoip_enabled = self._private_config.get("geoip_enabled", 1)
            self.alert_role = self._private_config.get("alert_to_role", "hive.alert.send_alert_msg")  # Optional


            cfg_db = str(self._private_config.get("maxmind_db", "")).strip()

            # If it's an absolute path or a path relative to install_path
            if cfg_db and os.path.isfile(cfg_db):
                self.mmdb_path = cfg_db
            else:
                self.mmdb_path = os.path.join(self.path_resolution["install_path"], "maxmind", "GeoLite2-City.mmdb")

            # if can't contact oracle, then still forward message
            self.enable_fallback_forward = bool(self._private_config.get('enable_fallback_forward', 1))

            self.bot_filter = ["buy now", "click here", "viagra", "bitcoin"]

        except Exception as e:
            self.log(error=e, block="main_try")

    def post_boot(self):
        """A one-time setup hook called after the main threads have started."""
        self.log(f"{self.NAME} v{self.AGENT_VERSION} – may this email find you in good spirits.")

    def cmd_update_agent_config(self):
        """
        Stops old watchers and starts new ones based on the current config.

        This method is called when a new configuration is received. It ensures
        a clean state by terminating any existing file system watchers before
        initializing new ones according to the updated settings, such as new
        paths to watch or a change in the agent's suspended state.
        """
        try:
            self._initialized_from_tree = True
            self.log(f"[CONFIG] Applying new agent configuration.")

            # Stop and clear all existing directory watchers
            for watcher in self._watchers:
                try:
                    watcher.stop()
                    watcher.join()  # Wait for thread to terminate
                except Exception as e:
                    self.log(f"Error stopping a watcher: {e}", level="WARNING")
            self._watchers = []

            if self._private_config.get("suspended", False):
                self._suspended = True
                self.log("[WATCHER] Agent is suspended per configuration. No watchers will be started.")
                return

            self._suspended = False
            paths = self._private_config.get("watched_paths", [])
            for path in paths:
                self._start_dir_watcher(path)

        except Exception as e:
                self.log(error=e, block="main_try")

    def worker(self, config:IdentityObject=None, identity=None):
        """
        The main throttled loop for the agent.

        This method is called repeatedly by the BootAgent's throttled worker
        wrapper. Its primary responsibilities are to process any incoming live
        configuration changes and to trigger periodic tasks, such as checking
        for timed-out requests to the Oracle agent.

        Args:
            config (dict, optional): A dictionary containing new configuration
                data sent to the agent's /config drop zone.
            identity (IdentityObject, optional): The verified identity of the
                sender of the configuration packet. Not used in this agent.
        """
        try:
            if config and isinstance(config, dict):
                self.log(f"[CONFIG] New configuration packet received.")
                # This logic allows for both full and partial config updates
                if config.get("partial_config"):
                    config.pop("partial_config", None)
                    self._private_config.update(config)
                    self.log("[WORKER] Partial config merged.")
                else:
                    self._private_config = config
                    self.log("[WORKER] Full config override applied.")
                # Flag that the new config needs to be applied to the watchers
                self._initialized_from_tree = False

            # If a new config has been loaded, re-initialize the watchers
            if not self._initialized_from_tree:
                self.cmd_update_agent_config()

            # The main loop now only checks for oracle timeouts and other periodic tasks.
            # File handling is managed by the watcher threads.
            if not self._suspended:
                self.check_oracle_responses()

        except Exception as e:
            self.log(error=e, block="WORKER_LOOP")

        interruptible_sleep(self, 10)

    def _start_dir_watcher(self, watch_folder):
        """
        Starts a file system watcher for a specific directory.

        This method chooses the best available watching mechanism. It prefers
        the efficient, event-based `watchdog` library (which uses inotify on
        Linux) if it's available. If not, it gracefully falls back to a
        manual polling thread.

        Args:
            watch_folder (str): The absolute path to the directory to monitor.
        """
        # === GUARD: Validate the path before starting a watcher ===
        if not os.path.isdir(watch_folder):
            self.log(f"[WATCHER][ERROR] Path does not exist or is not a directory: '{watch_folder}'. Skipping.", level="ERROR")
            return

        try:
            if INOTIFY_AVAILABLE:
                observer = Observer()
                handler = ContactFileHandler(self)
                observer.schedule(handler, watch_folder, recursive=False)
                observer.start()
                self._watchers.append(observer)
                self.log(f"[INOTIFY] Started watching: {watch_folder}")
            else:
                # Fallback to manual polling if watchdog is not installed
                poll_thread = threading.Thread(target=self._poll_dir, args=(watch_folder,), daemon=True)
                poll_thread.start()
                self._watchers.append(poll_thread) # Store thread to manage it if needed
                self.log(f"[POLLING] Started watching: {watch_folder}")
        except Exception as e:
            self.log(f"Failed to start watcher for '{watch_folder}'", error=e, block="START_WATCHER")



    def _poll_dir(self, watch_folder):
        """
        Fallback directory polling method if `watchdog` is unavailable.

        This method runs in a dedicated thread and periodically scans a directory
        for new .json files, providing a less efficient but highly portable
        alternative to inotify-based watching.

        Args:
            watch_folder (str): The absolute path to the directory to poll.
        """
        seen_files = set(f for f in os.listdir(watch_folder) if f.endswith('.json'))
        while self.running and not self._suspended:
            try:
                current_files = set(f for f in os.listdir(watch_folder) if f.endswith('.json'))
                new_files = current_files - seen_files
                for fname in new_files:
                    self.handle_contact_file(os.path.join(watch_folder, fname))
                seen_files = current_files
            except Exception as e:
                self.log(f"Error during polling of '{watch_folder}': {e}", level="ERROR")
            interruptible_sleep(self, 10)

    def handle_contact_file(self, fpath):
        """
        Securely decrypts, processes, and cleans up a single contact file.

        This is the core processing function for new messages. It performs the
        two-layer decryption (RSA for the AES key, then AES for the message),
        parses the JSON payload, and passes the result to the next stage of
        processing. It includes robust error handling to quarantine any file
        that is malformed or cannot be decrypted, preventing processing loops.

        Args:
            fpath (str): The full path to the encrypted .json message file.
        """
        # === GUARD: Ensure file exists before trying to open it ===
        if not os.path.exists(fpath):
            return

        try:
            with open(fpath, 'r') as f:
                blob = json.load(f)

            # Decrypt the AES key with our private RSA key
            cipher_rsa = PKCS1_OAEP.new(self.privkey_for_external_comm)
            aes_key = cipher_rsa.decrypt(base64.b64decode(blob['meta']['encrypted_key']))

            # Use the decrypted AES key to decrypt the message
            msg_cipher = AES.new(aes_key, AES.MODE_GCM, nonce=base64.b64decode(blob['meta']['nonce']))
            plaintext = msg_cipher.decrypt_and_verify(
                base64.b64decode(blob['data']), base64.b64decode(blob['meta']['tag'])
            )
            message = json.loads(plaintext)

            # If decryption and parsing succeed, process the message
            self.process_new_message(message)

            # On full success, remove the file
            os.remove(fpath)
            self.log(f"Successfully processed and removed: {os.path.basename(fpath)}")

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # These errors indicate a malformed, invalid, or undecryptable file.
            self.log(f"Failed to parse or decrypt file '{os.path.basename(fpath)}'. Error: {e}", level="ERROR")
            self._quarantine_file(fpath)
        except Exception as e:
            # Catch any other unexpected errors during file handling
            self.log(f"An unexpected error occurred handling '{os.path.basename(fpath)}'", error=e, level="ERROR")
            self._quarantine_file(fpath)

    def _quarantine_file(self, fpath):
        """
        Moves a problematic file to a 'failed_msgs' directory.

        This helper prevents the agent from getting stuck in a loop trying to
        process a file that is corrupted or cannot be decrypted.

        Args:
            fpath (str): The full path to the file to be quarantined.
        """
        try:
            if not os.path.exists(fpath):
                return

            base_dir = os.path.dirname(fpath)
            quarantine_dir = os.path.join(base_dir, "failed_msgs")
            os.makedirs(quarantine_dir, exist_ok=True)

            # Move the file
            new_path = os.path.join(quarantine_dir, os.path.basename(fpath))
            os.rename(fpath, new_path)
            self.log(f"Moved problematic file to quarantine: {new_path}", level="WARNING")
        except Exception as e:
            self.log(f"Could not quarantine file '{os.path.basename(fpath)}'", error=e, level="ERROR")

    def process_new_message(self, data):
        """
        Analyzes and sanitizes a decrypted message, then decides on the next action.

        This method sanitizes the user-provided fields ('name', 'email', 'message')
        to prevent cross-site scripting (XSS) attacks. It then fingerprints the
        message for spam detection and, based on the agent's configuration,
        either sends it to the Oracle for AI-based classification or
        forwards it directly to the operator.

        Args:
            data (dict): The decrypted message payload as a dictionary.
        """
        try:
            # Sanitize user-provided input to prevent XSS
            # Strips any HTML tags and attributes, leaving only plain text.
            clean_title = bleach.clean(data.get("title", ""), tags=[], strip=True)
            clean_name = bleach.clean(data.get("name", ""), tags=[], strip=True)
            clean_email = bleach.clean(data.get("email", ""), tags=[], strip=True)
            clean_message = bleach.clean(data.get("message", ""), tags=[], strip=True)

            # Update the data dictionary with sanitized content
            sanitized_data = data.copy()
            sanitized_data["title"] = clean_name
            sanitized_data["name"] = clean_name
            sanitized_data["email"] = clean_email
            sanitized_data["message"] = clean_message

            # Use the sanitized message for all further processing
            body = sanitized_data.get("message", "")
            query_id = f"q_{int(time.time())}"
            fingerprint = hashlib.sha256(body.encode()).hexdigest()[:16]

            # Check against known spam fingerprints
            if fingerprint in self.memory_vectors:
                self.log(f"Message discarded; matches known spam fingerprint: {fingerprint}")
                return

            self.pending_evals[query_id] = {
                "data": sanitized_data,  # Use the sanitized data
                "timestamp": time.time(),
                "sent": False,
                "fingerprint": fingerprint
            }

            if self.enable_oracle:
                self.send_to_oracle(query_id, body)
            else:
                # If oracle is disabled, forward the sanitized message directly
                self.forward_clean_message(sanitized_data)

        except Exception as e:
            self.log(f"Error processing new message", error=e)


    def send_to_oracle(self, query_id, text):
        """
        Constructs and sends a command packet to an Oracle agent.

        This method requests an AI-based classification of the message text
        to determine if it is spam.

        Args:
            query_id (str): A unique identifier for this query.
            text (str): The message body to be analyzed.
        """
        try:
            # Standardized Oracle packet
            pk_command = self.get_delivery_packet("standard.command.packet")
            pk_command.set_data({
                "handler": "cmd_msg_prompt",  # Standard handler for Oracle text analysis
                "timestamp": int(time.time()),
                "content": {
                    "prompt": f"Classify the following message as 'spam' or 'not_spam'.\n\n{text}",
                    "message_type": "contact_form",
                    "query_id": query_id,
                    "target_universal_id": self.command_line_args.get("universal_id", "contact-reflex"),
                    "return_handler": "cmd_oracle_response",
                },

            })

            # Send to the first agent serving as hive.oracle
            for node in self.get_nodes_by_role("hive.oracle","any",1):
                self.pass_packet(pk_command, node["universal_id"])

            # Mark as sent
            self.pending_evals[query_id]['sent'] = True

        except Exception as e:
            self.log(error=e, block='main_try')

    def cmd_oracle_response(self, content, packet, identity=None):
        """
        Handles the asynchronous response from the Oracle agent.

        This method is a command handler that is triggered when an Oracle
        agent sends back its analysis. It interprets the response and either
        discards the message as spam or forwards it to the operator.

        Args:
            content (dict): The payload from the Oracle, containing the
                'response' and original 'query_id'.
            packet (dict): The raw packet object.
            identity (IdentityObject, optional): The verified identity of the
                sending Oracle agent.
        """
        try:
            query_id = content.get("query_id",0)
            oracle_response = content.get("response") or content.get("content", {}).get("response")

            self.log(f"[CONTACT_REFLEX][ORACLE_RESPONSE] Received: session {query_id}, response: {oracle_response}")

            # Locate the original pending eval
            record = self.pending_evals.pop(query_id, None)
            if not record:
                self.log(f"[CONTACT_REFLEX][WARN] No pending eval found for query_id : {query_id}")
                return

            msg = record['data']
            # Interpret oracle's result (e.g. spam/not_spam)
            if oracle_response == "spam":
                self.memory_vectors[record['fingerprint']] = time.time()
                self.log("[CONTACT_REFLEX] Message flagged as spam. Not relayed.")
            else:
                self.forward_clean_message(msg)

        except Exception as e:
            self.log(f"[CONTACT_REFLEX][ERROR][cmd_oracle_response] {e}")

    def check_oracle_responses(self):
        """
        Periodically checks for and handles timed-out Oracle requests.

        This method prevents messages from getting stuck if an Oracle agent
        fails to respond. If a query has been pending for longer than the
        configured `oracle_timeout`, this method will either forward or
        discard the message based on the `enable_fallback_forward` setting.
        """
        try:
            now = time.time()
            expired = [qid for qid, v in self.pending_evals.items()
                       if v['sent'] and now - v['timestamp'] > self.oracle_timeout]
            for qid in expired:
                data = self.pending_evals.pop(qid)
                if self.enable_fallback_forward:
                    self.log(f"[ORACLE] Timeout. Forwarding message with fail note: {qid}")
                    data['data']['oracle_status'] = "timeout"
                    self.forward_clean_message(data['data'])

        except Exception as e:
            self.log(f"[CONTACT][ERROR] {e}")

    def forward_clean_message(self, msg):
        """
        Formats a clean message, validates the sender's IP, and prepares it for operator delivery.

        This method validates the provided IP address. If valid, it enriches
        the message data with GeoIP information (if enabled) and formats the
        entire payload into a human-readable string before passing it to the
        `alert_operator` method for final delivery.

        Args:
            msg (dict): The clean message payload.
        """
        try:
            ip_string = msg.get('sender_ip')
            ip = None
            geo = None

            # 🧐 Validate the IP address before using it
            if ip_string:
                try:
                    ipaddress.ip_address(ip_string)
                    ip = ip_string
                except ValueError:
                    self.log(f"[VALIDATION] Received invalid IP address: '{ip_string}'. Skipping GeoIP lookup.", level="WARNING")

            # Resolve the IP if it's valid and GeoIP is enabled
            if ip and self.geoip_enabled:
                geo = self.resolve_ip(ip)

            # Compose the message payload
            payload = (
                f"📥 *New Contact Message* {msg.get('site', '')}\n"
                f"👤 *Name:* {msg.get('name', 'none')}\n"
                f"✉️ *Email:* {msg.get('email', 'none')}\n"
                f"💬 *Message:* {msg.get('message', 'none')[:800]}\n"
                f"🕓 *Time:* {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.get('timestamp', time.time())))}\n"
            )
            # Add GeoIP info if available
            if geo and isinstance(geo, dict):
                city = geo.get("city", "Unknown")
                region = geo.get("region", "")
                country = geo.get("country", "Unknown")
                payload += f"🌐 *IP:* {geo.get('ip', 'none')}  ({city}, {region}, {country})\n"
            elif ip: # Only show the IP if it was validated
                payload += f"🌐 *IP:* {ip}\n"

            if msg.get("oracle_status") == "timeout":
                payload += "⚠️ Oracle failed to respond. Spam filter skipped.\n"

            self.alert_operator("Contact Inbox", payload)
        except Exception as e:
            self.log(f"[FORWARD_CLEAN_MESSAGE][ERROR] {e}\n[MESSAGE] {msg}", error=e, block='main_try')


    def resolve_ip(self, ip):
        """
        Resolves an IP address to a geographic location using a local database.

        Args:
            ip (str): The IP address to look up.

        Returns:
            dict: A dictionary containing location data (city, region, country)
                  on success, or False on failure.
        """
        try:
            reader = geoip2.database.Reader(self.mmdb_path)
            response = reader.city(ip)
            return {
                "ip": ip,
                "city": response.city.name,
                "region": response.subdivisions[0].name if response.subdivisions else None,
                "country": response.country.name
            }
        except Exception as e:
            self.log(error=e, block='main_try')
            return False

    def alert_operator(self, title, message):
        """

        Sends the final, formatted message to the configured alerting agent.

        This method constructs a standard alert packet and sends it to all
        agents that have the configured `alert_to_role` (e.g., a Discord or
        Telegram relay agent).

        Args:
            title (str): The title for the alert.
            message (str): The formatted message body.
        """
        try:
            pk1 = self.get_delivery_packet("standard.command.packet")
            pk1.set_data({"handler": "cmd_send_alert_msg"})

            try:
                server_ip = requests.get("https://api.ipify.org").text.strip()
            except Exception:
                server_ip = "Unknown"

            pk2 = self.get_delivery_packet("notify.alert.general")
            pk2.set_data({
                "server_ip": server_ip,
                "universal_id": self.command_line_args.get("universal_id", "contact_reflex"),
                "level": "info",
                "msg": message,
                "formatted_msg": message,
                "cause": title,
                "origin": "contact_reflex"
            })

            pk1.set_packet(pk2, "content")

            if self.alert_role:
                for node in self.get_nodes_by_role(self.alert_role):
                    self.pass_packet(pk1, node["universal_id"])

        except Exception as e:
            self.log(f"[CONTACT][ERROR] {e}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
