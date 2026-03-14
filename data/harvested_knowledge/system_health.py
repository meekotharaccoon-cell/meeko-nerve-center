#Authored by Daniel F MacDonald and Gemini
import sys
import os
import psutil

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    """
    A config-driven MatrixSwarm agent that monitors system resources.
    It sends reports to the role defined in its configuration.
    """
    def __init__(self):
        """
        Initializes the agent and loads its configuration directly from the
        directive's tree_node, following the swarm's standard pattern.
        """
        super().__init__()
        self.name = "SystemHealthMonitor"

        # Get the agent's specific config dictionary from the global tree_node.
        config = self.tree_node.get("config", {})

        self.log("Initializing SystemHealthMonitor from directive config...")

        # Set attributes, using config values but keeping original defaults as fallbacks.
        self.mem_threshold = config.get("mem_threshold_percent", 95.0)
        self.cpu_threshold = config.get("cpu_threshold_percent", 90.0)
        self.disk_threshold = config.get("disk_threshold_percent", 95.0)
        self.check_interval_sec = config.get("check_interval_sec", 60)
        self.report_to_role = config.get("report_to_role", "hive.forensics.data_feed")
        self.report_handler = config.get("report_handler", "cmd_ingest_status_report")

        self.log(f"Monitoring configured: [Mem: {self.mem_threshold}%, CPU: {self.cpu_threshold}%, Disk: {self.disk_threshold}%]")
        self.log(f"Reporting to role '{self.report_to_role}' with handler '{self.report_handler}'")

    def send_status_report(self, service_name, status, severity, details):
        """Helper method to construct and send a status packet to the configured role."""
        pk_content = {
            "handler": self.report_handler,
            "content": {"source_agent": self.name, "service_name": service_name, "status": status, "details": details,
                        "severity": severity}
        }
        # Get destination nodes from the role defined in the config
        report_nodes = self.get_nodes_by_role(self.report_to_role)
        if not report_nodes:
            return

        pk = self.get_delivery_packet("standard.command.packet")
        pk.set_data(pk_content)
        for node in report_nodes:
            self.pass_packet(pk, node["universal_id"])
            self.log(f"Sent '{severity}' for '{service_name}' to role '{self.report_to_role}'", level="INFO")

        #if self.debug.is_enabled():
        #    self.log(f"Sent '{severity}' for '{service_name}' to role '{self.report_to_role}'", level="INFO")


    def worker(self, config: dict = None, identity: IdentityObject = None):
        """Main execution loop for the agent."""
        try:
            # Check Memory
            mem = psutil.virtual_memory()
            if mem.percent > self.mem_threshold:
                self.send_status_report("system.memory", "high_usage", "WARNING",
                                        f"Memory usage is critical: {mem.percent:.2f}%.")

            # Check CPU
            cpu = psutil.cpu_percent(interval=1)
            if cpu > self.cpu_threshold:
                self.send_status_report("system.cpu", "high_load", "WARNING", f"CPU load is critical: {cpu:.2f}%.")

            # Check Disk
            disk = psutil.disk_usage('/')
            if disk.percent > self.disk_threshold:
                self.send_status_report("system.disk", "low_space", "WARNING",
                                        f"Root disk space is critical: {disk.percent:.2f}% full.")
        except Exception as e:
            self.log(f"An error occurred while checking system resources: {e}", level="ERROR")

        interruptible_sleep(self, self.check_interval_sec)

if __name__ == "__main__":
    agent = Agent()
    agent.boot()