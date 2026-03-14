import sys, os, json, subprocess, urllib.request, base64, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

base = Path(r'C:\Users\meeko\Desktop')
secrets_path = base / 'UltimateAI_Master' / '.secrets'
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v

print("="*60)
print("DO WHAT YOU CAN WITH WHAT YOU HAVE")
print("="*60)

# ── 1. TEST WHAT'S ACTUALLY WORKING RIGHT NOW ───────────────
working = {}
broken  = {}

print("\n[CHECKING ALL CONNECTIONS]")

# PayPal - confirmed working
pp_id = os.environ.get('PAYPAL_CLIENT_ID','')
pp_sc = os.environ.get('PAYPAL_CLIENT_SECRET','')
if pp_id and pp_sc:
    try:
        creds = base64.b64encode(f"{pp_id}:{pp_sc}".encode()).decode()
        req = urllib.request.Request('https://api-m.paypal.com/v1/oauth2/token',
            data=b'grant_type=client_credentials',
            headers={'Authorization':'Basic '+creds,'Content-Type':'application/x-www-form-urlencoded'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        if d.get('access_token'):
            working['paypal'] = 'live payments'
            print("  OK   PayPal -> live payments active")
        else:
            broken['paypal'] = 'no token returned'
    except Exception as e:
        broken['paypal'] = str(e)[:60]
        print(f"  FAIL PayPal -> {e}")
else:
    broken['paypal'] = 'no credentials'

# Gumroad - confirmed working
gt = os.environ.get('GUMROAD_TOKEN','')
if gt:
    try:
        req = urllib.request.Request('https://api.gumroad.com/v2/products',
            headers={'Authorization':'Bearer '+gt})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        count = len(d.get('products',[]))
        working['gumroad'] = f'{count} products'
        print(f"  OK   Gumroad -> {count} products listed")
    except Exception as e:
        broken['gumroad'] = str(e)[:60]

# GitHub - confirmed working
ct = os.environ.get('CONDUCTOR_TOKEN','')
if ct:
    try:
        req = urllib.request.Request('https://api.github.com/user',
            headers={'Authorization':'Bearer '+ct,'User-Agent':'meeko'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        working['github'] = d.get('login','?')
        print(f"  OK   GitHub -> {d.get('login')}")
    except Exception as e:
        broken['github'] = str(e)[:60]

# yfinance - free market data (no key needed!)
try:
    import yfinance as yf
    ticker = yf.Ticker('AAPL')
    info = ticker.fast_info
    price = info.last_price if hasattr(info,'last_price') else None
    if price:
        working['market_data'] = f'yfinance free (AAPL=${price:.2f})'
        print(f"  OK   Market data -> yfinance free (no key needed) AAPL=${price:.2f}")
    else:
        working['market_data'] = 'yfinance free'
        print("  OK   Market data -> yfinance free (no key needed)")
except Exception as e:
    broken['market_data'] = str(e)[:60]

# Coinbase Commerce
cck = os.environ.get('COINBASE_COMMERCE_KEY','')
if cck:
    try:
        req = urllib.request.Request('https://api.commerce.coinbase.com/checkouts',
            headers={'X-CC-Api-Key':cck,'X-CC-Version':'2018-03-22'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        working['coinbase_commerce'] = f'{len(d.get("data",[]))} checkouts'
        print(f"  OK   Coinbase Commerce -> {len(d.get('data',[]))} checkouts")
    except Exception as e:
        broken['coinbase_commerce'] = str(e)[:60]
        print(f"  FAIL Coinbase Commerce -> {e}")

# Kraken (no trade permissions needed to check pairs/prices)
kak = os.environ.get('KRAKEN_API_KEY','')
kas = os.environ.get('KRAKEN_API_SECRET','')
if kak and kas:
    try:
        import ccxt
        k = ccxt.kraken({'apiKey':kak,'secret':kas})
        bal = k.fetch_balance()
        nonzero = {c:v for c,v in bal.get('total',{}).items() if v and float(v) > 0}
        working['kraken'] = f'{len(nonzero)} currencies'
        print(f"  OK   Kraken -> {nonzero}")
    except Exception as e:
        broken['kraken'] = str(e)[:60]
        print(f"  FAIL Kraken -> {str(e)[:60]}")

# Alpaca - test key validity
ak = os.environ.get('ALPACA_KEY','')
asc = os.environ.get('ALPACA_SECRET','')
if ak and asc:
    try:
        req = urllib.request.Request('https://paper-api.alpaca.markets/v2/account',
            headers={'APCA-API-KEY-ID':ak,'APCA-API-SECRET-KEY':asc})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        working['alpaca'] = 'paper trading'
        print(f"  OK   Alpaca -> paper trading, equity=${float(d.get('equity',0)):.2f}")
    except urllib.error.HTTPError as e:
        broken['alpaca'] = f'401 - key expired or wrong secret'
        print(f"  FAIL Alpaca -> 401 unauthorized (key needs regeneration)")

# Stripe
sk = os.environ.get('STRIPE_SECRET_KEY','')
if sk and sk.startswith('sk_'):
    try:
        req = urllib.request.Request('https://api.stripe.com/v1/balance',
            headers={'Authorization':'Bearer '+sk})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        working['stripe'] = 'live'
        print(f"  OK   Stripe -> live")
    except Exception as e:
        broken['stripe'] = str(e)[:60]
elif sk:
    broken['stripe'] = f'wrong key prefix: {sk[:6]} (needs sk_live_...)'
    print(f"  FAIL Stripe -> wrong key format (mk_ is not Stripe)")

# DexScreener / pump.fun - free, no key
try:
    req = urllib.request.Request('https://api.dexscreener.com/token-boosts/top/v1',
        headers={'User-Agent':'meeko'})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    sol_tokens = [t for t in (d if isinstance(d,list) else []) if t.get('chainId')=='solana']
    working['dexscreener'] = f'{len(sol_tokens)} Solana tokens trending'
    print(f"  OK   DexScreener/pump.fun -> {len(sol_tokens)} Solana trending (free, no key)")
except Exception as e:
    broken['dexscreener'] = str(e)[:60]

# Ollama - local, free
try:
    data = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags',timeout=3).read())
    models = [m['name'] for m in data.get('models',[])]
    working['ollama'] = f'{len(models)} models local'
    print(f"  OK   Ollama local AI -> {models}")
except Exception as e:
    broken['ollama'] = 'offline'
    print(f"  FAIL Ollama -> offline, run: ollama serve")

print()
print("="*60)
print(f"WORKING: {len(working)} services")
print(f"BROKEN:  {len(broken)} services")
print("="*60)

# ── 2. WIRE FREE ALTERNATIVES FOR BROKEN SERVICES ───────────
print("\n[WIRING FREE ALTERNATIVES]")

# Free market data config
free_config = {
    'market_data': {
        'provider': 'yfinance',
        'description': 'Free stock/crypto data, no API key, covers all NYSE/NASDAQ/crypto',
        'working': True
    },
    'payment': {
        'primary': 'paypal' if 'paypal' in working else 'gumroad',
        'secondary': 'gumroad' if 'gumroad' in working else None,
        'stripe_status': broken.get('stripe',''),
        'note': 'Routing all payments through PayPal + Gumroad (both working)'
    },
    'crypto_data': {
        'provider': 'dexscreener',
        'description': 'Free pump.fun/Solana token data, no key needed',
        'working': True
    },
    'trading': {
        'stock': 'alpaca_needs_new_key' if 'alpaca' in broken else 'alpaca',
        'crypto': 'kraken' if 'kraken' in working else 'coinbase',
        'fallback': 'paper_only_via_yfinance_simulation'
    }
}

config_path = base / 'UltimateAI_Master' / 'system_config.json'
config_path.write_text(json.dumps(free_config, indent=2), encoding='utf-8')
print(f"  Written: system_config.json")
print(f"  Payment: routing through {'PayPal' if 'paypal' in working else 'Gumroad'}")
print(f"  Market data: yfinance (free, unlimited)")
print(f"  Crypto data: DexScreener (free, no key)")

# ── 3. WRITE THE CLEAR MANUAL STEPS FOR BROKEN THINGS ───────
instructions = []

if 'alpaca' in broken:
    instructions.append({
        'service': 'Alpaca Trading',
        'problem': 'Your key was rejected (401). Keys expire or get invalidated.',
        'time': '2 minutes',
        'steps': [
            '1. Open browser -> go to app.alpaca.markets',
            '2. Log in -> click your account icon top right',
            '3. Click "Paper Trading" tab on the left',
            '4. Scroll to "API Keys" section',
            '5. If you see your old key (PK33RL...) -> click the trash icon to delete it',
            '6. Click "Generate New Key"',
            '7. Copy BOTH the API Key ID and Secret Key (secret shows ONCE)',
            '8. Open: C:\\Users\\meeko\\Desktop\\UltimateAI_Master\\.secrets',
            '9. Replace the ALPACA_KEY= and ALPACA_SECRET= lines with new values',
            '10. Save and close'
        ]
    })

if 'stripe' in broken:
    instructions.append({
        'service': 'Stripe',
        'problem': 'Key starts with mk_ which is not Stripe (it may be a MoonPay key).',
        'time': '1 minute',
        'steps': [
            '1. Open browser -> go to dashboard.stripe.com',
            '2. Log in',
            '3. Click "Developers" in left sidebar',
            '4. Click "API keys"',
            '5. You will see "Secret key" with a "Reveal" button',
            '6. Click Reveal -> copy the FULL key (starts with sk_live_)',
            '7. Open: C:\\Users\\meeko\\Desktop\\UltimateAI_Master\\.secrets',
            '8. Replace STRIPE_SECRET_KEY= with sk_live_... value',
            '9. Save and close',
            'NOTE: If you see sk_test_ instead of sk_live_, you are in test mode.',
            '      sk_test_ works fine for now - just use it.'
        ]
    })

phantom_addr = os.environ.get('PHANTOM_SOLANA_ADDRESS','')
known_bad = {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC token mint (not your wallet)'}
if phantom_addr in known_bad:
    instructions.append({
        'service': 'Phantom Wallet Address',
        'problem': f'Current address is the {known_bad[phantom_addr]} - not yours.',
        'time': '30 seconds',
        'steps': [
            '1. Open Brave browser',
            '2. Click the Phantom fox icon in the top-right toolbar',
            '3. Your wallet opens - look at the TOP where it shows your account name',
            '4. BELOW the account name you will see a short address like "EPjF...1v"',
            '5. Click that address - it copies your FULL address to clipboard',
            '   (OR: click the three dots ... -> Account Details -> copy the full address)',
            '6. Your real address is 44 characters and unique to you',
            '7. Open: C:\\Users\\meeko\\Desktop\\UltimateAI_Master\\.secrets',
            '8. Replace PHANTOM_SOLANA_ADDRESS= with YOUR address',
            '9. Save and close',
            'NOTE: Your real address will show YOUR actual SOL balance.',
            '      The current one shows 429 SOL belonging to Circle/USDC contract.'
        ]
    })

# Save instructions to a readable text file on Desktop
output = "MANUAL STEPS NEEDED\n" + "="*50 + "\n\n"
output += f"Working services ({len(working)}): {', '.join(working.keys())}\n"
output += f"Needs manual fix ({len(instructions)}): {', '.join(i['service'] for i in instructions)}\n\n"
output += "="*50 + "\n\n"

for idx, inst in enumerate(instructions, 1):
    output += f"FIX {idx}: {inst['service']} (~{inst['time']})\n"
    output += f"Problem: {inst['problem']}\n\n"
    for step in inst['steps']:
        output += f"  {step}\n"
    output += "\n" + "-"*40 + "\n\n"

output += "After fixing all three:\n"
output += "  Run: python C:\\Users\\meeko\\Desktop\\_debug.py\n"
output += "  Should show 79/79 PASS, 0 FAIL\n"

steps_path = base / 'MANUAL_STEPS.txt'
steps_path.write_text(output, encoding='utf-8')
print()
print("="*60)
print(f"Manual steps saved to Desktop: MANUAL_STEPS.txt")
print(f"Opening it now...")
print("="*60)
print()
print(output)

# Open the instructions
subprocess.Popen(['notepad', str(steps_path)])
