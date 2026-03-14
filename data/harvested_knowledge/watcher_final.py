#!/usr/bin/env python3
\"\"\"
GAZA ROSE - FINAL WATCHER
Watching Taproot for incoming Bitcoin.
Once detected, instructs user to move to Native Segwit.
\"\"\"

import requests
import time
import webbrowser
import pyperclip
from datetime import datetime

TAPROOT = "bc1ppmp8e7n8zlxzuafllpdjpdaxmfrrvr46r4jylg6pf38433m4f0ssjeqpah"
NATIVE_SEGWIT = "bc1qka74n62h3zk9mcv8v8xjtjtwehmnm24w3pfzzr"
PAYMENT_SERVER = "http://localhost:8006"

def check_balance():
    try:
        url = f"https://blockchain.info/q/addressbalance/{TAPROOT}"
        satoshis = int(requests.get(url, timeout=10).text)
        return satoshis / 100000000
    except:
        return 0

print("\n" + "="*60)
print("    FINAL WATCHER ACTIVATED")
print("="*60)
print(f"   Watching: {TAPROOT[:20]}...")
print(f"   Send to:  {NATIVE_SEGWIT[:20]}...")
print("   Waiting for Bitcoin to arrive in Taproot...")
print("="*60 + "\n")

balance = 0
while True:
    new_balance = check_balance()
    if new_balance > balance:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  BITCOIN DETECTED IN TAPROOT!")
        print(f"   Amount: {new_balance:.8f} BTC")
        print(f"\n    ACTION REQUIRED:")
        print(f"   1. Open Phantom  Collectibles tab")
        print(f"   2. Click SEND  Select Taproot address")
        print(f"   3. PASTE this Native Segwit address:")
        print(f"      {NATIVE_SEGWIT}")
        print(f"   4. Send ALL Bitcoin")
        print(f"   5. Wait 10-60 minutes for confirmation")
        print(f"   6. Run the CLOSE THE LOOP button\n")
        
        # Copy Native Segwit to clipboard
        pyperclip.copy(NATIVE_SEGWIT)
        print(f"    Native Segwit address COPIED to clipboard!")
        
        # Open Phantom
        webbrowser.open("https://phantom.app")
        
        balance = new_balance
    
    print(f"  [{datetime.now().strftime('%H:%M:%S')}]  Taproot balance: {balance:.8f} BTC", end='\r')
    time.sleep(15)
