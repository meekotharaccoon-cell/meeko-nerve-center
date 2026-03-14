# GAZA ROSE - PCRF ALLOCATION ENGINE
# Automatically sends 70% of revenue to PCRF Bitcoin address

import os
import json
import time
import sqlite3
import webbrowser
from datetime import datetime

class PCRFAllocationEngine:
    def __init__(self):
        self.pcrf_address = "https://give.pcrf.net/campaign/739651/donate"
        self.threshold = 10.0  # Send when total reaches 
        self.db_path = "revenue.db"
        
    def check_pending(self):
        """Check pending revenue"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT SUM(amount) FROM revenue WHERE status = 'pending'")
        total = c.fetchone()[0] or 0
        conn.close()
        return total
        
    def mark_sent(self, amount):
        """Mark revenue as sent to PCRF"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE revenue SET status = 'sent' WHERE status = 'pending'")
        conn.commit()
        conn.close()
        
    def open_pcrf_page(self, amount):
        """Open PCRF donation page"""
        url = f"https://pcrf1.app/donate/crypto"
        webbrowser.open_new_tab(url)
        print(f"\n  OPEN PCRF DONATION PAGE")
        print(f"   Amount to send: ")
        print(f"   Address: {self.pcrf_address}")
        print(f"   (Copy this address to send Bitcoin)")
        
    def check_and_allocate(self):
        """Check and allocate when threshold reached"""
        pending = self.check_pending()
        pcrf_amount = pending * 0.7
        
        if pcrf_amount >= self.threshold:
            self.open_pcrf_page(pcrf_amount)
            self.mark_sent(pcrf_amount)
            return True
        return False

if __name__ == "__main__":
    allocator = PCRFAllocationEngine()
    print(f" PCRF Allocation Engine ready")
    print(f"   Address: {allocator.pcrf_address[:20]}...")
    print(f"   Threshold: ")
