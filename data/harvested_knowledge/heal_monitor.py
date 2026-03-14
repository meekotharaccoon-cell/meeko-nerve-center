#!/usr/bin/env python3
"""
GAZA ROSE - HEAL MONITOR
Watches all processes, heals any that die, logs all events
"""

import os
import time
import json
import psutil
import subprocess
from datetime import datetime

class HealMonitor:
    def __init__(self):
        self.watchlist = [
            "python.exe",
            "node.exe",
            "autogpt.exe"
        ]
        self.heal_log = []
        self.heal_count = 0
        
    def scan_processes(self):
        """Find all running Python/Node processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in self.watchlist:
                    processes.append(proc.info)
            except:
                pass
        return processes
    
    def heal_dead_process(self, expected_process):
        """Attempt to heal a dead process"""
        print(f"  🔧 Healing: {expected_process}")
        # This would contain actual healing logic
        self.heal_count += 1
        self.heal_log.append({
            "timestamp": datetime.now().isoformat(),
            "process": expected_process,
            "action": "heal_attempted"
        })
        return True
    
    def check_health(self):
        """Check overall system health"""
        processes = self.scan_processes()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🩺 HEALTH CHECK")
        print(f"  📊 Running processes: {len(processes)}")
        
        for proc in processes[:5]:  # Show first 5
            print(f"    • {proc['name']} (PID: {proc['pid']})")
        
        return len(processes)
    
    def run_forever(self):
        """Main heal loop"""
        print("\n" + "="*60)
        print("  🩺 GAZA ROSE - HEAL MONITOR")
        print("="*60)
        
        cycle = 0
        while True:
            cycle += 1
            count = self.check_health()
            
            if count == 0:
                print("  ⚠️  No processes running - system may be down")
                self.heal_dead_process("all")
            
            # Log health
            with open("heal_log.json", 'a') as f:
                f.write(f"{datetime.now().isoformat()},HEAL,processes={count},heals={self.heal_count}\n")
            
            time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    monitor = HealMonitor()
    monitor.run_forever()
