# permissions_guardian.py
# Authored by Daniel F MacDonald and Gemini
# Refactored to include persistent, encrypted history and refined cron signals.
# ChatGPT added code enhancements.
import sys
import os

sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import stat
import json
import time
import base64
from Crypto.Cipher import AES

from matrixswarm.core.boot_agent import BootAgent
from matrixswarm.core.class_lib.packet_delivery.utility.encryption.utility.identity import IdentityObject

class Agent(BootAgent):
    """
    A mission-based agent that enforces file and directory permissions.

    This agent scans specified directory paths, checks the permissions of all
    files and subdirectories against a defined policy, and corrects any
    discrepancies. It maintains an encrypted history of all changes made.
    After a single run, it terminates itself, designed to be managed and
    re-activated by a parent 'cron_manager' agent.

    Attributes:
        targets (list): A list of dictionaries, where each dictionary defines
            a target path and the desired permissions for its files/dirs.
        log_only (bool): If True, the agent will only report permission
            discrepancies without making any changes to the filesystem.
        _state_path (str): The path to a private directory for storing agent state.
        _history_file_path (str): The full path to the encrypted scan history file.
    """
    def __init__(self):
        """
        Initializes the agent by loading its configuration from the directive.
        """
        super().__init__()
        config = self.tree_node.get("config", {})
        self.targets = config.get("targets", [])
        self.log_only = config.get("log_only", False)

        # Agent state for scan history (encrypted)
        self._state_path = os.path.join(self.path_resolution["comm_path_resolved"], ".state")
        os.makedirs(self._state_path, exist_ok=True)
        self._history_file_path = os.path.join(self._state_path, "scan_history.json.enc")

    def worker(self, config: dict = None, identity: IdentityObject = None):
        """
        The main operational logic for the agent's single-run mission.

        This method orchestrates the entire process: loading the past scan
        history, executing the new scan, saving the updated history, and
        finally dropping a 'mission.complete' receipt before shutting down.

        Args:
            config (dict, optional): Live configuration data. Not used by this agent.
            identity (IdentityObject, optional): Sender identity. Not used by this agent.
        """
        self.log("Permissions Guardian: starting scan.")
        scan_history = self._load_history()

        for target in self.targets:
            scan_history += self._scan_and_enforce(target)

        self._save_history(scan_history)
        self.log("Permissions scan complete. Dropping mission.complete receipt.")
        self._drop_mission_complete_receipt()
        self.log("Standing down for the parent to respawn (cron-style).")
        self.running = False  # Agent will exit after 1 pass

    def _get_aes_key(self, which="agent"):
        """
        Retrieves the raw bytes of either the agent's private key or the swarm key.

        Args:
            which (str): The key to retrieve, either "agent" or "swarm".

        Returns:
            bytes: The raw 32-byte AES key.
        """
        if which == "swarm":
            key_b64 = self.swarm_key
        else:
            key_b64 = self.private_key
        # Accept bytes (already decoded) or base64 string
        if isinstance(key_b64, bytes):
            return key_b64
        return base64.b64decode(key_b64)

    def _encrypt(self, data: bytes, which="agent") -> bytes:
        """
        Encrypts data using AES-GCM with the specified key.

        Args:
            data (bytes): The plaintext data to encrypt.
            which (str): The key to use for encryption ("agent" or "swarm").

        Returns:
            bytes: The encrypted data blob, containing nonce, tag, and ciphertext.
        """
        key = self._get_aes_key(which)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def _decrypt(self, data: bytes, which="agent") -> bytes:
        """
        Decrypts an AES-GCM encrypted data blob.

        Args:
            data (bytes): The encrypted blob (nonce + tag + ciphertext).
            which (str): The key to use for decryption ("agent" or "swarm").

        Returns:
            bytes: The original plaintext data.
        """
        key = self._get_aes_key(which)
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    def _load_history(self):
        """
        Loads and decrypts the scan history from the agent's state file.

        Returns:
            list: A list of dictionaries representing past scan events, or an
                  empty list if no history exists or decryption fails.
        """
        if not os.path.exists(self._history_file_path) or os.path.getsize(self._history_file_path) < 32:
            return []

        try:
            with open(self._history_file_path, "rb") as f:
                encrypted = f.read()
            return json.loads(self._decrypt(encrypted).decode('utf-8'))
        except Exception as e:
            self.log("History decrypt failed. Starting fresh.", error=e, level="WARNING")
            return []

    def _save_history(self, history):
        """
        Encrypts and saves the scan history to the agent's state file.

        Args:
            history (list): The list of scan events to save.
        """
        try:
            with open(self._history_file_path, "wb") as f:
                f.write(self._encrypt(json.dumps(history, indent=2).encode('utf-8')))
            self.log("Scan history saved and encrypted.")
        except Exception as e:
            self.log("Failed to save encrypted scan history.", error=e, level="ERROR")

    def _scan_and_enforce(self, target):
        """
        Scans a single target directory and enforces the defined permissions.

        Args:
            target (dict): A configuration dictionary for a single scan target.

        Returns:
            list: A list of log events generated during the scan.
        """
        path_key = target.get("path")
        if not path_key:
            self.log("No path key specified for target. Skipping.", level="WARNING")
            return []
        root_path = self.path_resolution.get(path_key, path_key)
        if not os.path.isdir(root_path):
            self.log(f"Root path {root_path} not found. Skipping.", level="WARNING")
            return []

        dir_mode = target.get("dir_mode", 0o755)
        file_mode = target.get("file_mode", 0o644)
        log_events = []

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Fix directories
            for d in dirnames:
                full_path = os.path.join(dirpath, d)
                log_events += self._check_and_set_perm(full_path, dir_mode)
            # Fix files
            for f in filenames:
                full_path = os.path.join(dirpath, f)
                log_events += self._check_and_set_perm(full_path, file_mode)

        return log_events

    def _check_and_set_perm(self, path, desired_mode):
        """
        Checks and, if necessary, corrects the permissions of a single file or directory.

        Args:
            path (str): The full path to the file or directory.
            desired_mode (int): The desired permission mode in octal (e.g., 0o755).

        Returns:
            list: A list containing a log event if a change was made, otherwise empty.
        """
        log_events = []
        try:
            current_mode = stat.S_IMODE(os.stat(path).st_mode)
            if current_mode != desired_mode:
                action = "chmod" if not self.log_only else "log_only"
                log_msg = f"{action.upper()} {path}: {oct(current_mode)} -> {oct(desired_mode)}"

                if self.debug.is_enabled():
                    self.log(log_msg)
                    log_events.append({
                        "timestamp": time.time(),
                        "path": path,
                        "previous_mode": oct(current_mode),
                        "enforced_mode": oct(desired_mode),
                        "action_taken": action
                    })
                    if not self.log_only:
                        os.chmod(path, desired_mode)

        except Exception as e:
            self.log(f"Could not process {path}", error=e, level="ERROR")
        return log_events

    def _drop_mission_complete_receipt(self):
        """
        Creates a 'mission.complete' file to signal successful task completion.

        This file acts as a signal to the parent 'cron_manager' agent,
        indicating that this run was successful and it is safe to schedule
        the next run after the specified interval.
        """
        receipt_path = os.path.join(self.path_resolution["comm_path_resolved"], "hello.moto", "mission.complete")
        with open(receipt_path, "w") as f:
            f.write(str(time.time()))

if __name__ == "__main__":
    agent = Agent()
    agent.boot()