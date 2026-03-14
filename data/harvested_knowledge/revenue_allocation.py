#!/usr/bin/env python3
"""
GAZA ROSE - REVENUE ALLOCATION ENGINE
70% to PCRF, 30% reinvested in system growth
Based on autonomous economic principles [5][7]
"""

import os
import json
import time
import subprocess
from datetime import datetime

class RevenueAllocationEngine:
    """
    Allocates revenue according to rules:
        70% to PCRF Bitcoin address
        30% reinvested in system growth
    """
    
    def __init__(self):
        self.pcrf_address = "https://give.pcrf.net/campaign/739651/donate"
        self.allocation_log = []
        self.knowledge_graph_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_ECOSYSTEM\knowledge.db"
        
    def get_pending_revenue(self):
        """Get pending revenue from knowledge graph"""
        import sqlite3
        conn = sqlite3.connect(self.knowledge_graph_path)
        c = conn.cursor()
        
        c.execute("SELECT SUM(amount) FROM sales WHERE status = 'pending'")
        sales = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount) FROM affiliate WHERE status = 'pending'")
        affiliate = c.fetchone()[0] or 0
        
        conn.close()
        
        return sales + affiliate
    
    def mark_as_allocated(self):
        """Mark pending revenue as allocated"""
        import sqlite3
        conn = sqlite3.connect(self.knowledge_graph_path)
        c = conn.cursor()
        
        c.execute("UPDATE sales SET status = 'allocated' WHERE status = 'pending'")
        c.execute("UPDATE affiliate SET status = 'allocated' WHERE status = 'pending'")
        
        conn.commit()
        conn.close()
    
    def calculate_allocation(self, total):
        """Calculate 70/30 split"""
        pcrf_amount = total * 0.7
        reinvest_amount = total * 0.3
        return pcrf_amount, reinvest_amount
    
    def allocate(self):
        """Allocate pending revenue"""
        total = self.get_pending_revenue()
        
        if total < 1.0:
            return {"status": "insufficient", "total": total}
        
        pcrf, reinvest = self.calculate_allocation(total)
        
        allocation = {
            "timestamp": datetime.now().isoformat(),
            "total_revenue": total,
            "pcrf_amount": pcrf,
            "reinvest_amount": reinvest,
            "pcrf_address": self.pcrf_address,
            "status": "allocated"
        }
        
        self.allocation_log.append(allocation)
        
        # Mark as allocated
        self.mark_as_allocated()
        
        # Save log
        with open("allocation_log.json", "a") as f:
            f.write(json.dumps(allocation) + "\n")
        
        return allocation
    
    def run_forever(self):
        """Run allocation loop"""
        print("\n" + "="*60)
        print("   GAZA ROSE - REVENUE ALLOCATION ENGINE")
        print("="*60)
        print(f"  PCRF Address: {self.pcrf_address}")
        print(f"  Allocation: 70% PCRF / 30% Reinvest")
        print("="*60 + "\n")
        
        cycle = 0
        while True:
            cycle += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  ALLOCATION CYCLE #{cycle}")
            
            result = self.allocate()
            
            if result["status"] == "allocated":
                print(f"   Allocated ${result['total_revenue']:.2f}")
                print(f"    PCRF (70%): ${result['pcrf_amount']:.2f} to {result['pcrf_address']}")
                print(f"   Reinvest (30%): ${result['reinvest_amount']:.2f}")
            else:
                print(f"   Pending revenue: ${result['total']:.2f} (insufficient for allocation)")
            
            time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    allocator = RevenueAllocationEngine()
    allocator.run_forever()
