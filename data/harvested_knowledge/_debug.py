import sys, os, sqlite3, json, subprocess, urllib.request, socket, time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(r'C:\Users\meeko\Desktop')
db   = base / 'UltimateAI_Master' / 'gaza_rose.db'
PASS = '[PASS]'
FAIL = '[FAIL]'
WARN = '[WARN]'
INFO = '[INFO]'

results = {'pass':0,'fail':0,'warn':0}
def p(tag,msg):
    print(f"{tag} {msg}")
    if tag==PASS: results['pass']+=1
    elif tag==FAIL: results['fail']+=1
    elif tag==WARN: results['warn']+=1

print("="*60)
print("  MEEKO MYCELIUM - FULL DEBUG SCAN")
print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ── SECRETS ──────────────────────────────────────────────
print("\n[SECRETS]")
secrets_path = base / 'UltimateAI_Master' / '.secrets'
loaded = {}
if secrets_path.exists():
    for line in secrets_path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            k,v = line.split('=',1)
            k,v = k.strip(), v.strip()
            if k and v:
                os.environ[k]=v
                loaded[k]=v

keys_needed = {
    'ALPACA_KEY':          'alpaca.markets -> API Keys',
    'ALPACA_SECRET':       'alpaca.markets -> API Keys',
    'CB_API_KEY':          'coinbase.com/settings/api',
    'CB_API_SECRET':       'coinbase.com/settings/api (private key block)',
    'COINBASE_COMMERCE_KEY':'commerce.coinbase.com/settings',
    'KRAKEN_API_KEY':      'kraken.com/u/security/api',
    'KRAKEN_API_SECRET':   'kraken.com/u/security/api',
    'PHANTOM_SOLANA_ADDRESS':'Phantom wallet -> copy address (44 chars)',
    'GUMROAD_TOKEN':       'gumroad.com/oauth/applications',
    'STRIPE_SECRET_KEY':   'dashboard.stripe.com/apikeys  sk_live_...',
    'PAYPAL_CLIENT_ID':    'developer.paypal.com -> Live apps',
    'PAYPAL_CLIENT_SECRET':'developer.paypal.com -> Live apps',
    'CONDUCTOR_TOKEN':     'github.com/settings/tokens  repo+workflow',
}
missing_keys = []
for k,where in keys_needed.items():
    val = os.environ.get(k,'').strip()
    if val:
        preview = val[:6]+'...' if len(val)>6 else val
        p(PASS, f"{k} = {preview}")
    else:
        p(FAIL, f"{k} MISSING  <- {where}")
        missing_keys.append(k)

# ── PYTHON PACKAGES ──────────────────────────────────────
print("\n[PACKAGES]")
pkgs = ['alpaca','coinbase','ccxt','yfinance','pandas','numpy','ta',
        'stripe','reportlab','crewai','litellm','openai','langchain',
        'requests','fastapi','flask','schedule','playwright','solders']
for pkg in pkgs:
    try:
        __import__(pkg)
        p(PASS, pkg)
    except ImportError:
        p(FAIL, pkg + '  <- pip install ' + pkg)

# ── OLLAMA ───────────────────────────────────────────────
print("\n[OLLAMA]")
try:
    data = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags',timeout=3).read())
    models = [m['name'] for m in data.get('models',[])]
    p(PASS, "Ollama running | models: "+str(models))
    if 'mycelium:latest' in models:
        p(PASS, "mycelium model present")
    else:
        p(FAIL, "mycelium model MISSING  <- run: python AGENT_ROLE.py")
except Exception as e:
    p(FAIL, "Ollama OFFLINE: "+str(e))

# ── DATABASE ─────────────────────────────────────────────
print("\n[DATABASE]")
required_tables = ['transactions','revenue_connections','browser_sessions',
                   'crypto_config','pcrf_donations','watchlist','analyses',
                   'approval_tokens','positions','trades','tax_lots','agent_actions']
try:
    conn = sqlite3.connect(str(db))
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for t in required_tables:
        if t in existing:
            c = conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]
            p(PASS, f"table '{t}': {c} rows")
        else:
            p(FAIL, f"table '{t}' MISSING")
    conn.close()
