"""
MEEKO MYCELIUM - CRYPTO REVENUE CONNECTOR
Connects Coinbase Commerce (customer payments) + Coinbase Advanced Trade (account) + Phantom/Solana wallet
Replaces Stripe + PayPal entirely. Keys entered at runtime - never saved.

HOW IT WORKS:
  - Coinbase Commerce: Customers pay you in BTC/ETH/USDC/SOL — you get the money
  - Coinbase Advanced Trade: Read your Coinbase account balances and history
  - Phantom (Solana): Accept SOL/USDC directly to your wallet — zero fees, instant
  - Gaza Rose DB: All connection status and revenue tracked automatically
  - PCRF: 70% of revenue you manually send via https://give.pcrf.net/campaign/739651/donate
          (PCRF does not accept crypto directly — fiat only — so you convert then donate)
"""

import getpass
import sqlite3
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')
PCRF_LINK = "https://give.pcrf.net/campaign/739651/donate"

print("\n" + "="*60)
print("  MEEKO MYCELIUM - CRYPTO REVENUE CONNECTOR")
print("="*60)
print("\nAll keys used this session only - NEVER written to disk.")
print("Press ENTER to skip any you want to set up later.\n")

# ── GET CREDENTIALS ────────────────────────────────────────
print("-- COINBASE COMMERCE (accept payments from customers) --")
print("Get this at: commerce.coinbase.com -> Settings -> API Keys")
commerce_key = getpass.getpass("Coinbase Commerce API Key: ").strip()

print("\n-- COINBASE ADVANCED TRADE (read your account balances) --")
print("Get this at: coinbase.com -> Settings -> API -> New API Key")
print("Create with: View permissions only (read-only is safest)")
cb_api_key    = getpass.getpass("Coinbase API Key Name (starts with 'organizations/...'): ").strip()
cb_api_secret = getpass.getpass("Coinbase API Private Key (paste full key including -----BEGIN EC...): ").strip()

print("\n-- PHANTOM WALLET (Solana address for direct payments) --")
print("Open Phantom in Brave -> click your account name -> copy address")
print("This is your PUBLIC address - safe to share with customers")
phantom_address = input("Your Phantom Solana Address: ").strip()

results = {}

