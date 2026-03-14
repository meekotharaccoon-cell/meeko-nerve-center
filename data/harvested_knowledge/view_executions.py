#!/usr/bin/env python3
"""
GAZA ROSE - EXECUTION LOG VIEWER
Shows what fixes were attempted and their success rate
"""

import json
import os
from datetime import datetime

HEALER_ROOT = r"C:\Users\meeko\Desktop\GAZA_ROSE_HEALER"
history_file = os.path.join(HEALER_ROOT, "execution_history.json")

print("\n" + "="*60)
print("  ⚡ GAZA ROSE - EXECUTION HISTORY")
print("="*60)

if os.path.exists(history_file):
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    print(f"\n📊 SUCCESS RATE: {history.get('success_rate', 0)*100:.1f}%")
    print(f"📈 TOTAL ATTEMPTS: {history.get('total_attempts', 0)}")
    print(f"\n🔄 RECENT EXECUTIONS:")
    
    for attempt in history.get('recent', [])[-10:]:  # Last 10
        status_color = "✅" if attempt['status'] == 'success' else "❌"
        print(f"\n  {status_color} [{attempt['timestamp'][:19]}] {attempt['system'][-30:]}")
        print(f"     Fix: {attempt['fix'][:100]}...")
        if attempt['status'] != 'success':
            print(f"     Error: {attempt.get('error', 'unknown')[:100]}")
else:
    print("\n⚠️  No execution history yet. Run the healer first.")

print("\n" + "="*60)
input("\nPress Enter to exit...")
