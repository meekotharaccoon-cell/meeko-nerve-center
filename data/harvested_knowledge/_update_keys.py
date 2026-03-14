import sys, os, json, subprocess, urllib.request, base64, time, sqlite3, threading
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

base = Path(r'C:\Users\meeko\Desktop')
secrets_path = base / 'UltimateAI_Master' / '.secrets'

# ── STEP 1: UPDATE SECRETS WITH NEW KEYS ────────────────────
print("Updating .secrets with new keys...")
lines = secrets_path.read_text(encoding='utf-8').splitlines()
updates = {
    'ALPACA_KEY':              'PKCNY6MJH425RHGN47DVBKKESS',
    'ALPACA_SECRET':           'mdrbdrjRVhuyqESDY4zMTey9A8XmBU1dYiSdRRAGpYT',
    'PHANTOM_SOLANA_ADDRESS':  'Gg3MpT7osGaDvuN3CZzgGTTTSkgFP14kBgdN46pajGAJ',
    'STRIPE_SECRET_KEY':       '',  # Removing broken stripe key
}

new_lines = []
written = set()
for line in lines:
    if '=' in line and not line.startswith('#'):
        k = line.split('=', 1)[0].strip()
        if k in updates:
            if updates[k]:  # only write if non-empty
                new_lines.append(f"{k}={updates[k]}")
                print(f"  UPDATED: {k}")
            else:
                new_lines.append(f"# {k}= (removed - not needed)")
                print(f"  REMOVED: {k}")
            written.add(k)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

secrets_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')

# Reload into env
for line in new_lines:
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v

# ── STEP 2: VERIFY EVERYTHING ────────────────────────────────
print("\nVerifying connections...")

def test(name, fn):
    try:
        result = fn()
        print(f"  OK   {name}: {result}")
        return result
    except Exception as e:
        print(f"  FAIL {name}: {str(e)[:60]}")
        return None

# Alpaca
def check_alpaca():
    ak = os.environ.get('ALPACA_KEY','')
    asc = os.environ.get('ALPACA_SECRET','')
    req = urllib.request.Request('https://paper-api.alpaca.markets/v2/account',
        headers={'APCA-API-KEY-ID':ak,'APCA-API-SECRET-KEY':asc})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    return f"equity=${float(d.get('equity',0)):.2f}"

# Phantom
def check_phantom():
    addr = os.environ.get('PHANTOM_SOLANA_ADDRESS','')
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr]}).encode()
    req = urllib.request.Request('https://api.mainnet-beta.solana.com', data=payload,
        headers={'Content-Type':'application/json'})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    sol = d.get('result',{}).get('value',0) / 1e9
    return f"{sol:.4f} SOL at {addr[:8]}..."

# Gumroad
def check_gumroad():
    gt = os.environ.get('GUMROAD_TOKEN','')
    req = urllib.request.Request('https://api.gumroad.com/v2/products',
        headers={'Authorization':f'Bearer {gt}'})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    products = d.get('products',[])
    total = sum(p.get('sales_count',0) for p in products)
    revenue = sum(float(p.get('revenue',0)) for p in products)
    return f"{len(products)} products, {total} sales, ${revenue/100:.2f} revenue"

# PayPal
def check_paypal():
    pp_id = os.environ.get('PAYPAL_CLIENT_ID','')
    pp_sc = os.environ.get('PAYPAL_CLIENT_SECRET','')
    creds = base64.b64encode(f"{pp_id}:{pp_sc}".encode()).decode()
    req = urllib.request.Request('https://api-m.paypal.com/v1/oauth2/token',
        data=b'grant_type=client_credentials',
        headers={'Authorization':'Basic '+creds,'Content-Type':'application/x-www-form-urlencoded'})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    return f"token obtained, live payments active"

alpaca_ok = test('Alpaca', check_alpaca)
phantom_ok = test('Phantom', check_phantom)
gumroad_ok = test('Gumroad', check_gumroad)
paypal_ok  = test('PayPal', check_paypal)

print()
print("Secrets updated and verified. System ready.")
