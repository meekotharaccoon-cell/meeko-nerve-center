# log_watcher.py
# Authored by Daniel F MacDonald and Gemini
import os
import sys

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import time
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    """
    A robust agent that tails a log file, parses new entries, and sends
    them as status reports to the swarm for real-time analysis.
    """

    def __init__(self):
        """Initializes the agent and its log watching configuration."""
        super().__init__()
        self.AGENT_VERSION = "1.0.0"

        config = self.tree_node.get("config", {})

        self.log_path = config.get("log_path")
        self.service_name = config.get("service_name", "generic.log")
        self.report_to_role = config.get("report_to_role", "hive.forensics.data_feed")

        # Rules for classifying log severity based on keywords
        self.severity_rules = config.get("severity_rules", {
            "CRITICAL": ["fatal", "critical", "segfault", "segmentation fault"],
            "WARNING": ["error", "warn", "warning", "denied", "failed"],
            "INFO": []  # Default
        })

        # State tracking for log rotation
        self._current_inode = None
        self._log_file = None

    def post_boot(self):
        self.log(f"{self.NAME} v{self.AGENT_VERSION} – your logs tell many secrets...")

    def worker_pre(self):
        self.log(f"Beginning to watch log file: {self.log_path}")
        self._open_log_file()


    def worker(self, config: dict = None, identity: IdentityObject = None):
        """
        Main worker loop that tails the log file and handles rotation.
        """
        try:
            if not self.log_path or not os.path.exists(self.log_path):
                self.log(f"Log path '{self.log_path}' is invalid or not found. Worker will idle.", level="ERROR")
                return

            try:
                # Check for log rotation
                if not self._is_file_still_valid():
                    self.log("Log rotation detected. Re-opening file handle.", level="INFO")
                    self._open_log_file()

                # Read new lines
                line = self._log_file.readline()
                if line:
                    self._process_line(line)
                else:
                    # If no new line, sleep briefly to avoid busy-waiting
                    interruptible_sleep(self, 1)  # CHANGED: Was 0.5, must be an integer

            except Exception as e:
                self.log("Error during log watch cycle.", error=e, level="ERROR")

            interruptible_sleep(self, 10)  # Longer sleep on error
        except Exception as e:
            self.log(error=e, block="main_try")

    def _open_log_file(self):
        """Opens or re-opens the log file and seeks to the end."""
        try:
            if self._log_file:
                self._log_file.close()

            self._log_file = open(self.log_path, 'r')
            self._current_inode = os.fstat(self._log_file.fileno()).st_ino
            self._log_file.seek(0, 2)  # Go to the end of the file

        except Exception as e:
            self.log(error=e, block="main_try")


    def _is_file_still_valid(self):
        """Checks if the log file has been rotated."""
        try:
            return os.stat(self.log_path).st_ino == self._current_inode
        except FileNotFoundError:
            return False

    def _process_line(self, line: str):
        """Parses a log line and sends it as a status report."""

        try:
            line = line.strip()
            if not line:
                return

            severity = "INFO"  # Default severity
            line_lower = line.lower()
            for level, keywords in self.severity_rules.items():
                if any(keyword in line_lower for keyword in keywords):
                    severity = level
                    break

            report = {
                "source_agent": self.command_line_args.get("universal_id"),
                "service_name": self.service_name,
                "status": "log_entry_detected",
                "severity": severity,
                "details": {
                    "timestamp": time.time(),
                    "log_line": line
                }
            }
            self._send_report(report)
        except Exception as e:
            self.log(error=e, block="main_try")

    def _send_report(self, report_content: dict):
        """Constructs and sends a status report packet."""
        try:
            report_nodes = self.get_nodes_by_role(self.report_to_role)
            if not report_nodes:
                return

            pk = self.get_delivery_packet("standard.command.packet")
            pk.set_data({
                "handler": "cmd_ingest_status_report",
                "content": report_content
            })

            for node in report_nodes:
                self.pass_packet(pk, node["universal_id"])

            if self.debug.is_enabled():
                self.log(f"Sent '{report_content['severity']}' log entry for '{self.service_name}'.")

        except Exception as e:
            self.log("Failed to send log report.", error=e, block="_send_report")


if __name__ == "__main__":
    agent = Agent()
    agent.boot()