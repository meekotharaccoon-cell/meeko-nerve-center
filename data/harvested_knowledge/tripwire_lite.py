# Authored by Daniel F MacDonald and ChatGPT aka The Generals
# Docstrings by Gemini
"""
A lightweight file system integrity monitor agent for the Matrix Swarm.

This script, 'TripwireLite', acts as a simple file integrity monitor. It uses the
'inotify' library to watch a configurable set of directories for any changes,
such as file creation, modification, or deletion. When an event is detected,
it logs the details, including the event type, the full path of the affected
file, and a timestamp. To prevent log spam, a cooldown mechanism is in place
for repeated events on the same file.
"""
import sys
import os

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import time
import inotify.adapters
from datetime import datetime
from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.utils.swarm_sleep import interruptible_sleep
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject


class Agent(BootAgent):
    """
    A file system monitoring agent that logs file creations, deletions, and modifications.

    Inherits from BootAgent and uses inotify to watch specified directories for
    changes. It is designed to be a lightweight 'tripwire' to detect unexpected
    file system activity.

    Attributes:
        name (str): The name of the agent, "TripwireLite".
        watch_paths (list): A list of relative directory paths to monitor.
        abs_watch_paths (list): A list of absolute paths derived from watch_paths.
        cooldown (int): The number of seconds to wait before logging a new event
                        for the same file path to prevent spam.
        last_seen (dict): A dictionary mapping file paths to the timestamp of their
                          last logged event.
    """
    def __init__(self):
        """Initializes the TripwireLite agent.

        Sets up the agent's name, reads the configuration to determine which
        paths to watch, resolves those paths to absolute paths, and initializes
        the event cooldown settings.
        """
        super().__init__()
        self.name = "TripwireLite"

        cfg = self.tree_node.get("config", {})
        self.watch_paths = cfg.get("watch_paths", [
            "agent", "core", "boot_directives", "matrix_gui", "https_certs", "socket_certs"
        ])

        self.abs_watch_paths = [
            path if os.path.isabs(path) else os.path.join(self.path_resolution["site_root_path"], path)
            for path in self.watch_paths
        ]
        self.cooldown = 60
        self.last_seen = {}

    def log_event(self, event_type, full_path):
        """Logs a file system event with a cooldown to prevent spam.

        If an event for a specific file path has occurred within the cooldown
        period, the new event is suppressed. Otherwise, it formats a message
        with the event details and logs it.

        Args:
            event_type (str): The type of file system event (e.g., 'IN_MODIFY').
            full_path (str): The absolute path to the file or directory that
                             triggered the event.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if time.time() - self.last_seen.get(full_path, 0) < self.cooldown:
            return  # suppress spam
        self.last_seen[full_path] = time.time()

        msg = (
            f"🧪 Tripwire Event\n"
            f"• Path: {full_path}\n"
            f"• Event: {event_type}\n"
            f"• Time: {timestamp}"
        )
        self.log(f"[TRIPWIRE] {msg}")
        # self.alert_operator(message=msg)  # optional alert to Discord/etc.

    def worker(self, config: dict = None, identity: IdentityObject = None):
        """The main worker method that monitors file system events.

        This method sets up the inotify watches on the specified directories.
        It then enters an infinite loop, waiting for file system events. When
        an event is received, it extracts the details and passes them to the
        log_event method.

        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
            identity (IdentityObject, optional): Identity object for the agent.
                                                 Defaults to None.
        """
        i = inotify.adapters.Inotify()
        for path in self.abs_watch_paths:
            if os.path.exists(path):
                i.add_watch(path,
                            mask=inotify.constants.IN_MODIFY | inotify.constants.IN_CREATE | inotify.constants.IN_DELETE)
                self.log(f"[TRIPWIRE] Watching {path}")
            else:
                self.log(f"[TRIPWIRE][SKIP] Missing: {path}")

        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            full_path = os.path.join(path, filename)
            self.log_event(", ".join(type_names), full_path)

        interruptible_sleep(self, 10)


if __name__ == "__main__":
    """
    Main execution block to run the agent as a standalone script.

    Instantiates the Agent class and calls its boot() method to start
    the monitoring process.
    """
    agent = Agent()
    agent.boot()