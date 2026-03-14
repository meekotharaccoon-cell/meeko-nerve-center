# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))
import json
import time
import subprocess
import ipaddress
from datetime import datetime
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
import geoip2.database
import requests
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        self.name = "Gatekeeper"
        cfg = self.tree_node.get("config", {})

        if os.path.exists("/var/log/secure"):
            self.log_path = "/var/log/secure"
        elif os.path.exists("/var/log/auth.log"):
            self.log_path = "/var/log/auth.log"
        else:
            self.log_path = cfg.get("log_path", "/var/log/secure") # Debian/Ubuntu — change to /var/log/secure on RHEL/CentOS

        self.maxmind_db = cfg.get("maxmind_db", "GeoLite2-City.mmdb")
        self.geoip_enabled = cfg.get("geoip_enabled", 1)
        self.always_alert = bool(cfg.get("always_alert", 1))
        self.cooldown_sec = 300
        self.last_alerts = {}

        cfg_db = str(cfg.get("maxmind_db", "")).strip()

        # If it's an absolute path or a path relative to install_path
        if cfg_db and os.path.isfile(cfg_db):
            self.mmdb_path = cfg_db
        else:
            self.mmdb_path = os.path.join(self.path_resolution["install_path"], "maxmind", "GeoLite2-City.mmdb")

        self.log_dir = os.path.join(self.path_resolution["comm_path"], "gatekeeper")
        os.makedirs(self.log_dir, exist_ok=True)

    def should_alert(self, key):

        if self.always_alert:
            return True

        now = time.time()
        last = self.last_alerts.get(key, 0)
        if now - last > self.cooldown_sec:
            self.last_alerts[key] = now
            return True
        return False

    def resolve_ip(self, ip):
        if not os.path.exists(self.mmdb_path):
            self.log(f"[GATEKEEPER][GEOIP] DB not found at {self.mmdb_path}")
            return {"ip": ip, "city": None, "region": None, "country": None}

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
            self.log(f"[GATEKEEPER][GEOIP][ERROR] {e}")
            return {"ip": ip}

    def drop_alert(self, info):

        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_send_alert_msg"})

        pk2 = self.get_delivery_packet("notify.alert.general")

        try:
            server_ip = requests.get("https://api.ipify.org").text.strip()
        except Exception:
            server_ip = "Unknown"

        # Force inject message
        msg_text = (
            f"🛡️ SSH Login Detected\n\n"
            f"• Server IP: {server_ip}\n"
            f"• User: {info.get('user')}\n"
            f"• IP: {info.get('ip')}\n"
            f"• Location: {info.get('city')}, {info.get('country')}\n"
            f"• Time: {info.get('timestamp')}\n"
            f"• Auth: {info.get('auth_method')}\n"
            f"• Terminal: {info.get('tty')}"
        )

        pk2.set_data({
            "msg": msg_text,
            "universal_id": self.command_line_args.get("universal_id", "unknown"),
            "level": "critical",
            "cause": "SSH Login Detected",
            "origin": self.command_line_args.get("universal_id", "unknown")
        })

        pk1.set_packet(pk2, "content")

        alert_nodes = self.get_nodes_by_role("hive.alert.send_alert_msg")
        if not alert_nodes:
            self.log("[WATCHDOG][ALERT] No alert-compatible agents found.")
            return

        for node in alert_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def tail_log(self):
        self.log(f"[GATEKEEPER] Tailing: {self.log_path}")
        with subprocess.Popen(["tail", "-n", "0", "-F", self.log_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                if "Accepted" in line and "from" in line:
                    try:
                        timestamp = " ".join(line.strip().split()[0:3])
                        if "password" in line:
                            auth_method = "password"
                        elif "publickey" in line:
                            auth_method = "public key"
                        else:
                            auth_method = "unknown"

                        user = line.split("for")[1].split("from")[0].strip()
                        ip = line.split("from")[1].split()[0].strip()

                        try:
                            ipaddress.ip_address(ip)
                        except ValueError:
                            self.log(f"[GATEKEEPER][SKIP] Invalid IP: {ip}")
                            return

                        tty = "unknown"
                        geo = self.resolve_ip(ip)
                        alert_data = {
                            "user": user,
                            "ip": ip,
                            "tty": tty,
                            "auth_method": auth_method,
                            "timestamp": timestamp,
                            **geo
                        }

                        if self.should_alert(ip):
                            self.drop_alert(alert_data)

                        self.persist(alert_data)

                    except Exception as e:
                        self.log(f"[GATEKEEPER][PARSER][ERROR] Failed to parse login line: {e}")

    def persist(self, data):
        fname = f"ssh_{self.today()}.log"
        path = os.path.join(self.log_dir, fname)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def today(self):
        return datetime.now().strftime("%Y-%m-%d")

    def worker(self, config:dict = None, identity:IdentityObject = None):
        self.tail_log()
        interruptible_sleep(self, 10)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()