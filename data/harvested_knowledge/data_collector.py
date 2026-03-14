#!/usr/bin/env python3
"""
GAZA ROSE - DATA COLLECTOR
Reads from all revenue systems and feeds WebSocket server
Based on Glances architecture [5] and Beszel collectors [2]
"""

import os
import sys
import json
import time
import sqlite3
import threading
import socket
from datetime import datetime, timedelta
from pathlib import Path

class DataCollector:
    """
    Collects data from all revenue systems:
        - Revenue Fabric (agents, generations, revenue)
        - Eternal System (daily revenue, pending)
        - Self-Healing logs (recovery events)
        - Growth metrics (projections, rates)
    """
    
    def __init__(self):
        self.data = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "revenue": {},
            "pcrf": {},
            "health": {},
            "growth": {},
            "recent_agents": []
        }
        self.running = True
        self.collect_count = 0
        
    def collect_from_fabric(self):
        """Collect data from revenue fabric database"""
        fabric_db = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_FABRIC\fabric.db"
        if not os.path.exists(fabric_db):
            return
        
        try:
            conn = sqlite3.connect(fabric_db)
            c = conn.cursor()
            
            # Agent count
            c.execute("SELECT COUNT(*) FROM agents")
            self.data["agents"]["total"] = c.fetchone()[0] or 0
            
            # Revenue totals
            c.execute("SELECT SUM(amount) FROM revenue")
            self.data["revenue"]["fabric_total"] = c.fetchone()[0] or 0
            
            # PCRF totals
            c.execute("SELECT SUM(amount) FROM pcrf")
            self.data["pcrf"]["fabric_total"] = c.fetchone()[0] or 0
            
            # Recent agents (for display)
            c.execute("SELECT id, generation, total_revenue, children FROM agents ORDER BY created DESC LIMIT 20")
            self.data["recent_agents"] = []
            for row in c.fetchall():
                self.data["recent_agents"].append({
                    "id": row[0][:8] if row[0] else "unknown",
                    "generation": row[1] or 0,
                    "revenue": row[2] or 0,
                    "children": row[3] or 0
                })
            
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Fabric collection error: {e}")
    
    def collect_from_eternal(self):
        """Collect data from eternal revenue system"""
        eternal_db = r"C:\Users\meeko\Desktop\GAZA_ROSE_ETERNAL\revenue.db"
        if not os.path.exists(eternal_db):
            return
        
        try:
            conn = sqlite3.connect(eternal_db)
            c = conn.cursor()
            
            # Today's revenue
            c.execute("SELECT SUM(amount) FROM revenue WHERE date(timestamp) = date('now')")
            self.data["revenue"]["today"] = c.fetchone()[0] or 0
            
            # Total revenue
            c.execute("SELECT SUM(amount) FROM revenue")
            self.data["revenue"]["total"] = c.fetchone()[0] or 0
            
            # Pending revenue
            c.execute("SELECT SUM(amount) FROM revenue WHERE status = 'pending'")
            self.data["revenue"]["pending"] = c.fetchone()[0] or 0
            
            # PCRF from eternal
            c.execute("SELECT SUM(amount) FROM revenue WHERE status = 'sent'")
            self.data["pcrf"]["eternal_total"] = c.fetchone()[0] or 0
            
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Eternal collection error: {e}")
    
    def collect_from_heal_log(self):
        """Collect self-healing statistics"""
        heal_log = r"C:\Users\meeko\Desktop\GAZA_ROSE_ETERNAL\heal_log.json"
        if not os.path.exists(heal_log):
            return
        
        try:
            with open(heal_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    self.data["health"] = {
                        "heals": last.get("heals", 0),
                        "fails": last.get("fails", 0),
                        "processes": last.get("processes", {})
                    }
        except:
            pass
    
    def collect_from_fabric_stats(self):
        """Collect from fabric stats JSON"""
        fabric_stats = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_FABRIC\fabric_stats.json"
        if os.path.exists(fabric_stats):
            try:
                with open(fabric_stats, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        self.data["fabric"] = json.loads(lines[-1])
            except:
                pass
    
    def calculate_pcrf_total(self):
        """Calculate total PCRF donations"""
        pcrf_total = 0
        if "fabric_total" in self.data["pcrf"]:
            pcrf_total += self.data["pcrf"]["fabric_total"]
        if "eternal_total" in self.data["pcrf"]:
            pcrf_total += self.data["pcrf"]["eternal_total"]
        self.data["pcrf"]["total"] = pcrf_total
        self.data["pcrf"]["address"] = "https://give.pcrf.net/campaign/739651/donate"
    
    def collect_all(self):
        """Run all collectors"""
        self.collect_count += 1
        self.data["timestamp"] = datetime.now().isoformat()
        
        self.collect_from_fabric()
        self.collect_from_eternal()
        self.collect_from_heal_log()
        self.collect_from_fabric_stats()
        self.calculate_pcrf_total()
        
        return self.data
    
    def run_forever(self):
        """Continuous collection loop"""
        print(f"\n  ✅ Data Collector started - reading from all revenue systems")
        while self.running:
            self.collect_all()
            time.sleep(2)  # Match WebSocket update rate [6]

if __name__ == "__main__":
    collector = DataCollector()
    
    # Run once for testing
    data = collector.collect_all()
    print(json.dumps(data, indent=2))
