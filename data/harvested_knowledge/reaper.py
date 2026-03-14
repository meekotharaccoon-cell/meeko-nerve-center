#Authored by Daniel F MacDonald and ChatGPT 4
# ╔═══════════════════════════════════════════════╗
# ║              ☠ REAPER AGENT ☠                ║
# ║   Tactical Cleanup · Wipe Authority · V2.5    ║
# ║        Forged in the halls of Matrix          ║
# ║  Accepts: .cmd / .json  |  Modes: soft/full   ║
# ╚═══════════════════════════════════════════════╝
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
# DisposableReaperAgent.py

import json
import time
import threading
from pathlib import Path

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.processes.reaper_universal_id_handler import ReaperUniversalHandler  # PID Handler
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
class Agent(BootAgent):
    def __init__(self):
        super().__init__()


        # Load targets, kill ID, and initialize paths
        config = self.tree_node.get("config", {})
        self.is_mission = bool(config.get("is_mission", False))
        self.targets = self.command_line_args.get("targets") or config.get("kill_list", [])
        self.universal_ids = self.command_line_args.get("universal_ids") or config.get("universal_ids", {})
        self.kill_id = self.command_line_args.get("kill_id") or config.get("kill_id") or f"reap-{int(time.time())}"
        self.strike_delay = config.get("delay", 0)
        self.tombstone_comm = config.get("tombstone_comm", True)
        self.tombstone_pod = config.get("tombstone_pod", True)
        self.cleanup_die = config.get("cleanup_die", False)

        self.universal_id_handler = ReaperUniversalHandler(self.path_resolution['pod_path'], self.path_resolution['comm_path'], logger=self.logger)

    def post_boot(self):
        """
        Logs the mission details and starts the mission in a separate thread.
        """
        if self.is_mission:
            self.mission()
        else:
            threading.Thread(target=self.patrol_comm_for_hit_cookies, daemon=True).start()

    def worker_pre(self):
        self.log("[REAPER] Agent entering execution mode. Targets loaded. Blades sharp.")

    def worker_post(self):
        self.log("[REAPER] Mission completed. Reaper dissolving into silence.")

    def mission(self):
        """
        Execute the mission using the Permanent ID handler to process shutdown requests for all targets.
        """
        self.log("[INFO] Inserting hit team...")

        if self.strike_delay > 0:
            self.log(f"[REAPER] ⏱ Waiting {self.strike_delay} seconds before executing strike...")
            time.sleep(self.strike_delay)

        # Filter `self.targets` based on valid universal_ids
        filtered_universal_ids = {universal_id: self.universal_ids[universal_id] for universal_id in self.targets if universal_id in self.universal_ids}

        if not filtered_universal_ids:
            self.log("[WARNING] No valid targets found in the provided target list.")
            self.running = False  # Mark the agent as stopped
            return

        # Use central handler to process all valid targets at once
        try:

            self.universal_id_handler.process_all_universal_ids(
                filtered_universal_ids,
                tombstone_mode=True,
                wait_seconds=20,
                tombstone_comm=self.tombstone_comm,
                tombstone_pod=self.tombstone_pod
            )
            if self.cleanup_die:
                for uid in filtered_universal_ids:
                    try:
                        die_path = os.path.join(self.path_resolution["comm_path"], uid, "incoming", "die")
                        if os.path.exists(die_path):
                            os.remove(die_path)
                            self.log(f"[REAPER] Removed die signal from comm: {uid}")
                    except Exception as e:
                        self.log(f"[REAPER][ERROR] Failed to remove die for {uid}: {e}")

            self.log("[INFO] Mission completed successfully.")

        except Exception as e:
            self.log(f"[ERROR] Failed to complete mission: {str(e)}")

        self.running = False  # Mark the agent as stopped
        self.log("[INFO] Mission completed and the agent is now stopping.")
        self.leave_tombstone_and_die()

    #TODO verify Matrix sig
    def verify_hit_cookie(self, payload, signature):
        try:
            pass
        except Exception as e:
            #self.log(f"[ERROR] Failed to complete mission: {str(e)}")
            pass

        return True

    def patrol_comm_for_hit_cookies(self):
        self.log("[REAPER] 🛰 Patrol mode active. Scanning for hit cookies...")
        comm_root = Path(self.path_resolution["comm_path"])
        while True:
            try:
                for agent_dir in comm_root.iterdir():
                    hello_path = agent_dir / "hello.moto"
                    cookie_path = hello_path / "hit.cookie"

                    if not cookie_path.exists():
                        continue

                    payload = {}
                    uid=None
                    with open(cookie_path, "r", encoding="utf-8") as f:
                        try:
                            payload = json.load(f)
                            uid = payload.get("target")
                        except Exception as e:
                            self.log(f"[REAPER][WARN] Malformed cookie in {cookie_path}: {e}")
                            continue

                    # Optional: verify signature
                    signature = "sig"  # payload.get("signature")
                    if not self.verify_hit_cookie(payload, signature):
                        if not uid:
                            uid = "[not set]"
                        self.log(f"[REAPER][WARN] Invalid or unsigned kill cookie for {uid}, skipping.")
                        continue


                    if not uid:
                        continue

                    # TODO: Verify signature if encryption is enabled (hook here)
                    self.log(f"[REAPER] ☠ Target marked: {uid} — executing...")

                    # Execute: reuse universal_id handler
                    self.process_universal_id(uid)

                    #cookie_path.unlink()  # Remove cookie after execution - scavenger will do it
            except Exception as e:
                self.log(f"[REAPER][ERROR] Patrol loop failed: {e}")

            interruptible_sleep(self, 15)

    def process_universal_id(self, uid):
        handler = ReaperUniversalHandler(self.path_resolution["pod_path"], self.path_resolution["comm_path"], logger=self.logger)
        handler.process_all_universal_ids(
            [uid],
            tombstone_mode=True,
            wait_seconds=15,
            tombstone_comm=True,
            tombstone_pod=True
        )

    def leave_tombstone_and_die(self):
        """
        Reaper drops his own tombstone and shuts down cleanly.
        """
        try:

            incoming_dir = os.path.join(self.path_resolution["comm_path"], self.command_line_args["universal_id"], "incoming")
            os.makedirs(incoming_dir, exist_ok=True)

            pod_dir = os.path.join(self.path_resolution["pod_path"], self.command_line_args["install_name"])

            # Write tombstone to comm
            die_path = os.path.join(incoming_dir, "die")
            with open(die_path, "w", encoding="utf-8") as f:
                f.write("true")

            # Write tombstone to comm
            tombstone_path = os.path.join(incoming_dir, "tombstone")
            with open(tombstone_path, "w", encoding="utf-8") as f:
                f.write("true")

            # Write tombstone to pod
            tombstone_path = os.path.join(pod_dir, "tombstone")
            with open(tombstone_path, "w", encoding="utf-8") as f:
                f.write("true")

            death_warrant=self.tree_node.get('config',{}).get('death_warrant', False)
            if death_warrant:
                self.deliver_death_warrant(death_warrant)

            self.log(f"[DISPOSABLE-REAPER] Die cookie dropped & Tombstone dropped. Mission complete. Signing off.")

        except Exception as e:
            self.log(f"[DISPOSABLE-REAPER][ERROR] Failed to leave tombstone: {str(e)}")

        finally:
            self.running = False  # Always stop running, even if tombstone writing fails

    def attempt_kill(self, universal_id):
        """
        Deliver 'die' and 'tombstone' signals to a directory and wait for graceful shutdown.
        Escalates with Permanent ID Handler if the process resists termination.
        """
        # Paths for the target
        pod_path = os.path.join(self.path_resolution['pod_path'], universal_id)
        comm_path = os.path.join(self.path_resolution['comm_path'], universal_id)

        # Send 'die' and 'tombstone' signals via `comm_path`
        incoming = os.path.join(comm_path, "incoming")
        os.makedirs(incoming, exist_ok=True)
        with open(os.path.join(incoming, "die"), "w", encoding="utf-8") as f:
            json.dump({"cmd": "die", "force": False}, f)
        with open(os.path.join(incoming, "tombstone"), "w", encoding="utf-8") as f:
            f.write("true")

        self.log(f"[DISPOSABLE-REAPER] Die and tombstone delivered to {universal_id}")

        # Monitor shutdown success via hello.moto file
        hello_path = os.path.join(pod_path, "hello.moto")
        max_wait = 18
        elapsed = 0
        while elapsed < max_wait:
            if not os.path.exists(hello_path):
                self.log(f"[DISPOSABLE-REAPER] {universal_id} down gracefully.")
                return True
            time.sleep(3)
            elapsed += 3

        # Escalate with PID handler if process resists
        self.log(f"[DISPOSABLE-REAPER] {universal_id} resisted — invoking Full PID Handler escalation.")
        self.escalate_with_pid_handler(universal_id)
        return False

    def escalate_with_pid_handler(self, universal_id):
        """
        Escalate the shutdown process using the Permanent ID handler for the specified target.
        """
        try:
            self.universal_id_handler.shutdown_processes(universal_id, universal_id)
            self.log(f"[DISPOSABLE-REAPER] PID Handler escalation complete for {universal_id}")
        except Exception as e:
            self.log(f"[DISPOSABLE-REAPER] PID Handler escalation FAILED for {universal_id}: {e}")

    def deliver_death_warrant(self, signed_warrant):

        try:

            # request the agent_tree_master from Matrix
            packet = self.get_delivery_packet("standard.command.packet", new=True)
            packet.set_data({
                "handler": "cmd_validate_warrant",
                "agent_id": self.command_line_args["universal_id"],
                "content": {  # ✅ wrap inside content
                    "agent_id": self.command_line_args["universal_id"],
                    "warrant": signed_warrant
                },
                "timestamp": time.time(),
                "origin": self.command_line_args["universal_id"]
            })
            self.pass_packet(packet, "matrix")

            self.log("[REAPER] 🕊 Death warrant dispatched to Matrix for post-mission validation.")

        except Exception as e:
            self.log(f"Sync request failed: {e}")



    def send_mission_report(self, results):
        """
        Generate and save a mission report including results for each target.
        """
        payload = {
            "kill_id": self.kill_id,
            "targets": self.targets,
            "results": results,
            "timestamp": time.time(),
            "message": f"Kill operation {self.kill_id} complete."
        }

        report_path = os.path.join(self.outbox_path, f"reaper_mission_{self.kill_id}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.log(f"[DISPOSABLE-REAPER] Mission report written: {report_path}")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()