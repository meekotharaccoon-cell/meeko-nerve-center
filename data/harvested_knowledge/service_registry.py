
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import json
import time
import threading
from matrixswarm.core.boot_agent import BootAgent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject
class Agent(BootAgent):
    def __init__(self):
        super().__init__()

        self.directory = {}
        self.tree_path = os.path.join(self.path_resolution["comm_path"], "matrix", "agent_tree_master.json")
        self.incoming_path = os.path.join(self.path_resolution["comm_path_resolved"], "incoming")

    def worker_pre(self):
        self.log("[RESOLVER] Booting service discovery...")
        self.scan_tree_once()
        threading.Thread(target=self.watch_files, daemon=True).start()

    def worker(self, config:dict = None, identity:IdentityObject = None):
        while self.running:
            interruptible_sleep(self, 600)

    def scan_tree_once(self):
        if not os.path.exists(self.tree_path):
            self.log("[RESOLVER][WARN] Tree file not found.")
            return
        try:
            with open(self.tree_path, "r", encoding="utf-8") as f:
                tree = json.load(f)
            self.directory.clear()
            self.parse_tree(tree)
            self.save_directory_snapshot()
            self.log(f"[RESOLVER] Loaded {len(self.directory)} services.")
        except Exception as e:
            self.log(f"[RESOLVER][ERROR] Failed to scan tree: {e}")

    def parse_tree(self, node):
        try:
            name = (node.get("name") or node.get("universal_id", "unknown")).lower()
            uid = node.get("universal_id")
            app = node.get("app")
            if not uid or not name:
                return
            self.directory.setdefault(name, [])
            if all(e["universal_id"] != uid for e in self.directory[name]):
                self.directory[name].append({"universal_id": uid, "app": app})
            for child in node.get("children", []):
                self.parse_tree(child)
        except Exception as e:
            self.log(f"[RESOLVER][PARSE] Error: {e}")

    def handle_payload_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            content = payload.get("content", {})
            name = content.get("agent_name") or content.get("name")
            uid = content.get("universal_id")
            app = content.get("directives", {}).get("app")
            if name and uid:
                name = name.lower()
                self.directory.setdefault(name, [])
                if all(e["universal_id"] != uid for e in self.directory[name]):
                    self.directory[name].append({"universal_id": uid, "app": app})
                    self.log(f"[RESOLVER] Registered service: {name} ({uid})")
                    self.save_directory_snapshot()
        except Exception as e:
            self.log(f"[RESOLVER][PARSE ERROR] {e}")

    def save_directory_snapshot(self):
        try:
            path = os.path.join(self.path_resolution["comm_path_resolved"], "directory.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.directory, f, indent=2)
        except Exception as e:
            self.log(f"[RESOLVER][SNAPSHOT] Failed: {e}")

    def cmd_resolve(self, command, packet, identity:IdentityObject = None):
        try:
            payload = packet.get("payload", {})
            role = payload.get("role", "").lower()
            reply_path = os.path.join(self.path_resolution["comm_path"], "commander-1", "stack", "resolve_oracle_test.json")

            if not role or not reply_path:
                self.log("[RESOLVER][CMD] Missing role or reply path.")
                return

            if not os.path.exists(os.path.dirname(reply_path)):
                self.log(f"[RESOLVER][SKIP] Reply path missing: {reply_path}")
                return

            agents = self.directory.get(role, [])
            response = {
                "role": role,
                "targets": agents,
                "count": len(agents)
            }

            with open(reply_path, "w", encoding="utf-8") as f:
                json.dump(response, f, indent=2)

            self.log(f"[RESOLVER][REPLY] → {reply_path} ({len(agents)} matches)")

        except Exception as e:
            self.log(f"[RESOLVER][CMD-ERROR] {e}")

    def watch_files(self):
        class Handler(FileSystemEventHandler):
            def on_created(inner_self, event):
                if not event.is_directory and any(x in event.src_path for x in ["inject", "spawn"]):
                    self.handle_payload_file(event.src_path)
            def on_modified(inner_self, event):
                if not event.is_directory and event.src_path == self.tree_path:
                    self.log("[RESOLVER] Tree modified. Rescanning.")
                    self.scan_tree_once()

        observer = Observer()
        observer.schedule(Handler(), self.path_resolution["comm_path_resolved"], recursive=False)
        observer.schedule(Handler(), os.path.dirname(self.tree_path), recursive=False)
        observer.start()
        self.log("[RESOLVER] Watching for service and tree changes.")
        try:
            while self.running:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    agent = Agent()
    agent.boot()

