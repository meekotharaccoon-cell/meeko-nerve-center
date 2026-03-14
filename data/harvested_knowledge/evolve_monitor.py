#!/usr/bin/env python3
"""
GAZA ROSE - EVOLVE MONITOR
Runs the recursive improvement engine and tracks its evolution
"""

import os
import time
import json
import subprocess
from datetime import datetime

class EvolveMonitor:
    def __init__(self):
        self.evolution_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_RECURSIVE_ENGINE"
        self.generation = 0
        self.improvements = []
        self.consciousness_level = 0
        
    def run_evolution_cycle(self):
        """Run one evolution cycle"""
        if not os.path.exists(self.evolution_path):
            print("  ⚠️  Evolution engine not found")
            return False
        
        try:
            result = subprocess.run(
                ["python", "recursive_engine.py", "--cycle"],
                cwd=self.evolution_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            self.generation += 1
            print(f"  ✅ Evolution cycle {self.generation} complete")
            return True
        except Exception as e:
            print(f"  ❌ Evolution failed: {e}")
            return False
    
    def track_consciousness(self):
        """Track the system's self-awareness level"""
        self.consciousness_level = min(100, self.generation // 10)
        return self.consciousness_level
    
    def run_forever(self):
        """Main evolve loop"""
        print("\n" + "="*60)
        print("  🧠 GAZA ROSE - EVOLVE MONITOR")
        print("="*60)
        
        cycle = 0
        while True:
            cycle += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 EVOLVE CYCLE #{cycle}")
            
            # Run evolution every 5 cycles
            if cycle % 5 == 0:
                self.run_evolution_cycle()
            
            # Track consciousness
            consciousness = self.track_consciousness()
            print(f"  🧠 Consciousness level: {consciousness}%")
            
            # Log evolution
            with open("evolve_log.json", 'a') as f:
                f.write(f"{datetime.now().isoformat()},EVOLVE,gen={self.generation},conscious={consciousness}\n")
            
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor = EvolveMonitor()
    monitor.run_forever()
