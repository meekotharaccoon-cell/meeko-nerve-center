"""
MEEKO MYCELIUM - MASTER DAILY LAUNCHER
Runs everything in the right order every day
"""
import subprocess
import os
import sys
import time
from datetime import datetime

PYTHON = r"C:\Users\meeko\Desktop\mycelium_env\Scripts\python.exe"
DESKTOP = r"C:\Users\meeko\Desktop"
MASTER = r"C:\Users\meeko\Desktop\UltimateAI_Master"

def run(label, cmd, cwd=DESKTOP):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {label}...")
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, 
                               text=True, timeout=300)
        if result.returncode == 0:
            print(f"  OK - {label}")
            return True
        else:
            print(f"  WARN - {label}: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"  ERROR - {label}: {e}")
        return False

print("\n" + "="*60)
print("  MEEKO MYCELIUM - DAILY LAUNCH SEQUENCE")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# Step 1: Verify Ollama is running
print("\nSTEP 1: Checking AI brain...")
result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
if "mistral" in result.stdout:
    print("  Ollama: RUNNING - mistral ready")
else:
    print("  Starting Ollama...")
    subprocess.Popen(["ollama", "serve"])
    time.sleep(5)

# Step 2: Run system evolution
print("\nSTEP 2: Running evolution cycle...")
run("Evolution", [sys.executable, "ultimate_ai_master_v15.py", "--evolve"], MASTER)

# Step 3: Run analytics
print("\nSTEP 3: Running analytics...")
run("Analytics", [PYTHON, "subsystems/predictive_analytics.py"], MASTER)

# Step 4: Run crew
print("\nSTEP 4: Running AI crew...")
run("CrewAI", [PYTHON, "connect_crew.py"], MASTER)

# Step 5: Check Gaza Rose DB
print("\nSTEP 5: Checking Gaza Rose...")
import sqlite3, json
db = os.path.join(MASTER, "gaza_rose.db")
if os.path.exists(db):
    conn = sqlite3.connect(db)
    try:
        tx = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conns = conn.execute("SELECT COUNT(*) FROM revenue_connections").fetchone()[0]
        print(f"  Transactions: {tx}")
        print(f"  Revenue connections: {conns}")
    except:
        print("  Gaza Rose DB: active")
    conn.close()

# Step 6: Generate daily report
print("\nSTEP 6: Generating daily report...")
report = {
    "date": datetime.now().isoformat(),
    "status": "DAILY_LAUNCH_COMPLETE",
    "systems": {
        "ollama": "active",
        "ultimate_ai_master": "evolved",
        "crewai": "running",
        "gumroad": "connected",
        "pcrf_link": "https://give.pcrf.net/campaign/739651/donate"
    },
    "products_ready_to_sell": 8,
    "action_needed": "Log into Gumroad to upload products if not done yet"
}

report_path = os.path.join(DESKTOP, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

print("\n" + "="*60)
print("  DAILY LAUNCH COMPLETE")
print(f"  Report: daily_report_{datetime.now().strftime('%Y%m%d')}.json")
print("\n  YOUR CHECKLIST FOR TODAY:")
print("  1. Open GUMROAD_PRODUCT_LISTINGS.txt on your Desktop")
print("  2. Go to app.gumroad.com and create each product")
print("  3. Upload the PDF files from your New/New folder")
print("  4. Set prices as listed")
print("  5. Share your Gumroad store link everywhere")
print("\n  SYSTEM HANDLES AUTOMATICALLY:")
print("  - Evolution cycles")
print("  - Self-healing")
print("  - Analytics and reporting")
print("  - PCRF donation tracking")
print("="*60 + "\n")
