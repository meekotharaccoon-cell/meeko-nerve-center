import sys, os, json, urllib.request, base64
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1)
        k,v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v

print("=== DIAGNOSING 401 FAILURES ===")
print()

# 1. Alpaca — test both paper AND live endpoints
ak = os.environ.get('ALPACA_KEY','')
asc = os.environ.get('ALPACA_SECRET','')
print("ALPACA KEY:", ak[:12] + "..." if ak else "NOT SET")
print("ALPACA SECRET:", asc[:8] + "..." if asc else "NOT SET")
print()

for label, url in [("Paper", "https://paper-api.alpaca.markets/v2/account"),
                    ("Live",  "https://api.alpaca.markets/v2/account"),
                    ("Broker","https://broker-api.alpaca.markets/v1/accounts")]:
    try:
        req = urllib.request.Request(url,
            headers={'APCA-API-KEY-ID': ak, 'APCA-API-SECRET-KEY': asc})
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
        print(f"  Alpaca {label}: CONNECTED | {list(d.keys())[:5]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  Alpaca {label}: HTTP {e.code} | {body}")
    except Exception as e:
        print(f"  Alpaca {label}: ERROR | {str(e)[:80]}")

print()

# 2. Stripe — check key format and test
sk = os.environ.get('STRIPE_SECRET_KEY','')
print("STRIPE KEY:", sk[:12] + "..." if sk else "NOT SET")
print("STRIPE KEY PREFIX:", sk[:6] if sk else "N/A")
print()

if sk.startswith('sk_live_') or sk.startswith('sk_test_'):
    print("  Key format: VALID (sk_live_ or sk_test_)")
elif sk.startswith('rk_'):
    print("  Key format: RESTRICTED KEY (rk_) - may not have full access")
elif sk.startswith('mk_'):
    print("  Key format: WRONG - 'mk_' is NOT a Stripe key")
    print("  This might be a MoonPay key or pasted in wrong.")
    print("  Get your Stripe key from: dashboard.stripe.com/apikeys")
    print("  It must start with sk_live_ (live) or sk_test_ (test)")
else:
    print("  Key format: UNRECOGNIZED prefix:", sk[:6])

try:
    req = urllib.request.Request('https://api.stripe.com/v1/balance',
        headers={'Authorization': 'Bearer ' + sk})
    d = json.loads(urllib.request.urlopen(req, timeout=8).read())
    print("  Stripe: CONNECTED |", d.get('available', '?'))
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print(f"  Stripe: HTTP {e.code} | {body}")
except Exception as e:
    print(f"  Stripe: ERROR | {str(e)[:80]}")

print()

# 3. Phantom address check
phantom = os.environ.get('PHANTOM_SOLANA_ADDRESS','')
print("PHANTOM ADDRESS:", phantom)
print("ADDRESS LENGTH:", len(phantom))
known_bad = {
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC token mint address (NOT a wallet)',
    'So11111111111111111111111111111111111111112': 'Wrapped SOL mint (NOT a wallet)',
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT mint (NOT a wallet)',
}
if phantom in known_bad:
    print(f"  WARNING: This is {known_bad[phantom]} — NOT your personal wallet!")
    print("  Open Phantom in Brave browser -> click your address -> copy the full address")
    print("  It should be a unique 44-char address, not a known token mint.")
else:
    print("  Address looks like a personal wallet address.")

print()
print("=== WHAT TO FIX ===")
print()
if sk.startswith('mk_'):
    print("1. STRIPE KEY IS WRONG (mk_ prefix)")
    print("   Go to: https://dashboard.stripe.com/apikeys")
    print("   Copy your Secret key (starts with sk_live_...)")
    print("   Paste it into .secrets as: STRIPE_SECRET_KEY=sk_live_...")
    print()
if phantom in known_bad:
    print("2. PHANTOM ADDRESS IS A TOKEN MINT, NOT YOUR WALLET")
    print("   Open Brave browser -> Phantom extension -> click your account name")
    print("   Copy the address shown there (unique to you, starts with a random letter)")
    print("   Paste it into .secrets as: PHANTOM_SOLANA_ADDRESS=YOUR_REAL_ADDRESS")
    print()
print("After fixing, open .secrets and update the values, then re-run the debug.")
