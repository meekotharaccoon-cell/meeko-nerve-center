#!/usr/bin/env python3
"""
GAZA ROSE - LOOP CONNECTOR
Connects all autonomous loops into one ecosystem.
Based on multi-agent coordination [1][4][5][7]
"""

import os
import sys
import time
import json
import threading
import subprocess
from datetime import datetime

class LoopConnector:
    """
    Connects all loops:
        - Knowledge Graph (data)
        - Swarm Orchestrator (revenue)
        - Self-Healing (recovery)
        - Revenue Allocation (distribution)
        - Performance Analytics (metrics)
    """
    
    def __init__(self):
        self.loops = {}
        self.processes = {}
        self.threads = []
        self.start_time = datetime.now()
        
    def start_loop(self, name, script):
        """Start a loop in its own thread"""
        print(f"   Starting {name} loop...")
        
        def run_loop():
            while True:
                try:
                    proc = subprocess.Popen(
                        ["python", script],
                        cwd=os.path.dirname(__file__),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    self.processes[name] = proc
                    proc.wait()  # Wait for process to exit (shouldn't happen)
                except Exception as e:
                    print(f"   {name} loop error: {e}")
                time.sleep(5)  # Restart delay
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        self.threads.append(thread)
        self.loops[name] = {
            "script": script,
            "thread": thread,
            "process": None,
            "status": "starting"
        }
        print(f"   {name} loop started")
    
    def start_all(self):
        """Start all loops"""
        loops = [
            ("knowledge_graph", "knowledge_graph.py"),
            ("swarm_orchestrator", "swarm_orchestrator.py"),
            ("self_healing", "self_healing.py"),
            ("revenue_allocation", "revenue_allocation.py"),
            ("performance_analytics", "performance_analytics.py")
        ]
        
        for name, script in loops:
            self.start_loop(name, script)
            time.sleep(2)  # Stagger startup
    
    def status(self):
        """Get status of all loops"""
        status = {
            "uptime": str(datetime.now() - self.start_time),
            "loops": {}
        }
        
        for name, loop in self.loops.items():
            proc = self.processes.get(name)
            status["loops"][name] = {
                "running": proc is not None and proc.poll() is None,
                "script": loop["script"]
            }
        
        return status
    
    def run_forever(self):
        """Run the loop connector forever"""
        print("\n" + "="*60)
        print("   GAZA ROSE - LOOP CONNECTOR")
        print("="*60)
        print(f"  Connecting all autonomous loops")
        print(f"  Based on multi-agent coordination [1][4][5][7]")
        print("="*60 + "\n")
        
        self.start_all()
        
        print(f"\n ALL LOOPS STARTED:")
        for name in self.loops:
            print(f"   {name}")
        
        print(f"\n Use status() to check running loops")
        
        # Keep connector alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n Shutting down all loops...")
            for proc in self.processes.values():
                if proc:
                    proc.terminate()
            print(" All loops stopped.")

if __name__ == "__main__":
    connector = LoopConnector()
    connector.run_forever()
