# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
import sys
import os
import time
import requests

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))


from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):

    def __init__(self):
        super().__init__()
        self.name = "StormCrow"

        self._initialized_from_tree = False
        self._private_config = self.tree_node.get("config", {})

    def cmd_update_agent_config(self):

        try:

            self._initialized_from_tree = True
            # Support ZIP code override
            self.zipcode = self._private_config.get("zip-code") or os.getenv("WEATHER_ZIPCODE")

            self.log(f"🌪 [HOWDY] We've moved. StormCrow now watches over ZIP: {self.zipcode}")

            if self.zipcode:
                self.lat, self.lon = self.resolve_zip_to_latlon(self.zipcode)
            else:
                self.lat = os.getenv("WEATHER_LAT", "37.7749")
                self.lon = os.getenv("WEATHER_LON", "-122.4194")

            self.alert_endpoint = f"https://api.weather.gov/alerts/active?point={self.lat},{self.lon}"
            self.last_alert_ids = set()

        except Exception as e:
            self.log("Failed to initialize config", error=e)

    def pre_boot(self):
        self.log("Pre-boot weather alert initialization complete.")

    def post_boot(self):
        self.log("Agent is live and scanning the sky.")
        self.log("╔════════════════════════════════════════════════╗")
        self.log("║ 🤡 CAPTAIN HOWDY IS WATCHING THE WEATHER       ║")
        self.log("║ 🛰️  StormCrow is deployed. Sky tracking is HOT ║")
        self.log("║ 🧠 Reflexes armed. Sirens ready.               ║")
        self.log("╚════════════════════════════════════════════════╝")

    def worker(self, config: dict = None, identity:IdentityObject = None):
        try:

            if config and isinstance(config, dict):

                self.log(f"config loaded: {config}")
                self._private_config = config
                self.log("[WORKER] 🔁 Full config applied.")
                self._initialized_from_tree = False

            if not self._initialized_from_tree:
                self.cmd_update_agent_config()


            alerts = self.fetch_alerts()
            if not alerts:
                self.log("[STORMCROW] ✅ NWS returned no alerts.")
            for item in alerts:
                alert_id = item.get("id")
                props = item.get("properties", {})
                event = props.get("event")
                severity = props.get("severity")
                area = props.get("areaDesc")
                headline = props.get("headline")
                issued = props.get("sent")
                description = props.get("description", "")
                instruction = props.get("instruction", "")

                msg = f"{event} | {severity} | {area}\n📰 {headline}\n"
                if description:
                    msg += f"📖 {description}\n"
                if instruction:
                    msg += f"📢 {instruction}\n"
                msg += f"📅 Issued: {issued}"

                if alert_id not in self.last_alert_ids:
                    self.last_alert_ids.add(alert_id)
                    msg = f"{event} | {severity} | {area}\n📰 {headline}\n📅 Issued: {issued}"
                    self.log(f"[STORMCROW] ⚠️ NEW ALERT: {event} | {severity} | {area}")
                    self.log(f"[STORMCROW] 📰 {headline} (Issued: {issued})")
                    self.alert_operator(event, msg)

            interruptible_sleep(self, 900)

        except Exception as e:
            self.log(error=e, block="main_try")
            interruptible_sleep(self, 60)


    def fetch_alerts(self):
        try:
            resp = requests.get(self.alert_endpoint, headers={"User-Agent": "StormCrow-Agent"}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features")
            if not isinstance(features, list):
                self.log(f"Unexpected response shape: {data}")
                return []
            return features
        except requests.exceptions.RequestException as e:
            self.log(error=e, block="main_try")

        except Exception as e:
            self.log(error=e, block="main_try")

        return []

    def alert_operator(self, title, message):
        pk1 = self.get_delivery_packet("standard.command.packet")
        pk1.set_data({"handler": "cmd_send_alert_msg"})

        try:
            server_ip = requests.get("https://api.ipify.org").text.strip()
        except Exception:
            server_ip = "Unknown"

        pk2 = self.get_delivery_packet("notify.alert.general")
        pk2.set_data({
            "server_ip": server_ip,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "universal_id": self.command_line_args.get("universal_id", "unknown"),
            "level": "warning",
            "msg": message,
            "formatted_msg": f"🌩 {title}\n{message}",
            "cause": "StormCrow Severe Weather Alert",
            "origin": self.command_line_args.get("universal_id", "unknown")
        })

        pk1.set_packet(pk2, "content")

        alert_nodes = self.get_nodes_by_role("hive.alert.send_alert_msg")
        if not alert_nodes:
            self.log("No alert-compatible agents found.")
            return

        for node in alert_nodes:
            self.pass_packet(pk1, node["universal_id"])

    def resolve_zip_to_latlon(self, zip_code):
        try:
            url = f"http://api.zippopotam.us/us/{zip_code}"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            coords = data["places"][0]
            lat = coords["latitude"]
            lon = coords["longitude"]
            self.log(f"[STORMCROW] ZIP {zip_code} resolved to {lat},{lon}")
            return lat, lon
        except Exception as e:
            self.log(f"Could not resolve ZIP {zip_code}", error=e, block="main_try")
            return os.getenv("WEATHER_LAT", "37.7749"), os.getenv("WEATHER_LON", "-122.4194")

    def worker_post(self):
        self.log("[STORMCROW] Worker loop scanning for severe weather alerts...")




if __name__ == "__main__":
    agent = Agent()
    agent.boot()
