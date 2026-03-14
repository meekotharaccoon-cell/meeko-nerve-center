import json
import webbrowser
import os
from datetime import datetime

print(" REAL HUMANITARIAN CRYPTO DONATION SYSTEM")
print("="*60)

# CRITICAL FIX: Use utf-8-sig to handle ANY BOM
with open("crisis_wallets.json", "r", encoding="utf-8-sig") as f:
    wallets = json.load(f)

print("\n GAZA: UNRWA USA (Bitcoin)")
print("    UNRWA USA accepts crypto via The Giving Block")
webbrowser.open("https://www.unrwausa.org/crypto")
print("    Opened - Send Bitcoin to Gaza refugees")

print("\n SUDAN: UNHCR (Bitcoin/Ethereum)")
webbrowser.open_new_tab("https://givingblock.com/nonprofit/unhcr")
print("    Opened - Send crypto to Sudan refugees")

print("\n CONGO: UNICEF (Bitcoin/Ethereum)")
webbrowser.open_new_tab("https://www.unicef.org/donate/crypto")
print("    Opened - Send crypto to Congo refugees")

print("\n" + "="*60)
print(" REAL DONATION PATHS OPENED")
print(" Your Amazon tag: autonomoushum-20")
print("="*60)

# Log it
os.makedirs("humanitarian_logs", exist_ok=True)
with open("humanitarian_logs/crypto_ready.json", "w") as f:
    json.dump({"timestamp": str(datetime.now()), "status": "ready"}, f)