except Exception as e:
    p(FAIL, "DB error: "+str(e))

# ── FILES ────────────────────────────────────────────────
print("\n[FILES]")
key_files = [
    base/'AUTONOMOUS_AGENT.py',
    base/'AGENT_ROLE.py',
    base/'GRAND_SETUP_WIZARD.py',
    base/'LIVE_DASHBOARD.py',
    base/'BUILD_MCP_CONFIG.py',
    base/'COMMAND_CENTER.bat',
    base/'MEEKO_LAUNCH.bat',
    base/'SYSTEM_HEALTH_CHECK.py',
    base/'UltimateAI_Master'/'.secrets',
    base/'UltimateAI_Master'/'gaza_rose.db',
    base/'GAZA_ROSE_GALLERY'/'index.html',
    base/'INVESTMENT_HQ'/'src'/'ai_analyst.py',
    base/'INVESTMENT_HQ'/'src'/'approval_portal.py',
    base/'INVESTMENT_HQ'/'src'/'exchange_connector.py',
    base/'atomic-agents-conductor'/'.github'/'workflows'/'dispatch.yml',
    base/'atomic-agents-conductor'/'.github'/'workflows'/'agent-dispatch.yml',
    base/'GAZA_ROSE_OMNI'/'master_orchestrator.py',
]
for f in key_files:
    if f.exists():
        sz = f.stat().st_size
        p(PASS, f"{f.name}  ({sz:,} bytes)")
    else:
        p(FAIL, f"{f.name}  MISSING  <- {str(f)}")

# ── LIVE SERVICE CONNECTIONS ──────────────────────────────
print("\n[LIVE CONNECTIONS]")

# Alpaca paper
ak = os.environ.get('ALPACA_KEY','')
asc = os.environ.get('ALPACA_SECRET','')
if ak and asc:
    try:
        req = urllib.request.Request('https://paper-api.alpaca.markets/v2/account',
            headers={'APCA-API-KEY-ID':ak,'APCA-API-SECRET-KEY':asc})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        p(PASS, f"Alpaca paper | equity=${float(d.get('equity',0)):.2f} | buying_power=${float(d.get('buying_power',0)):.2f}")
    except Exception as e:
        p(FAIL, "Alpaca: "+str(e)[:80])
else:
    p(WARN, "Alpaca: no credentials in .secrets")

