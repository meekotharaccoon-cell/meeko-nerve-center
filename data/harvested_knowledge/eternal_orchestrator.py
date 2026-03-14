# GAZA ROSE - ETERNAL ORCHESTRATOR [FIXED]
# Runs forever, heals itself, makes money

import os
import sys
import time
import json
import random
import threading
import subprocess
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

try:
    from revenue_core import RevenueCore
    from self_healing import SelfHealingEngine
    CORE_OK = True
except ImportError as e:
    CORE_OK = False
    print(f"Import warning: {e}")

class EternalOrchestrator:
    """
    The one loop to rule them all.
    Runs forever, heals itself, makes money.
    """
    
    def __init__(self):
        self.core = RevenueCore()
        self.healer = SelfHealingEngine()
        self.start_time = datetime.now()
        self.cycle = 0
        
        print("\n" + "="*60)
        print("   GAZA ROSE - ETERNAL ORCHESTRATOR")
        print("="*60)
        print(f"  Amazon tag: {self.core.amazon_tag}")
        print(f"  PCRF address: {self.core.pcrf_address[:20]}...")
        print("="*60 + "\n")
        
    def revenue_loop(self):
        """Main revenue generation loop [1]"""
        while True:
            try:
                # Generate revenue
                amount = self.core.generate_amazon_revenue()
                pcrf, reinvest = self.core.calculate_allocation(amount)
                
                # Update display
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  New revenue: ${amount:.2f}")
                print(f"    PCRF (70%): ${pcrf:.2f}")
                print(f"   Reinvest (30%): ${reinvest:.2f}")
                
                # Open platforms occasionally
                if random.random() < 0.1:  # 10% chance each cycle
                    self.core.open_platforms()
                    
            except Exception as e:
                print(f"   Revenue loop error: {e}")
                
            time.sleep(random.randint(300, 900))  # 5-15 minutes
            
    def healing_loop(self):
        """Self-healing loop [2]"""
        while True:
            self.healer.level1_watchdog()
            self.healer.level4_log()
            time.sleep(60)
            
    def reporting_loop(self):
        """Generate periodic reports"""
        while True:
            time.sleep(3600)  # Every hour
            stats = self.core.get_stats()
            print(f"\n HOURLY REPORT [{datetime.now().strftime('%H:%M:%S')}]")
            print(f"  Total revenue: ${stats['total_revenue']:.2f}")
            print(f"  PCRF total: ${stats['pcrf_total']:.2f}")
            print(f"  Reinvest total: ${stats['reinvest_total']:.2f}")
            
    def run_forever(self):
        """Launch all loops in parallel"""
        
        # Register processes with healer
        self.healer.register_process(
            "revenue_loop",
            [sys.executable, "-c", "from revenue_core import RevenueCore; import random; import time; c=RevenueCore(); while True: c.generate_amazon_revenue(); time.sleep(random.randint(300,900))"],
            os.path.dirname(__file__)
        )
        
        # Start all threads
        threads = [
            threading.Thread(target=self.revenue_loop, daemon=True),
            threading.Thread(target=self.healing_loop, daemon=True),
            threading.Thread(target=self.reporting_loop, daemon=True)
        ]
        
        for t in threads:
            t.start()
            
        print("\n ALL LOOPS STARTED - RUNNING FOREVER")
        print("   Press Ctrl+C to stop (but why would you?)")
        print("")
        
        try:
            while True:
                self.cycle += 1
                time.sleep(60)
                if self.cycle % 10 == 0:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  Heartbeat - {self.cycle} minutes")
        except KeyboardInterrupt:
            print("\n\n Eternal system paused")
            print(f"Uptime: {datetime.now() - self.start_time}")
            print(f"Total cycles: {self.cycle}")
            print("\nResume by running this script again.")

if __name__ == "__main__":
    if not CORE_OK:
        print(" Core modules not loaded - continuing anyway")
    orchestrator = EternalOrchestrator()
    orchestrator.run_forever()
