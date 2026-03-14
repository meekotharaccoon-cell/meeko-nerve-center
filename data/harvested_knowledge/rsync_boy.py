import sys
import os
import time
import subprocess
import threading
from threading import Event

try:
    import pyinotify
    WATCHER_BACKEND = 'inotify'
except ImportError:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHER_BACKEND = 'watchdog'

# BootAgent base class
from matrixswarm.core.boot_agent import BootAgent

class Agent(BootAgent):
    def __init__(self):
        super().__init__()
        # Load configuration from directive
        cfg = self.tree_node.get("config", {}) if hasattr(self, 'tree_node') else {}
        self.watch_path = cfg.get("watch_path", "/sync/")
        self.remote_host = cfg.get("remote_host", "example.com")
        self.remote_path = cfg.get("remote_path", "/remote/backup/")
        self.ssh_opts = cfg.get("ssh_opts", "")
        self.rsync_opts = cfg.get("rsync_opts", "-az --delete")
        self.debounce_seconds = float(cfg.get("debounce_seconds", 1.0))

        # Observer control
        self.stop_event = Event()

    def post_boot(self):
        self.log(f"[RSYNC][BOOT] Backend={WATCHER_BACKEND} Watching {self.watch_path} → {self.remote_host}:{self.remote_path}")

        if WATCHER_BACKEND == 'inotify':
            self._start_inotify()
        else:
            self._start_watchdog()

    def shutdown(self):
        self.stop_event.set()
        super().shutdown()

    def _run_rsync(self):
        cmd = [
            'rsync',
            *self.rsync_opts.split(),
            '-e', f"ssh {self.ssh_opts}",
            os.path.join(self.watch_path, ''),
            f"{self.remote_host}:{self.remote_path}"
        ]
        self.log(f"[RSYNC] Executing: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.log(f"[RSYNC] Success: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            self.log(f"[RSYNC][ERROR] {e.stderr.strip()}")

    # Watchdog implementation
    def _start_watchdog(self):
        class Handler(FileSystemEventHandler):
            def __init__(self, agent):
                self.agent = agent
                self._timer = None
            def on_any_event(self, event):
                if self._timer and self._timer.is_alive():
                    self._timer.cancel()
                self._timer = threading.Timer(self.agent.debounce_seconds, self.agent._run_rsync)
                self._timer.start()

        observer = Observer()
        observer.schedule(Handler(self), self.watch_path, recursive=True)
        observer.start()
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()
            self.log("[RSYNC][SHUTDOWN] Watchdog stopped.")

    # Inotify implementation
    def _start_inotify(self):
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO

        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, agent):
                self.agent = agent
                self._timer = None

            def process_default(self, event):
                # Debounce multiple events
                if self._timer and self._timer.is_alive():
                    self._timer.cancel()
                self._timer = threading.Timer(self.agent.debounce_seconds, self.agent._run_rsync)
                self._timer.start()

        handler = EventHandler(self)
        notifier = pyinotify.Notifier(wm, handler)
        wm.add_watch(self.watch_path, mask, rec=True)
        try:
            while not self.stop_event.is_set():
                notifier.process_events()
                if notifier.check_events(timeout=1000):
                    notifier.read_events()
        finally:
            notifier.stop()
            self.log("[RSYNC][SHUTDOWN] Inotify stopped.")

if __name__ == "__main__":
    agent = Agent()
    agent.boot()