# Solana/Phantom
phantom = os.environ.get('PHANTOM_SOLANA_ADDRESS','')
if phantom and len(phantom) > 30:
    try:
        payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[phantom]}).encode()
        req = urllib.request.Request('https://api.mainnet-beta.solana.com',data=payload,
            headers={'Content-Type':'application/json'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        sol = d.get('result',{}).get('value',0)/1_000_000_000
        p(PASS, f"Phantom/Solana | addr={phantom[:8]}... | balance={sol:.4f} SOL")
    except Exception as e:
        p(FAIL, "Phantom: "+str(e)[:80])
else:
    p(WARN, "Phantom: no address in .secrets")

# Gumroad
gt = os.environ.get('GUMROAD_TOKEN','')
if gt:
    try:
        req = urllib.request.Request('https://api.gumroad.com/v2/user',
            headers={'Authorization':'Bearer '+gt})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        email = d.get('user',{}).get('email','verified')
        p(PASS, "Gumroad: "+email)
    except Exception as e:
        p(FAIL, "Gumroad: "+str(e)[:80])
else:
    p(WARN, "Gumroad: no token in .secrets")

# Stripe
sk = os.environ.get('STRIPE_SECRET_KEY','')
if sk:
    try:
        req = urllib.request.Request('https://api.stripe.com/v1/balance',
            headers={'Authorization':'Bearer '+sk})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        avail = d.get('available',[{}])
        p(PASS, "Stripe connected | "+str(avail))
    except Exception as e:
        p(FAIL, "Stripe: "+str(e)[:80])
else:
    p(WARN, "Stripe: no key in .secrets")

# PayPal
pp_id = os.environ.get('PAYPAL_CLIENT_ID','')
pp_sc = os.environ.get('PAYPAL_CLIENT_SECRET','')
if pp_id and pp_sc:
    try:
        import base64
        creds = base64.b64encode(f"{pp_id}:{pp_sc}".encode()).decode()
        req = urllib.request.Request('https://api-m.paypal.com/v1/oauth2/token',
            data=b'grant_type=client_credentials',
            headers={'Authorization':'Basic '+creds,'Content-Type':'application/x-www-form-urlencoded'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        p(PASS, "PayPal: token obtained | scope: "+str(d.get('scope','')[:50]))
    except Exception as e:
        p(FAIL, "PayPal: "+str(e)[:80])
else:
    p(WARN, "PayPal: no credentials in .secrets")

# GitHub
ct = os.environ.get('CONDUCTOR_TOKEN','')
if ct:
    try:
        req = urllib.request.Request('https://api.github.com/user',
            headers={'Authorization':'Bearer '+ct,'User-Agent':'meeko-mycelium'})
        d = json.loads(urllib.request.urlopen(req,timeout=8).read())
        p(PASS, "GitHub: authenticated as "+d.get('login','?'))
    except Exception as e:
        p(FAIL, "GitHub token: "+str(e)[:80])
else:
    p(WARN, "GitHub: no CONDUCTOR_TOKEN in .secrets")

# Coinbase
cbk = os.environ.get('CB_API_KEY','')
if cbk:
    try:
        import coinbase
        p(PASS, "Coinbase package present | credentials will be tested when key format verified")
    except Exception as e:
        p(FAIL, "Coinbase: "+str(e)[:80])
else:
    p(WARN, "Coinbase: no credentials in .secrets")

# DexScreener (pump.fun proxy - no auth needed)
try:
    req = urllib.request.Request('https://api.dexscreener.com/token-boosts/top/v1',
        headers={'User-Agent':'meeko-mycelium'})
    d = json.loads(urllib.request.urlopen(req,timeout=8).read())
    count = len(d) if isinstance(d,list) else 0
    p(PASS, f"DexScreener (pump.fun data): {count} trending tokens")
except Exception as e:
    p(FAIL, "DexScreener: "+str(e)[:80])

# MCP config
print("\n[MCP CONFIG]")
mcp_config = Path(os.environ.get('APPDATA','')) / 'Claude' / 'claude_desktop_config.json'
if mcp_config.exists():
    try:
        cfg = json.loads(mcp_config.read_text(encoding='utf-8'))
        servers = cfg.get('mcpServers',{})
        p(PASS, f"claude_desktop_config.json: {len(servers)} MCP servers configured")
        for s in servers:
            p(INFO, f"  MCP: {s}")
    except Exception as e:
        p(FAIL, "MCP config malformed: "+str(e))
else:
    p(FAIL, "claude_desktop_config.json MISSING  <- run: python BUILD_MCP_CONFIG.py")

# Ports in use
print("\n[PORTS]")
port_map = {7776:'Grand Setup',7777:'Setup Wizard',7778:'Investment Portal',
             7779:'Live Dashboard',7780:'Autonomous Agent',11434:'Ollama'}
for port, name in port_map.items():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    result = s.connect_ex(('127.0.0.1', port))
    s.close()
    if result == 0:
        p(PASS, f":{port} {name} is RUNNING")
    else:
        p(WARN, f":{port} {name} not running")

# MEEKO_LAUNCH.bat
print("\n[LAUNCH BUTTON]")
lb = base/'MEEKO_LAUNCH.bat'
if lb.exists():
    p(PASS, "MEEKO_LAUNCH.bat exists on Desktop")
else:
    p(FAIL, "MEEKO_LAUNCH.bat MISSING  <- will be created")

print()
print("="*60)
print(f"  PASS: {results['pass']}  FAIL: {results['fail']}  WARN: {results['warn']}")
print("="*60)
if results['fail'] > 0 or missing_keys:
    print(f"\n  {results['fail']} things need fixing.")
    if missing_keys:
        print(f"  {len(missing_keys)} secrets still missing from .secrets file.")
print()
