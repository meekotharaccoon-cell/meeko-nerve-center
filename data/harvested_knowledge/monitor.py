# SOLARPUNK MONITORING DASHBOARD - NO DEPENDENCIES
# Save as: monitor.py
# Run: python monitor.py

import json
import time
import os
from datetime import datetime

class SolarPunkMonitor:
    def __init__(self):
        self.nodes = {
            "github": {"count": 30, "active": 0, "total_value": 3000},
            "browser": {"count": 0, "active": 0, "total_value": 0},
            "cloud": {"count": 10, "active": 0, "total_value": 1000}
        }
        self.log_file = "solarpunk_monitor.log"
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        print("=" * 70)
        print("🌐 SOLARPUNK NETWORK MONITOR".center(70))
        print("=" * 70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"OS: Windows (detected)")
        print("=" * 70)
    
    def update_browser_nodes(self):
        self.nodes["browser"]["count"] = min(100, self.nodes["browser"]["count"] + 1)
        self.nodes["browser"]["total_value"] = self.nodes["browser"]["count"] * 100
    
    def calculate_growth(self):
        growth_rate = 0.005 / 1440
        for node_type in self.nodes:
            if self.nodes[node_type]["count"] > 0:
                self.nodes[node_type]["total_value"] *= (1 + growth_rate)
    
    def print_dashboard(self):
        print("\n" + "📊 NODE NETWORK STATUS".center(70))
        print("-" * 70)
        
        total_nodes = 0
        total_value = 0
        
        for node_type, data in self.nodes.items():
            emoji = {"github": "📁", "browser": "🌐", "cloud": "☁️"}[node_type]
            nodes = data["count"]
            value = data["total_value"]
            
            total_nodes += nodes
            total_value += value
            
            print(f"{emoji} {node_type.upper():10} Nodes: {nodes:4} | Value: ${value:10,.2f}")
        
        print("-" * 70)
        print(f"💰 TOTAL: {total_nodes:4} nodes | ${total_value:,.2f}")
        print(f"🕊️  Humanitarian: ${total_value * 0.5:,.2f}")
        print(f"👥 UBI: ${total_value * 0.5:,.2f}")
        
        daily_growth = total_value * 0.005
        monthly = total_value * ((1.005 ** 30) - 1)
        yearly = total_value * ((1.005 ** 365) - 1)
        three_year = total_value * ((1.005 ** 1095) - 1)
        
        print("\n" + "📈 PROJECTIONS".center(70))
        print("-" * 70)
        print(f"Daily growth:   ${daily_growth:,.2f}")
        print(f"Monthly (30d):  ${monthly:,.2f}")
        print(f"Yearly:         ${yearly:,.2f}")
        print(f"3-year total:   ${three_year + total_value:,.2f}")
        
        print("\n" + "❤️  NETWORK HEALTH".center(70))
        print("-" * 70)
        
        if total_nodes >= 140:
            status = "🟢 OPTIMAL"
            message = "Full digital network operational"
        elif total_nodes >= 50:
            status = "🟡 GROWING"
            message = "Building network capacity"
        else:
            status = "🔴 INITIALIZING"
            message = "Need more nodes deployed"
        
        print(f"Status: {status}")
        print(f"Message: {message}")
        print(f"Next milestone: {max(0, 140 - total_nodes)} nodes to reach optimal")
    
    def log_status(self):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "nodes": self.nodes,
            "total_value": sum(data["total_value"] for data in self.nodes.values()),
            "humanitarian": sum(data["total_value"] for data in self.nodes.values()) * 0.5
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def run(self):
        print("Starting SolarPunk Monitor...")
        print("Press Ctrl+C to exit\n")
        
        try:
            while True:
                self.clear_screen()
                self.print_header()
                self.update_browser_nodes()
                self.calculate_growth()
                self.print_dashboard()
                self.log_status()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped. Logs saved to:", self.log_file)

def main():
    os.makedirs("logs", exist_ok=True)
    
    monitor = SolarPunkMonitor()
    monitor.run()

if __name__ == "__main__":
    main()