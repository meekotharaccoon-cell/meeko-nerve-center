#Authored by Daniel F MacDonald
# ╔════════════════════════════════════════════════════════╗
# ║               🧹 SCAVENGER AGENT 🧹                    ║
# ║   Runtime Sweeper · Pod Watchdog · Tombstone Handler   ║
# ║   Brought online under blackout protocol | Rev 1.8      ║
# ║   Monitors: /pod/* | Deletes: expired / orphaned nodes ║
# ╚════════════════════════════════════════════════════════╝
# 🧹 FINAL FULL HIVE-CORRECTED SCAVENGERAGENT v3.1 🧹
# Using ONLY post_boot(), NEVER manual boot()

import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import time
import json
import shutil
import threading
import psutil
from pathlib import Path

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.file_system.util.json_safe_write import JsonSafeWrite
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep

class Agent(BootAgent):
    def __init__(self):
        super().__init__()

    def post_boot(self):
        try:
            self.log("[SCAVENGER] Online. Scanning the battlefield for tombstones...")
            threading.Thread(target=self.scavenger_sweep, daemon=True).start()
        except Exception as e:
            self.log(f"[SCAVENGER][POST-BOOT ERROR] {e}")

    def worker_pre(self):
        self.log("[SCAVENGER] Agent activated. Monitoring for cleanup ops.")

    def worker_post(self):
        self.log("[SCAVENGER] Shutdown confirmed. Sweep logs complete.")

    def scavenger_sweep(self):
        self.log("[SCAVENGER] Background sweep active. Scanning every 5 minutes...")
        while self.running:
            try:
                now = time.time()
                pod_root = self.path_resolution["pod_path"]
                comm_root = self.path_resolution["comm_path"]

                if not os.path.exists(pod_root) or not os.path.exists(comm_root):
                    self.log("[SCAVENGER][WARNING] Pod or Comm path missing. Skipping sweep.")
                    interruptible_sleep(self, 120)
                    continue

                #Loop through the pod looking for boot.json to extract --job [identity train]
                self.log("[SCAVENGER] 🧹 Running sweep at " + time.strftime('%H:%M:%S'))
                for uuid in os.listdir(pod_root):

                    try:

                        pod_path = os.path.join(pod_root, uuid)
                        boot_path = os.path.join(pod_path, "boot.json")

                        if not os.path.isfile(boot_path):
                            continue

                        with open(boot_path, "r", encoding="utf-8") as f:
                            boot_data = json.load(f)
                            universal_id = boot_data.get("universal_id")
                            cmdline_target = boot_data.get("cmd", [])

                        if not universal_id or not cmdline_target:
                            continue

                        comm_path = os.path.join(comm_root, universal_id)

                        die_path = os.path.join(comm_path, "incoming", "die")
                        tombstone_comm = os.path.join(comm_path, "incoming", "tombstone")
                        tombstone_pod = os.path.join(pod_path, "tombstone")

                        tombstone_paths = [tombstone_comm, tombstone_pod]
                        tombstone_found = False
                        tombstone_age_ok = False
                        now = time.time()

                        #self.log(f"[DEBUG] 🔍 Checking cleanup readiness for '{universal_id}'")
                        #self.log(f"         ⛓️  die path: {die_path}")
                        #self.log(f"         ⛓️  tombstone_comm: {tombstone_comm}")
                        #self.log(f"         ⛓️  tombstone_pod: {tombstone_pod}")

                        for tomb in tombstone_paths:
                            if os.path.exists(tomb):
                                age = now - os.path.getmtime(tomb)
                                self.log(f"[DEBUG] ⏱️ Tombstone '{tomb}' age: {age:.2f}s")
                                tombstone_found = True
                                if age >= 300:  # Change to 0 to force
                                    tombstone_age_ok = True
                                    break

                        die_exists = os.path.exists(die_path)

                        # Log result before decision
                        #self.log(f"[DEBUG] ✅ tombstone_found={tombstone_found}, tombstone_age_ok={tombstone_age_ok}, die_exists={die_exists}")

                        if not tombstone_found or not tombstone_age_ok or not die_exists:
                            self.log(f"[SCAVENGER] ⚠️ Skipping {universal_id} — nothing to do.")
                            continue

                        self.log(f"[SCAVENGER] 🧼 Cleaning up {universal_id} now.")

                        still_alive = False
                        for proc in psutil.process_iter(["pid", "cmdline", "status"]):
                            if proc.info['cmdline'] == cmdline_target:
                                if proc.info.get("status") == psutil.STATUS_ZOMBIE:
                                    self.log(f"[SCAVENGER] PID {proc.info['pid']} is a zombie. Allowing cleanup.")
                                else:
                                    still_alive = True

                        if still_alive:
                            self.log(f"[SCAVENGER][WARNING] Agent {universal_id} still breathing by cmdline. Delaying sweep.")
                            continue

                        self.log(f"[SCAVENGER] Sweeping corpse: {universal_id} (UUID {uuid})")
                        if os.path.exists(pod_path):
                            shutil.rmtree(pod_path)
                        if os.path.exists(comm_path):
                            shutil.rmtree(comm_path)

                        self.send_confirmation(universal_id, status="terminated")

                    except Exception as e:
                        self.log(f"[SCAVENGER][SWEEP-UUID-ERROR] {e}")

            except Exception as e:
                self.log(f"[SCAVENGER][SWEEP-MAIN-ERROR] {e}")

            interruptible_sleep(self, 120)


    def send_confirmation(self, universal_id, status="terminated"):
        try:

            target = "matrix"

            if not universal_id:
                return

            # request the agent_tree_master from Matrix
            pl = {"origin": self.command_line_args['universal_id'],
                  "handler": "cmd_deletion_confirmation",
                  "content": {"universal_id": universal_id, status: status},
                  "timestamp": time.time()}

            pk = self.get_delivery_packet("standard.command.packet", new=True)
            pk.set_data(pl)

            self.pass_packet(pk, target)

            self.log("[SCAVENGER] Sent agent_tree_master sync request to Matrix.")

        except Exception as e:
            self.log(f"[SCAVENGER][ERROR] Sync request failed: {e}")


if __name__ == "__main__":
    agent = Agent()
    agent.boot()