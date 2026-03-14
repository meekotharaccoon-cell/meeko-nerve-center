# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import pwd
import time
import json
import hashlib
import subprocess
import threading
import inotify.adapters
from datetime import datetime
from collections import OrderedDict
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.mixin.reflex_alert import ReflexAlertMixin
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent, ReflexAlertMixin):
    def __init__(self):
        super().__init__()
        self.AGENT_VERSION = "1.2.0"
        self.sessions = {}
        self.file_alerts = {}  # (path -> timestamp)
        self.command_hashes = OrderedDict()

        cfg = self.tree_node.get("config", {})

        self.report_role = cfg.get("report_to_role", None)

        self.tick_rate = cfg.get("tick_rate", 5)
        self.command_patterns = cfg.get("command_patterns", [
            "rm -rf", "scp", "curl", "wget", "nano /etc", "vi /etc", "vim /etc",
            "sudo", "su", "chmod 777", "systemctl stop", "service stop"
        ])

        self.watch_paths = cfg.get("watch_paths", ["/etc/passwd", "/etc/shadow", "/root/.ssh", "/home", "/var/www"])
        self.session_dir = os.path.join(self.path_resolution["comm_path"],
                                        self.command_line_args.get("universal_id", "ghostwire"), "sessions")
        os.makedirs(self.session_dir, exist_ok=True)

    def worker_pre(self):
        self.enforce_prompt_command_once()
        threading.Thread(target=self.watch_file_changes, daemon=True).start()

    def post_boot(self):
        self.log(f"{self.NAME} v{self.AGENT_VERSION} – shadow tracker engaged.")

    def worker(self, config: dict = None, identity: IdentityObject = None):

        self.track_active_users()
        self.poll_shell_history()
        interruptible_sleep(self, self.tick_rate)

    def enforce_prompt_command_once(self):
        paths = ["/etc/bash.bashrc", os.path.expanduser("~/.bashrc")]
        for path in paths:
            try:
                if not os.path.exists(path):
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "PROMPT_COMMAND" in content and "history -a" in content:
                        self.log(f"[GHOSTWIRE][PROMPT] Already present in {path}")
                        continue
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n# Added by GhostWire for real-time history logging\n")
                    f.write("export PROMPT_COMMAND='history -a'\n")
                self.log(f"[GHOSTWIRE][PROMPT] Injected PROMPT_COMMAND into {path}")
            except Exception as e:
                self.log(f"[GHOSTWIRE][PROMPT][ERROR] {path}: {e}")


    def track_active_users(self):
        try:
            output = subprocess.check_output(["who"], text=True)
            current_users = {}
            for line in output.strip().split("\n"):
                parts = line.strip().split()
                if len(parts) >= 2:
                    user, tty = parts[0], parts[1]
                    current_users[user] = tty

                    if user not in self.sessions:
                        # SIGN-IN
                        self.sessions[user] = {
                            "tty": tty,
                            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "commands": [],
                            "files_touched": [],
                            "last_seen": time.time()
                        }
                        msg = f"👤 User Signed In\n• User: {user}\n• TTY: {tty}\n• Time: {self.sessions[user]['start_time']}"
                        #self.alert_operator(message=msg)
                        self.log(f"[GHOSTWIRE][SIGNIN] {msg}")
                        session_path = os.path.join(self.session_dir, user, f"{self.today()}.log")
                        os.makedirs(os.path.dirname(session_path), exist_ok=True)
                        if os.path.exists(session_path):
                            try:
                                with open(session_path, "r", encoding="utf-8") as f:
                                    loaded = json.load(f)
                                    self.sessions[user]["commands"] = loaded.get("commands", [])
                            except Exception as e:
                                self.log(f"[GHOSTWIRE][LOAD] Failed to reload session for {user}: {e}")

                    else:
                        self.sessions[user]["last_seen"] = time.time()

            # SIGN-OUT
            for user in list(self.sessions.keys()):
                if user not in current_users:
                    msg = (
                        f"👋 User Signed Out\n"
                        f"• User: {user}\n"
                        f"• Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"🔒 Surveillance interrupted.\n"
                        f"🚨 Cuffs were **not** applied.\n"
                        f"📡 Tagging for re-entry tracking..."
                    )
                    #self.alert_operator(message=msg)
                    self.log(f"[GHOSTWIRE][SIGNOUT] {msg}")
                    del self.sessions[user]

        except Exception as e:
            self.log(f"[GHOSTWIRE][ERROR] Failed to track users: {e}")

    def watch_file_changes(self):
        i = inotify.adapters.Inotify()

        for path in self.watch_paths:
            try:
                i.add_watch(path)
            except Exception as e:
                self.log(f"[GHOSTWIRE][INOTIFY][ERROR] {path}: {e}")

        self.log(f"[GHOSTWIRE][INOTIFY] Monitoring: {', '.join(self.watch_paths)}")

        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            full_path = os.path.join(path, filename)
            now = time.strftime('%Y-%m-%d %H:%M:%S')

            # Message format for logs or alert
            msg = (
                f"👁️ Inotify Trigger\n"
                f"• Path: {full_path}\n"
                f"• Event: {', '.join(type_names)}\n"
                f"• Time: {now}"
            )

            # 🛡 Filter out repeated reads unless it's a first access
            if "IN_OPEN" in type_names or "IN_ACCESS" in type_names:
                if self.should_alert_path(full_path):
                    self.log(f"[GHOSTWIRE][INOTIFY] {msg}")
                    #self.alert_operator(message=msg)
                continue  # don't alert twice if IN_CLOSE_NOWRITE follows

            # 🔥 But always alert on write/delete
            if "IN_CLOSE_WRITE" in type_names or "IN_DELETE" in type_names:
                self.log(f"[GHOSTWIRE][INOTIFY] {msg}")
                #self.alert_operator(message=msg)


    def should_alert_path(self, full_path):
        now = time.time()
        last = self.file_alerts.get(full_path, 0)
        if now - last > 60:  # only once per minute per path
            self.file_alerts[full_path] = now
            return True
        return False

    def resolve_history_path(self, user):
        try:
            user_info = pwd.getpwnam(user)
            home = user_info.pw_dir
            shell = user_info.pw_shell
            if "bash" in shell:
                return os.path.join(home, ".bash_history")
            elif "zsh" in shell:
                return os.path.join(home, ".zsh_history")
            elif "fish" in shell:
                return os.path.join(home, ".config", "fish", "fish_history")
            else:
                self.log(f"[GHOSTWIRE][HISTORY] Unsupported shell for user {user}: {shell}")
                return None
        except Exception as e:
            self.log(f"[GHOSTWIRE] Failed to resolve history path for {user}: {e}")
            return None

    def poll_shell_history(self):
        for user, session in self.sessions.items():
            history_path = self.resolve_history_path(user)
            if not history_path or not os.path.exists(history_path):
                self.log(f"[GHOSTWIRE] No shell history found for {user} — logging login only.")
                self.persist(user, self.sessions[user])  # Still persist session
                continue
            last_seen_cmd = session.get("last_command_timestamp", 0)
            if time.time() - last_seen_cmd > 600:
                self.log(f"[GHOSTWIRE][{user}] 🕒 History inactive >10 min. May need PROMPT_COMMAND='history -a'")

            if os.path.exists(history_path):
                try:
                    with open(history_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.read().splitlines()
                    new_commands = [cmd for cmd in lines if cmd not in session["commands"]]
                    for cmd in new_commands:
                        session["commands"].append(cmd)
                        session["last_command_timestamp"] = time.time()

                        self.log(f"[GHOSTWIRE][{user}] {cmd}")
                        cmd_hash = self.hash_command(cmd)
                        if cmd_hash not in self.command_hashes:
                            self.remember_command(cmd_hash)
                            if self.is_suspicious(cmd):
                                self.alert(user, cmd)
                    self.persist(user, session)
                except Exception as e:
                    self.log(f"[GHOSTWIRE][{user}][ERROR] {e}")

    def is_suspicious(self, cmd):
        return any(p in cmd for p in self.command_patterns)

    def alert(self, user, cmd):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            f"🕶️ Suspicious Command Detected\n"
            f"• User: {user}\n"
            f"• Command: {cmd}\n"
            f"• Time: {timestamp}"
        )

        self.log(f"[GHOSTWIRE][ALERT] {msg}")

        # Also send a structured data report for the detective
        self.send_data_report(
            status="suspicious_command",
            severity="WARNING",
            details=f"User '{user}' executed command: {cmd}"
        )

    def hash_command(self, cmd):
        return hashlib.sha256(cmd.strip().encode()).hexdigest()

    def remember_command(self, cmd_hash):
        self.command_hashes[cmd_hash] = time.time()
        if len(self.command_hashes) > 5000:
            self.command_hashes.popitem(last=False)

    def persist(self, user, session):
        date_str = self.today()
        path = os.path.join(self.session_dir, user)
        os.makedirs(path, exist_ok=True)
        fpath = os.path.join(path, f"{date_str}.log")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2)

    def today(self):
        return datetime.now().strftime("%Y-%m-%d")

    def send_data_report(self, status, severity, details=""):
        """Sends a structured data packet for forensic analysis."""
        if not self.report_role:
            return

        report_nodes = self.get_nodes_by_role(self.report_role)
        if not report_nodes:
            return

        # Wrapper packet
        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_ingest_status_report"})

        # Structured event payload
        pk2 = self.get_delivery_packet("standard.status.event.packet")
        pk2.set_data({
            "source_agent": self.command_line_args.get("universal_id"),
            "service_name": "ghost_wire",  # A new service name for this event type
            "status": status,
            "details": details,
            "severity": severity,
        })

        pk1.set_packet(pk2, "content")

        for node in report_nodes:
            self.pass_packet(pk1, node["universal_id"])

if __name__ == "__main__":
    agent = Agent()
    agent.boot()