# ── 1. COINBASE COMMERCE ───────────────────────────────────
if commerce_key:
    print("\n[1/3] Testing Coinbase Commerce...")
    try:
        req = urllib.request.Request(
            'https://api.commerce.coinbase.com/checkouts',
            headers={
                'X-CC-Api-Key': commerce_key,
                'X-CC-Version': '2018-03-22',
                'Content-Type': 'application/json'
            }
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        count = len(data.get('data', []))
        print(f"  CONNECTED - {count} existing checkouts found")
        results['coinbase_commerce'] = {
            'status': 'connected',
            'checkouts': count,
            'note': 'Accept BTC, ETH, USDC, SOL, DOGE from customers'
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERROR: {e.code} - {body[:200]}")
        results['coinbase_commerce'] = {'status': 'error', 'detail': f"HTTP {e.code}: {body[:100]}"}
    except Exception as e:
        print(f"  ERROR: {e}")
        results['coinbase_commerce'] = {'status': 'error', 'detail': str(e)}
else:
    print("\n[1/3] Coinbase Commerce skipped")

# ── 2. COINBASE ADVANCED TRADE ─────────────────────────────
if cb_api_key and cb_api_secret:
    print("\n[2/3] Testing Coinbase Advanced Trade...")
    try:
        from coinbase.rest import RESTClient
        client = RESTClient(api_key=cb_api_key, api_secret=cb_api_secret)
        accounts = client.get_accounts()
        acct_list = accounts.accounts if hasattr(accounts, 'accounts') else []
        # Filter accounts with balances
        with_balance = [
            a for a in acct_list
            if float(getattr(getattr(a, 'available_balance', None), 'value', 0) or 0) > 0
        ]
        print(f"  CONNECTED - {len(acct_list)} accounts, {len(with_balance)} with balance")
        balances = {}
        for a in with_balance:
            currency = getattr(a, 'currency', '?')
            value = getattr(getattr(a, 'available_balance', None), 'value', '0')
            balances[currency] = value
            print(f"    {currency}: {value}")
        results['coinbase_advanced'] = {
            'status': 'connected',
            'accounts': len(acct_list),
            'balances': balances
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        results['coinbase_advanced'] = {'status': 'error', 'detail': str(e)}
else:
    print("\n[2/3] Coinbase Advanced Trade skipped")

# ── 3. PHANTOM / SOLANA ────────────────────────────────────
if phantom_address:
    print("\n[3/3] Checking Phantom wallet on Solana mainnet...")
    try:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [phantom_address]
        }).encode()
        req = urllib.request.Request(
            'https://api.mainnet-beta.solana.com',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        lamports = data.get('result', {}).get('value', 0)
        sol_balance = lamports / 1_000_000_000
        print(f"  CONNECTED - Wallet balance: {sol_balance:.6f} SOL")
        print(f"  Address: {phantom_address[:8]}...{phantom_address[-6:]}")

        # Also check USDC balance on Solana
        # USDC token mint on Solana mainnet
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        usdc_req = urllib.request.Request(
            'https://api.mainnet-beta.solana.com',
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    phantom_address,
                    {"mint": usdc_mint},
                    {"encoding": "jsonParsed"}
                ]
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        usdc_resp = urllib.request.urlopen(usdc_req, timeout=15)
        usdc_data = json.loads(usdc_resp.read())
        usdc_accounts = usdc_data.get('result', {}).get('value', [])
        usdc_balance = 0
        for acct in usdc_accounts:
            amount = acct.get('account', {}).get('data', {}).get('parsed', {}).get('info', {}).get('tokenAmount', {}).get('uiAmount', 0)
            usdc_balance += amount or 0
        print(f"  USDC Balance: ${usdc_balance:.2f}")

        results['phantom_solana'] = {
            'status': 'connected',
            'address': phantom_address,
            'sol_balance': sol_balance,
            'usdc_balance': usdc_balance,
            'note': 'Customers can send SOL or USDC directly to this address — zero fees'
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        results['phantom_solana'] = {'status': 'error', 'address': phantom_address, 'detail': str(e)}
else:
    print("\n[3/3] Phantom wallet skipped")

# ── SAVE STATUS TO GAZA ROSE DB ───────────────────────────
if results:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS crypto_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        platform TEXT,
        status TEXT,
        details TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS crypto_config (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated TEXT
    )''')

    for platform, data in results.items():
        conn.execute(
            'INSERT INTO crypto_connections VALUES (NULL, ?, ?, ?, ?)',
            (datetime.now().isoformat(), platform, data['status'],
             json.dumps({k: v for k, v in data.items() if k != 'key'}))
        )

    # Save phantom address (public - safe) for use by payment pages
    if phantom_address and results.get('phantom_solana', {}).get('status') == 'connected':
        conn.execute(
            'INSERT OR REPLACE INTO crypto_config VALUES (?, ?, ?)',
            ('phantom_address', phantom_address, datetime.now().isoformat())
        )
        print(f"\n  Phantom address saved to DB for payment pages")

    conn.commit()
    conn.close()
    print(f"\n  Connection status saved to Gaza Rose DB")

# ── FINAL SUMMARY ─────────────────────────────────────────
print("\n" + "="*60)
print("  CRYPTO CONNECTION SUMMARY")
print("="*60)
ok = [p for p, d in results.items() if d.get('status') == 'connected']
fail = [p for p, d in results.items() if d.get('status') != 'connected']

for platform, data in results.items():
    icon = "OK" if data.get('status') == 'connected' else "FAIL"
    print(f"  [{icon}] {platform.upper()}: {data.get('status','?').upper()}")

print(f"\n  {len(ok)}/{len(results)} platforms connected")
print(f"\n  IMPORTANT - PCRF DONATION NOTE:")
print(f"  PCRF does not accept crypto directly.")
print(f"  When you earn crypto revenue:")
print(f"  1. Convert 70% to USD via Coinbase")
print(f"  2. Donate via: {PCRF_LINK}")
print(f"  Your system will track what you owe and remind you.")
print("="*60 + "\n")

# Write the payment addresses file for the gallery
if phantom_address:
    payment_config = {
        "updated": datetime.now().isoformat(),
        "phantom_solana": phantom_address,
        "pcrf_donation_link": PCRF_LINK,
        "pcrf_note": "PCRF accepts fiat only. Convert crypto, then donate at the link above.",
        "accepted_coins_via_phantom": ["SOL", "USDC"],
        "accepted_coins_via_coinbase_commerce": ["BTC", "ETH", "USDC", "SOL", "DOGE", "LTC"]
    }
    config_path = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\payment_config.json')
    with open(config_path, 'w') as f:
        json.dump(payment_config, f, indent=2)
    print(f"  Payment config written to gallery for payment page use.")
    print(f"  Run: python build_payment_page.py to update your gallery payment page.")
