#!/usr/bin/env python3
"""
GAZA ROSE - BUILD MONITOR
Tracks all your AI systems, keeps them running, logs their status
"""

import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

class BuildMonitor:
    def __init__(self):
        self.systems = {
            "autogpt": {
                "path": r"C:\Users\meeko\autogpt",
                "command": "python -m autogpt --agent gaza_rose_agent --continuous",
                "process": None,
                "status": "stopped"
            },
            "recursive_engine": {
                "path": r"C:\Users\meeko\Desktop\GAZA_ROSE_RECURSIVE_ENGINE",
                "command": "python recursive_engine.py",
                "process": None,
                "status": "stopped"
            },
            "self_healer": {
                "path": r"C:\Users\meeko\Desktop\GAZA_ROSE_HEALER",
                "command": "python master_healer.py",
                "process": None,
                "status": "stopped"
            },
            "evolution_engine": {
                "path": r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER",
                "command": "python master_orchestrator.py",
                "process": None,
                "status": "stopped"
            }
        }
        self.log_file = "build_log.json"
        
    def start_system(self, name, config):
        """Start a system if it exists"""
        if not os.path.exists(config["path"]):
            print(f"  ⚠️  {name} not found at {config['path']}")
            return False
        
        try:
            process = subprocess.Popen(
                config["command"],
                cwd=config["path"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            config["process"] = process
            config["status"] = "running"
            print(f"  ✅ Started {name} (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"  ❌ Failed to start {name}: {e}")
            return False
    
    def check_systems(self):
        """Check all systems and restart if dead"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 CHECKING SYSTEMS")
        
        for name, config in self.systems.items():
            if config["process"]:
                # Check if process is still alive
                poll = config["process"].poll()
                if poll is not None:
                    print(f"  ⚠️  {name} died (exit code: {poll}) - restarting")
                    self.start_system(name, config)
                else:
                    print(f"  ✅ {name} running (PID: {config['process'].pid})")
            else:
                print(f"  ⚠️  {name} not started - attempting start")
                self.start_system(name, config)
    
    def run_forever(self):
        """Main build loop"""
        print("\n" + "="*60)
        print("  🤖 GAZA ROSE - BUILD MONITOR")
        print("="*60)
        
        # Start all systems
        for name, config in self.systems.items():
            self.start_system(name, config)
            time.sleep(2)
        
        cycle = 0
        while True:
            cycle += 1
            self.check_systems()
            
            # Log status
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()},BUILD,cycle={cycle}\n")
            
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor = BuildMonitor()
    monitor.run_forever()
