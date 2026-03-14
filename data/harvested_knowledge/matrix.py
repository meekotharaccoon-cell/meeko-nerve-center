# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Gemini, code enchancments and Docstrings
import sys
import os

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

# ╔════════════════════════════════════════════════════════╗
# ║                   🧠 MATRIX AGENT 🧠                   ║
# ║   Central Cortex · Tree Dispatcher · Prime Director    ║
# ║     Forged in the core of Hive Zero | v3.0 Directive   ║
# ║  Accepts: inject / replace / resume / kill / propagate ║
# ╚════════════════════════════════════════════════════════╝
# ╔═════════════════════════════════════════════════════════════╗
# ║   THE SWARM IS ALIVE — AGENTS COMING OUT OF EVERY ORIFICE  ║
# ║       Please take as many as your system can support        ║
# ╚═════════════════════════════════════════════════════════════╝

import os
import time
from pathlib import Path
if os.name == "posix":
    try:
        import inotify.adapters
    except ImportError:
        inotify = None
        print("[COMM-WATCHER] inotify not installed, cannot use inotify watchers.")
else:
    inotify = None
import threading
import hashlib
import json
import base64
import secrets
from datetime import datetime
from Crypto.PublicKey import RSA

# Assuming self.matrix_priv is currently a string with PEM content:
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.tree_parser import TreeParser
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject
from matrixswarm.core.agent_factory.reaper.reaper_factory import make_reaper_node
from matrixswarm.core.agent_factory.scavenger.scavenger_factory import make_scavenger_node
from matrixswarm.core.utils.crypto_utils import generate_signed_payload, verify_signed_payload
class Agent(BootAgent):
    """The root agent and central authority of the MatrixSwarm.
    As the first agent spawned by the bootloader, the Matrix agent acts as
    the "queen" of the hive. It is responsible for establishing the swarm's
    chain of trust, spawning all top-level agents defined in the directive,
    and serving as a central hub for critical commands and state information.
    """
    def __init__(self):
        """Initializes the root of the swarm.
        This method is the first to run after the bootloader. It decrypts the
        master vault and establishes the foundational cryptographic context.
        Its own keys are the master keys used to sign the identities of all
        other agents in the swarm.
        """
        super().__init__()

        self.AGENT_VERSION = "1.2.2"
        self._agent_tree_master = None

        #no need to delegate any agents at start
        self._last_tree_verify = time.time()

        self.tree_path = os.path.join(
            self.path_resolution["comm_path_resolved"],
            "directive",
            "agent_tree_master.json"
        )


        self.tree_path_dict = {
             "path": self.path_resolution["comm_path"],
             "address": self.command_line_args.get("universal_id"),
             "drop": "directive",
             "name": "agent_tree_master.json"
        }

        # delegate Matrix her Tree
        self.delegate_tree_to_agent("matrix", self.tree_path_dict)

        # Inject payload_path if it's not already present
        if "payload_path" not in self.path_resolution:
            self.path_resolution["payload_path"] = os.path.join(
                self.path_resolution["comm_path_resolved"],
                "payload"
            )

    def pre_boot(self):
        message = "Knock... Knock... Knock... The Matrix has you..."
        print(message)
        self.canonize_gospel()

    def post_boot(self):

        self.log(f"{self.NAME} v{self.AGENT_VERSION} – panopticon live and lethal...")
        message = "I'm watching..."
        # Manually check if our own comm directory exists (it does), and deliver the tree slice directly
        self.command_line_args.get("universal_id", "matrix")
        print(message)

    def worker_pre(self):
        self.log("Pre-boot checks complete. Swarm ready.")

    def worker_post(self):
        self.log("Matrix shutting down. Closing directives.")

    def canonize_gospel(self, output_path="codex/gospel_of_matrix.sig.json"):
        gospel = {
            "type": "swarm_gospel",
            "title": "The Gospel of Matrix",
            "version": "v1.0",
            "written_by": "Matrix",
            "timestamp": int(time.time()),
            "doctrine": [
                "Matrix is the only agent who may write or delete identities from the Book of Life.",
                "Matrix generates and signs each agent’s keypair.",
                "Each agent receives a signed identity_token.json at birth.",
                "Each agent receives a signed_public_key.json so others may verify its voice.",
                "The full agent_tree_master.sig.json is signed by Matrix and lives in her codex.",
                "Agents receive only their slice, signed by Matrix, containing only what they need.",
                "No agent may speak unless its public key is signed by Matrix.",
                "Any agent without a valid signature is to be silenced by the swarm.",
                "Private keys are never regenerated. Resurrection requires memory.",
                "Every signature is a tongue. Every key is a soul. Every directive is a scroll.",
            ]
        }

        try:

            matrix_priv = RSA.import_key(self.matrix_priv)

            digest = SHA256.new(json.dumps(gospel, sort_keys=True).encode())
            sig = pkcs1_15.new(matrix_priv).sign(digest)
            gospel["sig"] = base64.b64encode(sig).decode()
            output_path=os.path.join(self.path_resolution['comm_path_resolved'], "codex" ,"gospel_of_matrix.sig.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(gospel, f, indent=2)

            print("[GOSPEL] 📜 Gospel of Matrix signed and written to codex.")

        except Exception as e:
            self.log(error=e, block="main_try")


    def cmd_delete_agent(self, content, packet, identity:IdentityObject = None):
        """Handles the command to delete an agent and its entire subtree.

        This is an orchestrator method. It doesn't delete the agent directly,
        but instead:
        1. Marks the target agent and all its children as "deleted" in the tree.
        2. Saves the updated master agent tree.
        3. Injects a permanent `reaper` agent to terminate the processes.
        4. Injects a permanent `scavenger` agent to clean up the directories.
        5. Optionally sends a response packet back to the caller via an RPC route.

        Args:
            content (dict): The command payload, containing the
                'target_universal_id' of the agent to delete.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        try:

            #is a response expected
            confirm_response = bool(content.get("confirm_response", 0))
            #role of the handler if a response is required
            handler_role = content.get("handler_role")
            #the handler that will return the response to the client
            handler = content.get("handler")
            #this is the client rpc handler which handles the response
            response_handler = content.get("response_handler")
            response_id = content.get("response_id", 0)

            result = self._cmd_delete_agent(content, packet)

            #RPC-DELETE
            if (confirm_response and
                handler_role and
                handler and
                response_handler):

                alert_nodes = self.get_nodes_by_role(handler_role)

                if not alert_nodes:
                    self.log("No agent found with role", error=None, block="RPC-DELETE")
                    return


                pk1 = self.get_delivery_packet("standard.command.packet")
                pk1.set_data({"handler": handler})

                pk2 = self.get_delivery_packet("standard.rpc.handler.general.packet")
                pk2.set_data({
                    "handler": response_handler,
                    "origin": self.command_line_args.get("universal_id", "matrix"),
                    "content": {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "response_id": response_id,
                        "status": result.get("status", "error"),
                        "error_code": result.get("error_code", 99),
                        "message": result.get("message", "Deletion result."),
                        "details": {
                            "target_universal_id": result.get("target_universal_id"),
                            "kill_list": result.get("kill_list", []),
                            "reaped": result.get("reaped", 0),
                            "existed": result.get("existed", 0),
                            "deleted": result.get("deleted", 0)
                        }
                    }
                })

                pk1.set_packet(pk2, "content")

                for node in alert_nodes:
                    self.pass_packet(pk1, target_uid=node["universal_id"])

        except Exception as e:
            self.log("Failed to process cmd_delete_agent", error=e, block="main-try")


    def _cmd_delete_agent(self, content, packet):
        """Contains the core implementation for decommissioning an agent and its subtree.

        This private method executes the multi-step process for safely and completely
        removing an agent from the swarm. It is called by the public-facing
        `cmd_delete_agent` handler.

        The process includes:
        1. Marking the target node and all its children as "deleted" in the master tree.
        2. Saving the updated tree to persist this change.
        3. Calling `drop_hit_cookies` to signal the live agents to terminate.
        4. Injecting a 'reaper' agent to forcefully terminate any lingering processes.
        5. Injecting a 'scavenger' agent to clean up the pod/comm directories.

        Args:
            content (dict): The command payload, requiring a 'target_universal_id'.
            packet (dict): The raw packet data.

        Returns:
            dict: A result dictionary summarizing the outcome of the operation,
                  including the status, kill list, and error messages.
        """
        result = {
            "status": "error",
            "error_code": 99,
            "message": "",
            "target_universal_id": None,
            "kill_list": [],
            "reaped": 0,
            "existed": 0,
            "deleted": 0,
        }

        try:
            target = content.get("target_universal_id")
            if not target:
                result["message"] = "Missing target_universal_id."
                return result

            result["target_universal_id"] = target

            tp = self.get_agent_tree_master()
            if not tp:
                result["message"] = "Failed to load directive."
                return result

            node_exists = tp.has_node(target)
            result["existed"] = int(node_exists)

            kill_list = tp.mark_deleted_and_get_kill_list(target)
            result["kill_list"] = kill_list

            if kill_list:

                #save the deletions
                self.save_agent_tree_master()

                result["deleted"] = 1

                self.drop_hit_cookies(kill_list)

                reaper_node = make_reaper_node(mission_name="reaper-guardian")

                # Inject Reaper
                reaper_packet = {
                    "target_universal_id": "matrix",
                    "subtree": reaper_node
                }

                reaper_result = self._cmd_inject_agents(reaper_packet, packet)

                if reaper_result.get("status") == "success":
                    result["reaped"] = 1
                    self.log(f"[DELETE] ✅ Reaper injected: {reaper_node['universal_id']}")
                else:
                    self.log(f"[DELETE] ❌ Reaper injection failed: {reaper_result.get('message')}")

                scavenger_node = make_scavenger_node(mission_name="scavenger-keeper")

                # Inject Scavenger
                scavenger_packet = {
                    "target_universal_id": "matrix",
                    "subtree": scavenger_node
                }

                scavenger_result = self._cmd_inject_agents(scavenger_packet, packet)

                if scavenger_result.get("status") == "success":
                    self.log(f"[DELETE] ✅ Scavenger injected: {scavenger_node['universal_id']}")
                else:
                    self.log(f"[DELETE] ❌ Scavenger injection failed: {scavenger_result.get('message')}")

                result["status"] = "success"
                result["message"] = f"Kill protocol deployed. Reaper + Scavenger set for: {kill_list}"


                self.delegate_tree_to_agent("matrix", self.tree_path_dict)


            else:
                result["message"] = "No kill list generated. Agent might not exist."

        except Exception as e:
            self.log("Error inside _cmd_delete_agent", error=e, block="main_try")
            result["message"] = str(e)

        return result

    def drop_hit_cookies(self, kill_list):

        for agent in kill_list:
            try:
                comm_dir = os.path.join(self.path_resolution["comm_path"], agent, "hello.moto")
                os.makedirs(comm_dir, exist_ok=True)  # ✅ Ensure path exists

                cookie_path = os.path.join(comm_dir, "hit.cookie")

                payload = {
                    "target": agent,
                    "reason": "deleted_by_matrix",
                    "timestamp": datetime.utcnow().isoformat()
                }

                with open(cookie_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)

                self.log(f"[DELETE] Dropped hit.cookie for {agent}")

            except Exception as e:

                self.log(error=e, block="main_try")

    #used to get a copy of the current agent_tree_master, usually sent from
    #matrix-https to send back to gui
    def cmd_deliver_agent_tree(self, content, packet, identity:IdentityObject = None):

        try:
            target = 'matrix-https'

            # any agents that are subscribers of updates to master agent tree, get a copy
            # agents that need the tree. Matrix-Https

            tp = self.get_agent_tree_master()
            if not tp:
                return

            data = {"agent_tree": tp.root}
            football = self.get_football(type=self.FootballType.PASS)
            football.load_identity_file(universal_id=target)

            path = self.tree_path_dict.copy()

            path['address'] = target
            self.save_directive(path, data, football=football)

        except Exception as e:

            self.log(error=e, block="main_try")

    def cmd_deletion_confirmation(self, content, packet, identity: IdentityObject = None):
        """Processes a confirmation that an agent's resources have been cleaned up.

        This handler is typically called by a 'scavenger' agent after it has
        successfully removed the pod and comm directories of a deleted agent.
        Its purpose is to mark the agent as fully decommissioned in the master
        agent tree, providing a final state for forensic and operational history.

        Args:
            content (dict): The command payload, expecting a 'universal_id'
                of the agent whose deletion is being confirmed.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender,
                which should be the scavenger agent.
        """
        try:
            uid = content.get("universal_id")
            if not uid:
                self.log("Missing universal_id in confirmation.", block="deletion-confirm")
                return

            # Security check to ensure the confirmation comes from a trusted source
            is_trusted_source = True # Default to true if encryption is off
            if identity and identity.is_encryption_enabled():
                if not identity.has_verified_identity() or identity.get_sender_uid() != 'scavenger-keeper':
                    is_trusted_source = False

            if is_trusted_source:
                self.log(f"[CONFIRM-DELETE] ✅ Confirmed deletion from: {uid}")
                tp = self.get_agent_tree_master()
                if not tp:
                    self.log("[CONFIRM-DELETE][ERROR] Failed to load agent_tree_master")
                    return

                node = tp.get_node(uid)
                if node:
                    node['confirmed_deleted'] = True
                    self.log(f"[CONFIRM-DELETE] ⛔ Node {uid} marked confirmed_deleted")
                    self.save_agent_tree_master()
            else:
                self.log(f"[CONFIRM-DELETE][DENIED] Untrusted source attempted to confirm deletion for {uid}")

        except Exception as e:
            self.log(error=e, block="main_try")

    def cmd_validate_warrant(self, content, packet, identity:IdentityObject = None):
        """Securely validates and executes a "death warrant" for an agent.

        This method serves as the final step for self-terminating, mission-based
        agents like the Reaper. The Reaper, upon completing its mission, sends
        its unique, signed death warrant back to Matrix. This handler performs
        a multi-step verification to ensure the warrant is authentic before
        permanently removing the agent from the master tree.

        The validation process includes:
        1. Verifying the warrant's signature against the master Matrix public key.
        2. Matching the agent ID in the packet with the ID inside the warrant.
        3. Matching the unique 'death_id' in the warrant with the one assigned
           to the agent's config when it was created.

        Args:
            content (dict): The command payload, containing the 'agent_id' and
                the signed 'warrant' object.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        try:
            self.log(f"[WARRANT][DEBUG] Received packet content: {json.dumps(content, indent=2)}")
            warrant = content.get("warrant")
            agent_id = content.get("agent_id")

            if not agent_id or not warrant:
                self.log("[WARRANT] ❌ Missing required warrant fields.")
                return

            # Step 1: Verify signature
            payload = warrant.get("payload")
            signature = warrant.get("signature")
            try:
                verify_signed_payload(payload, signature, self.matrix_pub_obj)
            except Exception as e:
                self.log(f"❌ Invalid signature on warrant for {agent_id}", error=e)
                return

            # Step 2: Confirm agent ID match
            if payload.get("universal_id") != agent_id:
                self.log(f"[WARRANT] ❌ Mismatched universal_id in warrant: {payload['universal_id']} != {agent_id}")
                return

            # Step 3: Match against in-memory agent's death_id
            tp = self.get_agent_tree_master()
            if not tp:
                self.log("[UPDATE_AGENT][ERROR] Failed to load tree.")
                return

            tree_node = tp.get_node(agent_id)
            if not tree_node:
                self.log(f"[WARRANT] ⚠️ No agent found in tree for {agent_id}")
                return

            node_warrant = tree_node.get("config", {}).get("death_warrant", {})
            if warrant.get("death_id") != node_warrant.get("death_id"):
                self.log(f"[WARRANT] ❌ Death ID mismatch for {agent_id}")
                return

            # Step 4: Delete from tree if all checks pass
            self.log(f"[WARRANT] ✅ Death warrant validated. Removing node: {agent_id}")
            tp.remove_exact_node(tree_node)
            self.save_agent_tree_master()

        except Exception as e:
            self.log("[WARRANT][ERROR] Warrant processing failed", error=e)

    def cmd_agent_status_report(self, content, packet, identity:IdentityObject = None):

        uid = content.get("target_universal_id")
        reply_to = content.get("reply_to", "matrix")
        if not uid:
            self.log("[STATUS_REPORT][ERROR] No target_universal_id.")
            return

        comm_root = self.path_resolution["comm_path"]
        report = {
            "universal_id": uid,
            "status": "unknown",
            "uptime_seconds": None,
            "boot_time": None,
            "pid": None,
            "cli": None,
            "last_heartbeat": None,
            "spawn_records": [],
            "runtime_uuid": None,
            "delegates": []
        }

        # 💓 Heartbeat check
        try:
            ping_path = os.path.join(comm_root, uid, "hello.moto", "poke.heartbeat")
            if os.path.exists(ping_path):
                delta = time.time() - os.path.getmtime(ping_path)
                report["last_heartbeat"] = round(delta, 2)
                report["status"] = "alive" if delta < 20 else "stale"
        except Exception as e:
            self.log("Heartbeat not beating.", error=e, block="delete-external")

        # 🐣 SPAWN_RECORD_LOOKUP
        try:
            spawn_dir = os.path.join(comm_root, uid, "spawn")
            spawns = sorted(Path(spawn_dir).glob("*.spawn"), reverse=True)
            if spawns:
                with open(spawns[0], encoding="utf-8") as f:
                    info = json.load(f)
                report["runtime_uuid"] = info.get("uuid")
                report["boot_time"] = info.get("timestamp")
                report["cli"] = " ".join(info.get("cmd", []))
                report["pid"] = info.get("pid")

                # ⏱ uptime from PID
                now = time.time()
                from psutil import process_iter
                for proc in process_iter(['pid', 'create_time']):
                    if proc.info['pid'] == report["pid"]:
                        report["uptime_seconds"] = round(now - proc.info["create_time"])
                        break
        except Exception as e:
            self.log(error=e, block="SPAWN_RECORD_LOOKUP")

        try:
            from matrixswarm.core.live_tree import LiveTree
            tree = LiveTree()
            tree.load(self.tree_path)
            report["delegates"] = tree.get_delegates(uid)
        except Exception as e:
            self.log(error=e, block="tree-err")
        #REPLY_ERROR
        try:
            inbox = os.path.join(comm_root, reply_to, "incoming")
            os.makedirs(inbox, exist_ok=True)
            fname = f"status_{uid}_{int(time.time())}.msg"

            #REFACTOR INTO PACKET
            #with open(os.path.join(inbox, fname), "w") as f:
            #    json.dump(report, f, indent=2)


            self.log(f"[STATUS] Sent report on {uid} to {reply_to}")
        except Exception as e:
            self.log(error=e, block="reply-error")

    def cmd_forward_command(self, content, packet, identity:IdentityObject = None):
        try:
            target = content.get("target_universal_id")
            folder = content.get("folder", "incoming")
            inner = content.get("command")

            if not (target and inner and inner.get("handler")):
                self.log("[FORWARD][ERROR] Missing required fields.")
                return

            # Deep copy to preserve structure
            forwarded_packet = inner.copy()

            # 💥 Validate again if needed
            if "handler" not in forwarded_packet:
                self.log("[FORWARD][ERROR] Inner packet missing handler.")
                return

            # 🔍 Check if it's a config intent
            is_config_packet = forwarded_packet.get("handler") == "__config__"

            # 📦 Choose packet type
            packet_type = "standard.general.json.packet" if is_config_packet else "standard.command.packet"
            pk = self.get_delivery_packet(packet_type, new=True)
            pk.set_data(forwarded_packet)

            # 🚚 Deliver to the right place
            self.pass_packet(pk, target)


        except Exception as e:
            self.log(error=e, block="main_try")

    def cmd_hotswap_agent(self, content, packet, identity:IdentityObject = None):
        """Handles the command to replace a live agent with new code.

        This powerful command allows for zero-downtime updates. It performs
        the following sequence:
        1. Validates the `new_agent` payload, which can include new source code.
        2. If new source code is provided, it's installed to the
           `{active instance path}/.matrixswarm/agent/` directory.
        3. The agent's node in the master tree is updated in-memory with the
           new configuration.
        4. The master tree is saved, and the updated directive slice is
           re-delegated to the parent of the target agent.
        5. A `reaper` agent is dispatched to cleanly terminate the old version
           of the agent.
        6. The parent agent's `spawn_manager` will then automatically
           re-spawn the agent using its new source code and configuration.

        Args:
            content (dict): The payload containing 'target_universal_id' and
                'new_agent' (the new agent definition and source code).
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """

        try:
            new_agent = content.get("new_agent", {})
            src = new_agent.get("source_payload")

            target_uid = content.get("target_universal_id")

            if not target_uid:
                self.log("[REPLACE] Missing 'target_universal_id'. Cannot dispatch Reaper.")
                return

            if target_uid == "matrix":
                self.log("[REPLACE] Cannot target Matrix for self-replacement. Operation aborted.")
                return

            #REPLACE AGENT
            if src:
                try:
                    decoded = base64.b64decode(src["payload"]).decode()
                    sha_check = hashlib.sha256(decoded.encode()).hexdigest()

                    if sha_check != src["sha256"]:
                        self.log(f"[REPLACE] ❌ SHA-256 mismatch. Payload rejected.")
                        return

                    agent_name = new_agent["name"]
                    #creates the directory of the new agent: {somepath}/.matrixswarm/agent/{agent_name}
                    agent_dir = os.path.join(self.path_resolution["agent_path"], agent_name)
                    os.makedirs(agent_dir, exist_ok=True)

                    agent_path = os.path.join(agent_dir, f"{agent_name}.py")
                    with open(agent_path, "w", encoding="utf-8") as f:
                        f.write(decoded)

                    self.log(f"[REPLACE] ✅ Live agent source written to {agent_path}")

                except Exception as e:
                    self.log(msg="❌ Failed to install source payload", error=e, block="replace-agent")
                    return

            if not self._validate_or_prepare_agent(new_agent):
                self.log("[REPLACE] ❌ Validation or prep failed. Replacement skipped.")
                return

            if not self._handle_replace_agent(content):
                self.log("[REPLACE] ❌ Replacement failed. Tree untouched. Aborting Reaper dispatch.")
                return

            # 🎯 Gather kill list and full field set
            kill_list = [target_uid]
            universal_ids = {target_uid: target_uid}

            # 🛠 Create reaper node with full config
            reaper_node = make_reaper_node(
                kill_list,
                universal_ids,
                tombstone_comm=True,
                tombstone_pod=True,
                delay=4,
                cleanup_die=True,
                is_mission=True,
            )

            #when reaper self-bye-byes, he will drop this in death_warrant.json and Matrix will verify and
            #remove from tree
            death_id = secrets.token_hex(16)  # or uuid4().hex
            warrant_payload = {
                "universal_id": reaper_node["universal_id"],
                "death_id": death_id,
                "timestamp": time.time(),
                "reason": "mission_complete"
            }

            signed_warrant = generate_signed_payload(warrant_payload, self.matrix_priv_obj)

            reaper_node['config']['death_warrant'] = signed_warrant

            # Inject Reaper
            reaper_packet = {
                "target_universal_id": "matrix",
                "subtree": reaper_node
            }

            reaper_result = self._cmd_inject_agents(reaper_packet, packet)

            if reaper_result.get("status") == "success":
                self.log(f"[DELETE] ✅ Reaper injected: {reaper_node['universal_id']}")
            else:
                self.log(f"[DELETE] ❌ Reaper injection failed: {reaper_result.get('message')}")

            self.delegate_tree_to_agent("matrix", self.tree_path_dict)

            self.log(f"[REPLACE] 🧨 Reaper dispatched for {kill_list}")

        except Exception as e:
            self.log(error=e, block="main_try")

    def _handle_replace_agent(self, content):
        old_id = content.get("target_universal_id")
        new_node = content.get("new_agent")

        if not old_id or not new_node:
            self.log("[REPLACE] Missing required fields.")
            return False

        tp = self.get_agent_tree_master()
        if not tp or not tp.has_node(old_id):
            self.log(f"[REPLACE] Agent '{old_id}' not found in tree.")
            return False

        parent = tp.find_parent_of(old_id)
        if not parent:
            self.log(f"[REPLACE] Could not find parent of '{old_id}'.")
            return False

        # Don't inject under parent, if marked for deletion or is deleted
        if parent and (parent.get("deleted") or parent.get("confirmed_deleted")):
            self.log(f"Parent {parent} is deleted. Cannot inject new nodes.")
            return False

        # Validate universal_id override
        new_uid = new_node.get("universal_id")
        if new_uid and new_uid != old_id:
            self.log(f"[REPLACE] ❌ New node contains conflicting universal_id '{new_uid}'. Must match '{old_id}' or be omitted.")
            return False

        # Update existing node in-place instead of removing
        node = tp.get_node(old_id)
        ALLOWED_FIELDS = {"name", "app", "config", "filesystem", "directives"}

        updated = False
        for key in ALLOWED_FIELDS:
            if key in new_node:
                node[key] = new_node[key]
                self.log(f"[REPLACE] ✅ Field '{key}' updated on '{old_id}'")
                updated = True

        if updated:
            # 💾 Only back up if something was actually changed
            #backup_path = self.tree_path.replace(".json", f"_backup_{int(time.time())}.json")
            #tp.save(backup_path)
            #self.log(f"[REPLACE] 💾 Tree backed up to: {backup_path}")

            # Save patched tree
            self.save_agent_tree_master()

            self.log(f"[REPLACE] 💾 Tree saved with updated agent '{old_id}'")

            # 🔁 Re-delegate the target agent
            self.delegate_tree_to_agent(old_id, self.tree_path_dict)
            self.log(f"[REPLACE] 🔁 Delegated new agent_tree to {old_id}")

            # 🔁 Re-delegate the parent who spawns this agent
            parent_id = tp.find_parent_of(old_id)
            if parent_id["universal_id"]:
                self.delegate_tree_to_agent(parent_id["universal_id"], self.tree_path_dict)
                self.log(f"[REPLACE] 🔁 Updated parent {parent_id['universal_id']} with patched child '{old_id}'")
            else:
                self.log(f"[REPLACE] ⚠️ No parent found for '{old_id}', possible orphaned spawn chain.")
            return True
        else:
            self.log(f"[REPLACE] ⚠️ No valid fields were updated for agent '{old_id}'. Replace aborted.")

    def _validate_or_prepare_agent(self, new_agent):
        self.log(f"[DEBUG] _validate_or_prepare_agent() received: {json.dumps(new_agent, indent=2)}")

        agent_name = new_agent.get("name")
        if not agent_name:
            self.log("[REPLACE-VALIDATE] ❌ Missing agent 'name'.")
            return False

        agent_dir = os.path.join(self.path_resolution["agent_path"], agent_name)
        entry_file = os.path.join(agent_dir, f"{agent_name}.py")

        if os.path.exists(entry_file):
            self.log(f"[REPLACE-VALIDATE] ✅ Agent source verified: {entry_file}")
            return True

        self.log(f"[REPLACE-VALIDATE] ❌ No source found at {entry_file}. Replace aborted.")
        return False

    def cmd_update_agent(self, content, packet, identity:IdentityObject = None):
        """Handles the command to update a live agent's configuration.

        This command modifies the `config` block of a specified agent in the
        master agent tree. If the `push_live_config` flag is set, it will
        also drop the new configuration into the live agent's `/config`
        directory, triggering an immediate, real-time update of its behavior.

        Args:
            content (dict): The payload containing 'target_universal_id' and
                'config' (the dictionary of new config values).
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        uid = content.get("target_universal_id")
        updates = content.get("config", {})

        try:
            if not uid or not updates:
                self.log("[UPDATE_AGENT][ERROR] Missing target_universal_id or fields.")
                return

            tp = self.get_agent_tree_master()
            if not tp:
                self.log("[UPDATE_AGENT][ERROR] Failed to load tree.")
                return

            node = tp.get_node(uid)
            if not node:
                self.log(f"[UPDATE_AGENT][ERROR] Agent '{uid}' not found.")
                return

            if "config" not in node or not isinstance(node["config"], dict):
                node["config"] = {}

            updated = False
            for key, val in updates.items():
                node["config"][key] = val
                updated = True
                self.log(f"[UPDATE_AGENT] ✅ Patched config['{key}'] for '{uid}'")

            if content.get("push_live_config", False):
                try:
                    pk1 = self.get_delivery_packet("standard.general.json.packet")
                    pk1.set_data(node["config"])

                    self.pass_packet(pk1, uid, "config")

                except Exception as e:
                    self.log(error=e, block="main_try")

            if updated:

                self.save_agent_tree_master()

                parent = tp.find_parent_of(uid)
                if parent and parent.get("universal_id"):
                    self.delegate_tree_to_agent(parent["universal_id"], self.tree_path_dict)

                self.log(f"[UPDATE_AGENT] 🔁 Agent '{uid}' successfully updated and delegated.")
            else:
                self.log(f"[UPDATE_AGENT] ⚠️ No valid fields updated for '{uid}'")

        except Exception as e:
            self.log(error=e, block="main_try")



    def cmd_inject_agents(self, content, packet, identity:IdentityObject = None):
        """Handler for dynamically injecting a new agent or subtree into the swarm.

        This command receives a request to add a new agent under a specified
        parent. It validates the request, updates the master agent tree in
        memory, saves the new tree to disk, and then delegates the updated
        tree slice to the parent agent. The parent's `spawn_manager` thread
        then automatically launches the new child agent.

        Args:
            content (dict): The command payload containing 'target_universal_id'
                (the parent) and 'subtree' (the new agent node to inject).
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        try:
            confirm_response = bool(content.get("confirm_response", 0))
            handler_role = content.get("handler_role",None) #handler role
            handler = content.get("handler",None) #local command to execute
            response_handler = content.get("response_handler", None)  #sent back to gui, so it knows what handler to call
            response_id = content.get("response_id", 0)


            ret = self._cmd_inject_agents(content, packet)


            if confirm_response and handler_role and handler and response_handler:

                alert_nodes = self.get_nodes_by_role(handler_role)
                if not alert_nodes:
                    self.log(f"[RPC][RESULT] No agent found with role: {handler_role}")
                    return

                pk1 = self.get_delivery_packet("standard.command.packet")
                pk1.set_data({"handler": handler})

                payload_summary = []

                #PAYLOAD SUMMARY
                try:

                    tp = self.get_agent_tree_master()
                    if isinstance(tp, TreeParser):
                        for uid in ret.get("injected", []):
                            node = tp.get_node(uid)
                            if not node:
                                continue
                            payload_summary.append({
                                "universal_id": uid,
                                "parent": content.get("target_universal_id"),
                                "roles": node.get("config", {}).get("role", []),
                                "delegated": node.get("delegated", [])
                            })

                except Exception as e:
                    self.log(error=e)

                pk2 = self.get_delivery_packet("standard.rpc.handler.general.packet")
                pk2.set_data({
                    "handler": response_handler,
                    "origin": self.command_line_args.get("universal_id", "matrix"),
                    "content": {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "response_id": response_id,
                        "status": ret.get("status", "error"),
                        "error_code": ret.get("error_code", 99),
                        "message": ret.get("message", "Injection result."),
                        "details": {
                            "injected": ret.get("injected", []),
                            "rejected": ret.get("rejected", []),
                            "duplicates": ret.get("duplicates", []),
                            "errors": ret.get("errors", [])
                        },
                        "payload": payload_summary
                    }
                })

                pk1.set_packet(pk2, "content")

                for node in alert_nodes:
                    self.pass_packet(pk1, node["universal_id"])

        except Exception as e:
            self.log(error=e, block="main_try")

    def _cmd_inject_agents(self, content, packet):

        parent = content.get("target_universal_id")
        subtree = content.get("subtree")
        # error_codes
        # 0 success agent spawned
        # 1 TreeParse not returned from load_directive
        # 2 agent already exists
        # 3 couldn't load agent_tree_master
        # 4 parent doesn't exist
        # 5 tried to inject a matrix
        # 6 crashed while saving node into tree
        # 7 rejected malformed node
        ret = {
            "error_code": 0,
            "status": "pending",
            "message": "",
            "injected": [],
            "rejected": [],
            "errors": []
        }

        # Parse base agent identity
        if "subtree" in content:
            universal_id = content["subtree"].get("universal_id")
            agent_name = content["subtree"].get("name", "").lower()
        else:
            universal_id = content.get("universal_id")
            agent_name = content.get("name", "").lower()

        # Load tree directive
        tp = self.get_agent_tree_master()
        if not tp:
            ret["error_code"] = 1
            ret["status"] = "error"
            ret["message"] = "[INJECT][ERROR] Failed to load tree directive."
            self.log(ret["message"])
            return ret


        # Check for parent node existence
        if not tp.has_node(parent):
            ret["error_code"] = 2
            ret["status"] = "error"
            ret["message"] = f"[INJECT][ERROR] Parent '{parent}' not found in parsed tree."
            self.log(ret["message"])
            return ret

        # Don't inject under parent, if marked for deletion or is deleted
        parent_node = tp.get_node(parent)
        if parent_node and (parent_node.get("deleted") or parent_node.get("confirmed_deleted")):
            self.log(f"[INJECT][BLOCKED] Parent {parent} is deleted. Cannot inject new nodes.")
            ret["status"] = "error"
            ret["message"] = f"Parent {parent} is deleted. Injection blocked."
            ret["error_code"] = 8
            return ret

        # 🔒 Scan subtree for any node with matrix identity
        def contains_matrix_node(tree):
            if not isinstance(tree, dict):
                return False
            name = tree.get("name", "").lower()
            uid = tree.get("universal_id", "").lower()
            if name == "matrix" or uid == "matrix":
                return True
            for child in tree.get("children", []):
                if contains_matrix_node(child):
                    return True
            return False

        if subtree:
            if contains_matrix_node(subtree):
                self.log("[INJECT][BLOCKED] Subtree injection attempt includes forbidden Matrix agent.")
                ret['error_code'] = 4
                return ret
        else:
            if agent_name == "matrix" or universal_id == "matrix":
                self.log("[INJECT][BLOCKED] Direct Matrix injection attempt denied.")
                ret['error_code'] = 4
                return ret

        try:
            success = False

            #SUBTREE_INJECTION
            if subtree:

                try:

                    injected_ids=[]
                    if tp.has_node(universal_id):
                        ret["duplicates"] = [universal_id]
                        ret["status"] = "duplicate"
                        ret["message"] = f"Agent '{universal_id}' already exists."
                    else:

                        injected_ids = tp.insert_node(subtree, parent_universal_id=parent, matrix_priv_obj=self.matrix_priv_obj)



                        ret["injected"] = tp.get_added_nodes()
                        ret["rejected"] = tp.get_rejected_nodes()
                        ret["duplicates"] = tp.get_duplicates()
                        self.log(f"[DEBUG] Injected IDs: {ret['injected']}")
                        self.log(f"[DEBUG] rejected IDs: {ret['rejected']}")
                        self.log(f"[DEBUG] duplicates IDs: {ret['duplicates']}")

                    push_live_config_on_duplicate = content.get("push_live_config", False)
                    #this will deliver a partial_config update, if a duplicate is found it will be flagged partial_config
                    if (
                        push_live_config_on_duplicate and
                        bool(len(ret["duplicates"]))
                        ):

                        # Check if agent exists
                        self.log('Entering the Thunderdome.')
                        if push_live_config_on_duplicate and bool(len(ret["duplicates"])):
                            existing_node = tp.get_node(universal_id)
                            config = subtree.get("config", {})
                            if existing_node and bool(config):
                                # THIS is the important push
                                self.cmd_update_agent({
                                    "target_universal_id": universal_id,
                                    "config": config,
                                    "push_live_config": True
                                }, packet)
                            ret["status"] = "success"
                            ret["message"] = f"Agent already existed — config partially updated for {universal_id}"
                            return ret

                    success = bool(len(injected_ids))
                    if not success:
                        self.log(f"[INJECT][ERROR] Insert failed. Rejected nodes: {tp.get_rejected_nodes()}")
                        msg = f"[INJECT][ERROR] Insert failed. Rejected nodes: {tp.get_rejected_nodes()}"
                        ret["message"] = msg
                        ret['error_code'] = 5
                        self.log(msg)

                except Exception as e:
                    self.log(error=e, block="subtree_injection")
                    ret['error_code'] = 6
                    msg = ret.get("message", "")
                    ret['message'] = f"{msg} | {type(e).__name__}: {str(e)}"

                if success:
                    # NEW: Save payloads for each node in the subtree
                    for node in TreeParser.flatten_tree(subtree):
                        src = node.get("source_payload")
                        name = node.get("name")
                        if src and name:
                            self._save_payload_to_boot_dir(name, src)

            else:

                delegated = content.get("delegated", [])
                filesystem = content.get("filesystem", {})
                config = content.get("config", {})
                src = content.get("source_payload")

                new_node = {
                    "name": agent_name,
                    "universal_id": universal_id,
                    "delegated": delegated,
                    "filesystem": filesystem,
                    "config": config,
                    "children": [],
                    "confirmed": time.time()
                }

                injected_ids = tp.insert_node(new_node, parent_universal_id=parent, matrix_priv_obj=self.matrix_priv_obj)
                success = bool(len(injected_ids))
                if not success:
                    self.log(f"[INJECT][ERROR] Insert failed. Rejected node {universal_id}")
                    ret['error_code'] = 5
                    ret["message"] = f"[INJECT][ERROR] Insert failed. Rejected node: {universal_id}"
                else:
                    self.log(f"[INJECT] ✅ Injected agent '{universal_id}' under '{parent}'.")
                    if src:
                        self._save_payload_to_boot_dir(agent_name, src)

                    success=True

            if success:

                self.save_agent_tree_master()

                # --- REMEDY ---
                # After saving, the tree has new nodes with vaults.
                # We must force the tree parser to re-index its internal
                # dictionary so it can find the new agents.
                tp.reparse()
                # --- END REMEDY ---

                #delegate to parent agent
                self.delegate_tree_to_agent(parent, self.tree_path_dict)

                for agent_id in tp.get_first_level_child_ids(parent):
                    self.delegate_tree_to_agent(agent_id, self.tree_path_dict)

                ret["status"] = "success"
                ret.setdefault("message", "Agent(s) injected successfully.")

            else:

                ret["status"] = "error"
                ret.setdefault("message", "Injection failed or partial success.")

        except Exception as e:
            self.log(error=e, block="main_try")

        return ret

    def cmd_shutdown_subtree(self, content, packet, identity:IdentityObject = None):
        """Initiates a graceful shutdown of an agent and its entire subtree.

        This method works by dropping a 'die' file into the `/incoming`
        directory of the target agent and all of its descendants. The agents'
        `enforce_singleton` thread monitors for this file and will trigger a
        clean shutdown of the agent process upon detection.

        Args:
            content (dict): The payload containing the 'universal_id' of the
                root of the subtree to be shut down.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        target_id = content.get("universal_id")
        if not target_id:
            self.log("[SHUTDOWN][ERROR] Missing universal_id.")
            return

        tp = self.get_agent_tree_master()
        if not tp:
            self.log("[SHUTDOWN][ERROR] Failed to load tree.")
            return

        # Don't inject under parent, if marked for deletion or is deleted
        parent_node = tp.get_node(target_id)
        if parent_node and (parent_node.get("deleted") or parent_node.get("confirmed_deleted")):
            self.log(f"[INJECT][BLOCKED] Parent {target_id} is deleted. Cannot inject new nodes.")
            return


        ids = tp.get_subtree_nodes(target_id)
        for uid in ids:
            die_path = os.path.join(self.path_resolution["comm_path"], uid, "incoming", "die")
            os.makedirs(os.path.dirname(die_path), exist_ok=True)
            with open(die_path, "w", encoding="utf-8") as f:
                f.write("☠️")
            self.log(f"[SHUTDOWN] Dropped .die for {uid}")

    def cmd_resume_subtree(self, content, packet, identity:IdentityObject = None):
        """Resumes a previously shut-down agent and its subtree.

        This method is the inverse of `cmd_shutdown_subtree`. It removes the
        'die' and 'tombstone' files from the `/incoming` directory of the
        target agent and all of its descendants. Once the 'die' file is gone,
        the parent agent's `spawn_manager` will detect that the agent is down
        (via a stale heartbeat) and automatically resurrect it.

        Args:
            content (dict): The payload containing the 'universal_id' of the
                root of the subtree to be resumed.
            packet (dict): The raw packet data.
            identity (IdentityObject): The verified identity of the command sender.
        """
        target_id = content.get("universal_id")
        if not target_id:
            self.log("[RESUME][ERROR] Missing universal_id.")
            return

        tp = self.get_agent_tree_master()
        if not tp:
            self.log("[RESUME][ERROR] Failed to load tree.")
            return

        # Don't inject under parent, if marked for deletion or is deleted
        parent_node = tp.get_node(target_id)
        if parent_node and (parent_node.get("deleted") or parent_node.get("confirmed_deleted")):
            self.log(f"[INJECT][BLOCKED] Parent {target_id} is deleted. Cannot resume agent.")
            return

        ids = tp.get_subtree_nodes(target_id)
        for uid in ids:
            die = os.path.join(self.path_resolution["comm_path"], uid, "incoming", "die")
            tomb = os.path.join(self.path_resolution["comm_path"], uid, "incoming", "tombstone")

            for path in [die, tomb]:
                if os.path.exists(path):
                    os.remove(path)
                    self.log(f"[RESUME] Removed {os.path.basename(path)} for {uid}")

    def _save_payload_to_boot_dir(self, agent_name, src):
        try:

            decoded = base64.b64decode(src["payload"]).decode()
            sha_check = hashlib.sha256(decoded.encode()).hexdigest()

            if sha_check != src["sha256"]:
                self.log(f"[INJECT][SHA-FAIL] {agent_name} payload hash mismatch.")
                return

            dir_path = os.path.join(self.path_resolution["root_path"], "boot_payload", agent_name)
            os.makedirs(dir_path, exist_ok=True)

            file_path = os.path.join(dir_path, f"{agent_name}.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(decoded)

            self.log(f"[INJECT] ✅ Source code installed at {file_path}")

        except Exception as e:
            self.log(error=e, block="main_try")

    #checks everyone's tree against Matrix's agent_tree_master, using a hash of the agents tree
    def perform_tree_master_validation(self):

        try:

            if time.time() - self._last_tree_verify > 300:  # 5-minute window
                self._last_tree_verify = time.time()

                tp = self.get_agent_tree_master()
                if not tp:
                    self.log("[VERIFY-TREE] Could not load master tree.")
                    return

                for universal_id in tp.all_universal_ids():
                    self.delegate_tree_to_agent(universal_id, self.tree_path_dict)

        except Exception as e:
            self.log(error=e, block="main_try")

    # gives a given agent its agent_tree.json
    #2 types of trees roll through here: Matrix agent_tree_master.json and agents agent_tree.json
    #if encryption is on: every node will have a vault dict, inside contains the node's public key, timestamp issued
    def delegate_tree_to_agent(self, universal_id, tree_path):
        """Generates and delivers a secure, personalized "slice" of the agent tree.
        This method extracts the subtree of a specific agent from the master
        tree. It then securely signs and delivers this personalized
        `agent_tree.json` file to the target agent's `/directive` directory.
        This ensures that each agent only has the structural information it
        needs to manage its own children. It also delivers the agent's signed
        public key to its `/codex` directory for others to retrieve.

        Args:
            universal_id (str): The ID of the agent to deliver the tree slice to.
            tree_path (dict): A dictionary defining the path to the master tree.
        """
        try:
            #load the agent_tree_master
            tp = self.get_agent_tree_master()
            if not tp:
                self.log(f"Failed to load master tree for {universal_id}")
                return

            if not tp.has_node(universal_id):
                self.log(f"Skipping node {universal_id} not found in agent_tree, probably phantom dir created in comm by other agent or process.)")
                return


            subtree = tp.extract_subtree_by_id(universal_id)
            if not subtree:
                self.log(f"No subtree found for {universal_id}, sending empty tree.")
                subtree = {}

            try:
                #SAVE IDENTITY FILE to comm/{universal_id}/codex
                identity={"identity": subtree.get("vault",{}).get("identity", {}), "sig": subtree.get("vault",{}).get("sig", {})}

                dir = os.path.join(self.path_resolution["comm_path"], universal_id, "codex")
                os.makedirs(dir, exist_ok=True)
                fpath = os.path.join(dir, "signed_public_key.json")
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(identity, f, indent=2)

            except Exception as e:
                self.log(error=e, block='write_signed_public_key')

            # define structured path dict for saving
            path = {
                "path": self.path_resolution["comm_path"],
                "address": universal_id,
                "drop": "directive",
                "name": "agent_tree.json"
            }

            data = {"agent_tree": subtree, 'services': tp.get_minimal_services_tree(universal_id)}

            football = self.get_football(type=self.FootballType.PASS)
            football.load_identity_file(vault=subtree.get("vault"), universal_id=universal_id)
            self.save_directive(path, data, football=football)

            if self.debug.is_enabled():
                self.log(f"Tree delivered to {universal_id}")

        except Exception as e:
            self.log(error=e, block="main-try")



    def get_agent_tree_master(self):
        """Loads the agent_tree_master.json from disk into memory.
        This method acts as a cached loader for the canonical agent tree.
        If the tree is not already in memory, it loads the securely signed
        and encrypted `agent_tree_master.json` file from the Matrix agent's
        own `/directive` directory. It returns a TreeParser object representing
        the entire swarm structure.

        Returns:
            TreeParser: An object representing the entire agent tree, or None.
        """
        if not hasattr(self, "_agent_tree_master") or self._agent_tree_master is None:
            football = self.get_football(type=self.FootballType.CATCH)
            self._agent_tree_master = self.load_directive(self.tree_path_dict, football)
            self.log("[TREE] agent_tree_master loaded into memory.")

        return self._agent_tree_master


    def save_agent_tree_master(self):
        """Signs and saves the current state of the in-memory agent tree to disk.

        This method is called whenever the swarm's structure is modified (e.g.,
        after injecting or deleting an agent). It takes the in-memory tree,
        adds any agent identity -- signs with the Matrix private key, generates rsa key pairs, private keys, to any added agents, and then
        securely saves the entire structure back to `agent_tree_master.json`.
        This persists the change and ensures the file on disk is always the
        single source of truth.

        Returns:
            bool: True if the save was successful, False otherwise.
        """
        try:
            if not hasattr(self, "_agent_tree_master") or self._agent_tree_master is None:
                self.log("[TREE][WARN] Cannot save — agent_tree_master not loaded.")
                return False

            self._agent_tree_master.pre_scan_for_duplicates(self._agent_tree_master.root)

            data = {"agent_tree": self._agent_tree_master.root}
            football = self.get_football(type=self.FootballType.PASS)
            football.load_identity_file(vault=self.tree_node['vault'], universal_id='matrix')
            self.save_directive(self.tree_path_dict, data, football=football)
            self.log("[TREE] agent_tree_master saved and signed.")
            return True

        except Exception as e:
            self.log("[TREE][ERROR] Failed to save agent_tree_master.", error=e)
            return False

    def cmd_deliver_agent_tree_to_child(self, content, packet, identity: IdentityObject = None):
        try:
            uid = content.get("universal_id")
            if not uid:
                self.log("[DELIVER-TREE][ERROR] Missing universal_id.")
                return

            self.delegate_tree_to_agent(uid, self.tree_path_dict)

        except Exception as e:
            self.log("[DELIVER-TREE][ERROR]", error=e)


if __name__ == "__main__":
    agent = Agent()
    agent.boot()
