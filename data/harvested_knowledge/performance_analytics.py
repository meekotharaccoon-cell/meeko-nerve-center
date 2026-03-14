#!/usr/bin/env python3
"""
GAZA ROSE - PERFORMANCE ANALYTICS
Tracks success rates, recovery times, revenue growth
Based on SelfHeal metrics [9] and HIVE MIND analytics [5]
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta

class PerformanceAnalytics:
    def __init__(self):
        self.db_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_ECOSYSTEM\knowledge.db"
        
    def get_success_rate(self, days=7):
        """Calculate success rate over period [9]"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get all performance entries
        c.execute('''SELECT value FROM performance 
                    WHERE timestamp > ? AND metric = 'success' ''', (cutoff,))
        successes = c.fetchall()
        
        c.execute('''SELECT value FROM performance 
                    WHERE timestamp > ? AND metric = 'failure' ''', (cutoff,))
        failures = c.fetchall()
        
        conn.close()
        
        total = len(successes) + len(failures)
        if total == 0:
            return 0
        
        return len(successes) / total
    
    def get_average_recovery_time(self, days=7):
        """Get average recovery time [9]"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT AVG(value) FROM performance 
                    WHERE timestamp > ? AND metric = 'recovery_time' ''', (cutoff,))
        result = c.fetchone()[0]
        
        conn.close()
        return result or 0
    
    def get_revenue_growth(self, days=30):
        """Calculate revenue growth rate"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT SUM(amount) FROM sales WHERE timestamp > ?''', (cutoff,))
        revenue = c.fetchone()[0] or 0
        
        conn.close()
        return revenue
    
    def get_swarm_performance(self):
        """Get average swarm performance [5]"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT AVG(performance_score) FROM agent_swarm''')
        avg_perf = c.fetchone()[0] or 0
        
        c.execute('''SELECT COUNT(*) FROM agent_swarm WHERE status = 'running' ''')
        active = c.fetchone()[0] or 0
        
        c.execute('''SELECT COUNT(*) FROM agent_swarm''')
        total = c.fetchone()[0] or 1
        
        conn.close()
        
        return {
            "avg_performance": avg_perf,
            "active_agents": active,
            "total_agents": total,
            "active_percentage": (active / total) * 100
        }
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        report = {
            "timestamp": str(datetime.now()),
            "success_rate_7d": self.get_success_rate(7),
            "success_rate_30d": self.get_success_rate(30),
            "avg_recovery_time": self.get_average_recovery_time(),
            "revenue_30d": self.get_revenue_growth(),
            "swarm": self.get_swarm_performance()
        }
        
        # Save report
        with open("performance_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_forever(self):
        """Run analytics loop"""
        print("\n" + "="*60)
        print("   GAZA ROSE - PERFORMANCE ANALYTICS")
        print("="*60)
        print("  Based on SelfHeal metrics [9] + HIVE MIND [5]")
        print("="*60 + "\n")
        
        while True:
            report = self.generate_report()
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  PERFORMANCE REPORT")
            print(f"  Success rate (7d): {report['success_rate_7d']:.2%}")
            print(f"  Success rate (30d): {report['success_rate_30d']:.2%}")
            print(f"  Avg recovery time: {report['avg_recovery_time']:.1f}s")
            print(f"  Revenue (30d): ${report['revenue_30d']:.2f}")
            print(f"  Swarm performance: {report['swarm']['avg_performance']:.2%}")
            print(f"  Active agents: {report['swarm']['active_agents']}/{report['swarm']['total_agents']}")
            
            time.sleep(600)  # Update every 10 minutes

if __name__ == "__main__":
    analytics = PerformanceAnalytics()
    analytics.run_forever()
