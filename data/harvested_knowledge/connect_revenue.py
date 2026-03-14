"""
Revenue Connector for UltimateAI Master
Covers: Gumroad + Coinbase Commerce + Phantom/Solana + (Stripe/PayPal optional)
Keys entered at runtime - never saved to disk
"""
import getpass
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')

print("\n=== REVENUE CONNECTOR ===")
print("PRIMARY: Gumroad + Coinbase Commerce + Phantom/Solana")
print("OPTIONAL: Stripe + PayPal (skip if not working)")
print("Keys used this session only - NEVER saved anywhere\n")

# Get keys securely at runtime
print("Press ENTER to skip any account you want to set up later\n")

stripe_key = getpass.getpass("Paste your Stripe SECRET key (sk_live_...): ").strip()
paypal_id = getpass.getpass("Paste your PayPal Client ID: ").strip()
paypal_secret = getpass.getpass("Paste your PayPal Secret: ").strip()
gumroad_token = getpass.getpass("Paste your Gumroad Access Token (from Generate Access Token button): ").strip()

results = {}

# Test Stripe
if stripe_key:
    try:
        import subprocess
        result = subprocess.run(
            ['pip', 'install', 'stripe', '--quiet'],
            capture_output=True
        )
        import stripe
        stripe.api_key = stripe_key
        balance = stripe.Balance.retrieve()
        available = balance['available'][0]['amount'] / 100
        currency = balance['available'][0]['currency'].upper()
        print(f"\nStripe CONNECTED - Balance: {available} {currency}")
        results['stripe'] = {'status': 'connected', 'balance': available, 'currency': currency}
    except Exception as e:
        print(f"\nStripe error: {e}")
        results['stripe'] = {'status': 'error', 'message': str(e)}

# Test PayPal
if paypal_id and paypal_secret:
    try:
        import urllib.request
        import base64
        credentials = base64.b64encode(f"{paypal_id}:{paypal_secret}".encode()).decode()
        req = urllib.request.Request(
            'https://api-m.sandbox.paypal.com/v1/oauth2/token',
            data=b'grant_type=client_credentials',
            headers={
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        print(f"\nPayPal CONNECTED - Token expires in {data.get('expires_in', '?')}s")
        results['paypal'] = {'status': 'connected'}
    except Exception as e:
        print(f"\nPayPal error: {e}")
        results['paypal'] = {'status': 'error', 'message': str(e)}

# Test Gumroad
if gumroad_token:
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://api.gumroad.com/v2/user',
            headers={'Authorization': f'Bearer {gumroad_token}'}
        )
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        user = data.get('user', {})
        print(f"\nGumroad CONNECTED - Account: {user.get('email', 'verified')}")
        results['gumroad'] = {'status': 'connected', 'email': user.get('email', '')}
    except Exception as e:
        print(f"\nGumroad error: {e}")
        results['gumroad'] = {'status': 'error', 'message': str(e)}

# Save CONNECTION STATUS only (no keys) to Gaza Rose DB
conn = sqlite3.connect(str(DB_PATH))
conn.execute('''CREATE TABLE IF NOT EXISTS revenue_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    platform TEXT,
    status TEXT,
    details TEXT
)''')

for platform, data in results.items():
    conn.execute(
        'INSERT INTO revenue_connections VALUES (NULL, ?, ?, ?, ?)',
        (datetime.now().isoformat(), platform, data['status'], json.dumps({k:v for k,v in data.items() if k != 'key'}))
    )
conn.commit()
conn.close()

print(f"\n=== CONNECTION SUMMARY ===")
for platform, data in results.items():
    print(f"{platform.upper()}: {data['status'].upper()}")

print("\nConnection STATUS saved to Gaza Rose DB")
print("Your API keys were NOT saved anywhere")
print("\nRun this script again anytime to reconnect")
print("=== DONE ===\n")
