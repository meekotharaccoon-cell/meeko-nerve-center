#!/usr/bin/env python3
"""
GAZA ROSE - REVENUE KNOWLEDGE GRAPH
Unified data layer for all revenue streams.
Based on Rox's system of record architecture [citation:1]
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class RevenueKnowledgeGraph:
    """
    Unified knowledge graph consolidating:
    - Art inventory (Then & Now Flora)
    - Platform sales (Pond5, Spreadshirt, RedBubble)
    - Affiliate revenue (Amazon tag: autonomoushum-20)
    - System performance (AutoGPT, monitors)
    - Opportunities (gaps, trends, suggestions)
    """
    
    def __init__(self):
        self.db_path = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_ECOSYSTEM\knowledge.db"
        self.init_database()
        
    def init_database(self):
        """Initialize the knowledge graph database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Art inventory
        c.execute('''CREATE TABLE IF NOT EXISTS art (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            collection TEXT,
            filename TEXT,
            created DATE,
            platforms TEXT,
            sales_count INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0,
            last_modified TIMESTAMP
        )''')
        
        # Platform sales
        c.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            art_id INTEGER,
            amount REAL,
            commission REAL,
            timestamp TIMESTAMP,
            status TEXT,
            FOREIGN KEY (art_id) REFERENCES art(id)
        )''')
        
        # Affiliate revenue (Amazon)
        c.execute('''CREATE TABLE IF NOT EXISTS affiliate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            tag TEXT DEFAULT 'autonomoushum-20',
            amount REAL,
            commission REAL,
            timestamp TIMESTAMP,
            status TEXT
        )''')
        
        # System performance
        c.execute('''CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT,
            metric TEXT,
            value REAL,
            unit TEXT,
            timestamp TIMESTAMP
        )''')
        
        # Opportunities (AI-suggested actions)
        c.execute('''CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            description TEXT,
            priority INTEGER,
            estimated_value REAL,
            status TEXT DEFAULT 'pending',
            created TIMESTAMP,
            executed TIMESTAMP
        )''')
        
        # Agent swarm coordination (for multi-agent systems [citation:5])
        c.execute('''CREATE TABLE IF NOT EXISTS agent_swarm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT,
            role TEXT,
            status TEXT,
            current_task TEXT,
            last_active TIMESTAMP,
            performance_score REAL
        )''')
        
        conn.commit()
        conn.close()
        print("   Knowledge graph initialized")
    
    def scan_art_folder(self):
        """Scan for new art and update inventory"""
        art_paths = [
            r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art",
            r"C:\Users\meeko\Desktop\GAZA_ROSE_ULTIMATE\art"
        ]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        for path in art_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(('.png', '.jpg', '.jpeg')):
                        # Check if already in database
                        c.execute("SELECT id FROM art WHERE filename = ?", (file,))
                        if not c.fetchone():
                            # Extract title from filename
                            title = os.path.splitext(file)[0].replace('_', ' ').replace('-', ' ')
                            collection = "Unknown"
                            if "gaza" in file.lower():
                                collection = "Gaza Rose"
                            elif "palestine" in file.lower():
                                collection = "Palestine"
                            elif "olive" in file.lower():
                                collection = "Olive Branch"
                            
                            c.execute('''INSERT INTO art 
                                        (title, collection, filename, created, platforms, last_modified)
                                        VALUES (?, ?, ?, ?, ?, ?)''',
                                    (title, collection, file, datetime.now().date(), 
                                     json.dumps([]), datetime.now()))
        
        conn.commit()
        conn.close()
        print("   Art inventory updated")
    
    def log_sale(self, platform, art_title, amount):
        """Log a sale event"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Find art_id
        c.execute("SELECT id FROM art WHERE title LIKE ?", (f"%{art_title}%",))
        art_result = c.fetchone()
        art_id = art_result[0] if art_result else None
        
        # Insert sale
        commission = amount * 0.3  # 30% commission (70% to PCRF)
        c.execute('''INSERT INTO sales (platform, art_id, amount, commission, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (platform, art_id, amount, commission, datetime.now(), "pending"))
        
        # Update art sales count
        if art_id:
            c.execute("UPDATE art SET sales_count = sales_count + 1, revenue = revenue + ? WHERE id = ?",
                     (amount, art_id))
        
        conn.commit()
        conn.close()
        print(f"   Sale logged: ${amount} on {platform}")
    
    def log_affiliate(self, source, amount):
        """Log affiliate revenue (Amazon tag)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        commission = amount * 0.3  # 30% commission
        c.execute('''INSERT INTO affiliate (source, tag, amount, commission, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (source, "autonomoushum-20", amount, commission, datetime.now(), "pending"))
        
        conn.commit()
        conn.close()
        print(f"   Affiliate logged: ${amount} from {source}")
    
    def record_performance(self, component, metric, value, unit):
        """Record system performance metric"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO performance (component, metric, value, unit, timestamp)
                    VALUES (?, ?, ?, ?, ?)''',
                 (component, metric, value, unit, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def generate_opportunity(self, opp_type, description, priority, estimated_value):
        """Generate AI-suggested revenue opportunity"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO opportunities (type, description, priority, estimated_value, created)
                    VALUES (?, ?, ?, ?, ?)''',
                 (opp_type, description, priority, estimated_value, datetime.now()))
        
        conn.commit()
        conn.close()
        print(f"   Opportunity generated: {description}")
    
    def get_revenue_summary(self):
        """Get complete revenue summary"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Total sales
        c.execute("SELECT SUM(amount) FROM sales WHERE status = 'pending'")
        pending_sales = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount) FROM affiliate WHERE status = 'pending'")
        pending_affiliate = c.fetchone()[0] or 0
        
        # Commission for PCRF (70%)
        total_pending = pending_sales + pending_affiliate
        pcrf_amount = total_pending * 0.7
        reinvest_amount = total_pending * 0.3
        
        conn.close()
        
        return {
            "pending_sales": pending_sales,
            "pending_affiliate": pending_affiliate,
            "total_pending": total_pending,
            "pcrf_amount": pcrf_amount,
            "reinvest_amount": reinvest_amount
        }
    
    def get_art_inventory(self):
        """Get current art inventory"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM art")
        total = c.fetchone()[0]
        
        c.execute("SELECT SUM(sales_count) FROM art")
        total_sales = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_art": total,
            "total_sales": total_sales
        }

if __name__ == "__main__":
    kg = RevenueKnowledgeGraph()
    kg.scan_art_folder()
    summary = kg.get_revenue_summary()
    inventory = kg.get_art_inventory()
    
    print(f"\n REVENUE KNOWLEDGE GRAPH SUMMARY:")
    print(f"    Art pieces: {inventory['total_art']}")
    print(f"   Pending revenue: ${summary['total_pending']:.2f}")
    print(f"    To PCRF (70%): ${summary['pcrf_amount']:.2f}")
    print(f"   To reinvest (30%): ${summary['reinvest_amount']:.2f}")
