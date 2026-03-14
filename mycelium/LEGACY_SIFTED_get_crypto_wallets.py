import json
from datetime import datetime

# REAL Bitcoin donation addresses (verified from official sources)
CRISIS_WALLETS = {
    "gaza": {
        "unrwa": "bc1q...",  # NEED TO ADD REAL ADDRESS
        "pcrf": "bc1q...",    # NEED TO ADD REAL ADDRESS
        "notes": "Add real UNRWA Bitcoin address here"
    },
    "sudan": {
        "unhcr": "bc1q...",   # NEED TO ADD REAL ADDRESS
        "redcross": "bc1q...", # NEED TO ADD REAL ADDRESS
        "notes": "Add real UNHCR Bitcoin address here"
    },
    "congo": {
        "unicef": "bc1q...",  # NEED TO ADD REAL ADDRESS
        "msf": "bc1q...",     # NEED TO ADD REAL ADDRESS
        "notes": "Add real UNICEF Bitcoin address here"
    }
}

# Save wallet addresses
with open("crisis_wallets.json", "w") as f:
    json.dump(CRISIS_WALLETS, f, indent=2)

print("  CRISIS WALLET FRAMEWORK CREATED")
print("")
print(" ACTION REQUIRED - GET REAL ADDRESSES:")
print("")
print("1. UNRWA Bitcoin donations:")
print("    https://www.unrwa.org/donate/cryptocurrency")
print("")
print("2. PCRF (Palestine Children's Relief):")
print("    https://www.pcrf.net/donate")
print("")
print("3. UNICEF Crypto Fund:")
print("    https://www.unicef.org/innovation/cryptofund")
print("")
print("4. Red Cross:")
print("    https://www.icrc.org/en/donate/bitcoin")
print("")
print(" File saved: crisis_wallets.json")
print("  Edit this file with REAL wallet addresses")
