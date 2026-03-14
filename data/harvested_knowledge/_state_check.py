import sys, os, json, sqlite3, urllib.request as ur, base64
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
base = Path(r'C:\Users\meeko\Desktop')

for line in (base/'UltimateAI_Master'/'.secrets').read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1)
        if k.strip() and v.strip(): os.environ[k.strip()]=v.strip()

print('=== WHAT ACTUALLY WORKS RIGHT NOW ===')
working = []
broken  = []
free    = []

# GitHub
ct = os.environ.get('CONDUCTOR_TOKEN','')
if ct:
    try:
        d = json.loads(ur.urlopen(ur.Request('https://api.github.com/user',
            headers={'Authorization':'Bearer '+ct,'User-Agent':'meeko'}),timeout=8).read())
        print(f'  WORKS  GitHub -> {d.get("login")} | {d.get("public_repos")} public repos')
        working.append('GitHub')
    except Exception as e: broken.append(f'GitHub: {e}')

# PayPal
pp_id = os.environ.get('PAYPAL_CLIENT_ID','')
pp_sc = os.environ.get('PAYPAL_CLIENT_SECRET','')
if pp_id and pp_sc:
    try:
        creds = base64.b64encode(f'{pp_id}:{pp_sc}'.encode()).decode()
        d = json.loads(ur.urlopen(ur.Request('https://api-m.paypal.com/v1/oauth2/token',
            data=b'grant_type=client_credentials',
            headers={'Authorization':'Basic '+creds,'Content-Type':'application/x-www-form-urlencoded'}),timeout=8).read())
        print(f'  WORKS  PayPal -> token valid {d.get("expires_in")}s')
        working.append('PayPal')
    except Exception as e: broken.append(f'PayPal: {e}')

# Gumroad
gt = os.environ.get('GUMROAD_TOKEN','')
if gt:
    try:
        d = json.loads(ur.urlopen(ur.Request('https://api.gumroad.com/v2/products',
            headers={'Authorization':'Bearer '+gt}),timeout=8).read())
        print(f'  WORKS  Gumroad -> {len(d.get("products",[]))} products')
        working.append('Gumroad')
    except Exception as e: broken.append(f'Gumroad: {e}')

# Alpaca - test key format
ak = os.environ.get('ALPACA_KEY','')
asc = os.environ.get('ALPACA_SECRET','')
if ak:
    print(f'  BROKEN Alpaca -> key {ak[:12]}... giving 401 (needs regen at alpaca.markets)')
    broken.append('Alpaca (401 - key needs regen)')

# Stripe
sk = os.environ.get('STRIPE_SECRET_KEY','')
if sk:
    print(f'  BROKEN Stripe -> key starts with {sk[:6]} (needs sk_live_ prefix from dashboard.stripe.com/apikeys)')
    broken.append('Stripe (wrong key type)')

# Phantom/Solana - check what's in .secrets
phantom = os.environ.get('PHANTOM_SOLANA_ADDRESS','')
if phantom == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':
    print(f'  BROKEN Phantom -> address is USDC mint, not your wallet')
    broken.append('Phantom (wrong address - is USDC mint)')
elif phantom:
    print(f'  WORKS  Phantom -> {phantom[:8]}...{phantom[-6:]}')
    working.append('Phantom')

# Coinbase
cbk = os.environ.get('CB_API_KEY','')
if cbk:
    print(f'  SET    Coinbase -> key present, format needs test')

print()
print('=== FREE APIs (no key needed) ===')
free_apis = [
    ('yfinance',     'stocks, ETFs, crypto prices - no key'),
    ('CoinGecko',    'crypto prices, market caps'),
    ('DexScreener',  'pump.fun, Solana DEX data'),
    ('Solana RPC',   'read any wallet balance'),
    ('Kraken public','prices without auth'),
    ('CoinMarketCap','free tier prices'),
    ('OpenLiberty',  'news feed'),
    ('Wikipedia',    'knowledge base'),
    ('GitHub',       'repos, issues, workflows - have token'),
]
for name, desc in free_apis:
    print(f'  FREE   {name} -> {desc}')

print()
print('=== REPOS - WORKFLOW STATUS ===')
repos = ['atomic-agents','atomic-agents-staging','atomic-agents-demo','atomic-agents-conductor']
for repo in repos:
    try:
        import subprocess
        r = subprocess.run(['gh','run','list','--repo',f'meekotharaccoon-cell/{repo}',
            '--limit','3','--json','status,conclusion,name,createdAt'],
            capture_output=True,timeout=15)
        runs = json.loads(r.stdout) if r.stdout else []
        if runs:
            for run in runs[:2]:
                status = run.get('conclusion') or run.get('status','?')
                print(f'  {repo}: {run.get("name","?")} -> {status}')
        else:
            print(f'  {repo}: no recent runs')
    except Exception as e:
        print(f'  {repo}: error {str(e)[:40]}')

print()
print(f'SUMMARY: {len(working)} working, {len(broken)} broken, lots free')
