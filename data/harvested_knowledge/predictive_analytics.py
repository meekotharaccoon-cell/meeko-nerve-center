"""
Predictive Analytics Subsystem for UltimateAI Master
Learns from system history to predict and optimize performance
"""
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master')
KNOWLEDGE = BASE / 'knowledge'
DB_PATH = BASE / 'master.db'

def load_knowledge_history():
    """Load all crew evolution recommendations"""
    entries = []
    for f in KNOWLEDGE.glob('crew_evolution_*.json'):
        with open(f) as fh:
            entries.append(json.load(fh))
    return entries

def analyze_system_patterns():
    """Analyze what the system has learned so far"""
    history = load_knowledge_history()
    print(f"\n=== PREDICTIVE ANALYTICS REPORT ===")
    print(f"Generated: {datetime.now()}")
    print(f"Knowledge entries analyzed: {len(history)}")

    if history:
        print("\n--- Evolution Recommendations Summary ---")
        for i, entry in enumerate(history):
            print(f"\n[{i+1}] {entry['timestamp']}")
            # Extract first 200 chars as summary
            content = entry.get('content', '')[:200]
            print(f"    {content}...")

    print("\n--- System Growth Metrics ---")
    knowledge_files = list(KNOWLEDGE.glob('*.json'))
    print(f"Total knowledge files: {len(knowledge_files)}")

    # Check Gaza Rose data
    gaza_db = BASE / 'gaza_rose.db'
    if gaza_db.exists():
        print(f"Gaza Rose database: ACTIVE")
        conn = sqlite3.connect(str(gaza_db))
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"Gaza Rose tables: {[t[0] for t in tables]}")
        conn.close()

    print("\n--- Next Recommended Actions ---")
    print("1. Add more data sources to improve predictions")
    print("2. Run evolution cycle daily to compound growth")
    print("3. Connect Gaza Rose revenue data to analytics")
    print("4. ACTION NEEDED FROM YOU: Add your Stripe/PayPal API keys")
    print("   to activate real revenue tracking")
    print("\n=== END REPORT ===\n")

    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'knowledge_entries': len(history),
        'knowledge_files': len(knowledge_files),
        'status': 'analytics_active'
    }
    report_path = KNOWLEDGE / f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report saved: {report_path}")

if __name__ == '__main__':
    analyze_system_patterns()
