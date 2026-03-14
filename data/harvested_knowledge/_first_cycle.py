import sys, os, sqlite3, json, subprocess, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(r'C:\Users\meeko\Desktop')
db   = base / 'UltimateAI_Master' / 'gaza_rose.db'

print('=== AUTONOMOUS AGENT - FIRST CYCLE ===')
print()

# 1. Load secrets
secrets_file = base / 'UltimateAI_Master' / '.secrets'
loaded = []
if secrets_file.exists():
    for line in secrets_file.read_text(encoding='utf-8').strip().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip()
            if k and v:
                os.environ[k] = v
                loaded.append(k)

if loaded:
    print('Secrets loaded from .secrets: ' + str(loaded))
else:
    print('Secrets: .secrets file is empty template - needs filling in')
print()

# 2. Check each secret
SECRET_KEYS = [
    'ALPACA_KEY','ALPACA_SECRET','CB_API_KEY','CB_API_SECRET',
    'PHANTOM_SOLANA_ADDRESS','GUMROAD_TOKEN','STRIPE_SECRET_KEY',
    'PAYPAL_CLIENT_ID','CONDUCTOR_TOKEN'
]
missing = []
for k in SECRET_KEYS:
    if os.environ.get(k,'').strip():
        print('  SET:   ' + k)
    else:
        missing.append(k)
        print('  EMPTY: ' + k)
print()

# 3. Ensure DB tables
required_tables = {
    'analyses':       'CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, ticker TEXT, asset_type TEXT, action TEXT, confidence REAL, risk_level TEXT, price REAL, reasoning TEXT, indicators TEXT, status TEXT DEFAULT "pending_approval")',
    'approval_tokens':'CREATE TABLE IF NOT EXISTS approval_tokens (token TEXT PRIMARY KEY, analysis_id INTEGER, created_at TEXT, used INTEGER DEFAULT 0, action TEXT, ticker TEXT, quantity REAL, price REAL)',
    'watchlist':      'CREATE TABLE IF NOT EXISTS watchlist (ticker TEXT PRIMARY KEY, asset_type TEXT, added TEXT, notes TEXT, active INTEGER DEFAULT 1)',
    'positions':      'CREATE TABLE IF NOT EXISTS positions (ticker TEXT PRIMARY KEY, asset_type TEXT, quantity REAL, avg_cost_basis REAL, total_invested REAL, first_purchase TEXT, last_updated TEXT)',
    'trades':         'CREATE TABLE IF NOT EXISTS trades (id TEXT PRIMARY KEY, timestamp TEXT, date TEXT, ticker TEXT, asset_type TEXT, action TEXT, quantity REAL, price REAL, fees REAL DEFAULT 0, total_cost REAL, exchange TEXT, order_id TEXT, analysis_id INTEGER, notes TEXT, paper_trade INTEGER DEFAULT 0)',
    'tax_lots':       'CREATE TABLE IF NOT EXISTS tax_lots (id TEXT PRIMARY KEY, ticker TEXT, asset_type TEXT, quantity REAL, cost_basis_per_unit REAL, date_acquired TEXT, date_sold TEXT, sale_price_per_unit REAL, proceeds REAL, cost_basis REAL, gain_loss REAL, term TEXT, wash_sale INTEGER DEFAULT 0, wash_sale_disallowed REAL DEFAULT 0)',
    'pcrf_donations': 'CREATE TABLE IF NOT EXISTS pcrf_donations (id INTEGER PRIMARY KEY, amount REAL, date TEXT, note TEXT)',
    'crypto_config':  'CREATE TABLE IF NOT EXISTS crypto_config (key TEXT PRIMARY KEY, value TEXT, updated TEXT)',
    'agent_actions':  'CREATE TABLE IF NOT EXISTS agent_actions (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, action_type TEXT, description TEXT, result TEXT, needs_human INTEGER DEFAULT 0)',
}
conn = sqlite3.connect(str(db))
existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
created = []
for tname, ddl in required_tables.items():
    if tname not in existing:
        conn.execute(ddl)
        created.append(tname)
conn.commit()
conn.close()
if created:
    print('DB: Created missing tables: ' + str(created))
else:
    print('DB: All required tables exist')
print()

# 4. Ollama
try:
    data = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3).read())
    models = [m['name'] for m in data.get('models', [])]
    mycelium = 'mycelium:latest' in models or 'mycelium' in str(models)
    print('Ollama: RUNNING')
    print('  Models: ' + str(models))
    print('  mycelium model: ' + ('YES' if mycelium else 'NOT YET - run AGENT_ROLE.py'))
except Exception as e:
    print('Ollama: OFFLINE - ' + str(e))
print()

# 5. Gallery
art_dir = base / 'GAZA_ROSE_GALLERY' / 'art'
art_count = len(list(art_dir.glob('*'))) if art_dir.exists() else 0
print('Gallery: ' + str(art_count) + ' art files')

# 6. Conductor
cond = base / 'atomic-agents-conductor'
has_dispatch = (cond / '.github' / 'workflows' / 'dispatch.yml').exists()
has_agent    = (cond / '.github' / 'workflows' / 'agent-dispatch.yml').exists()
print('Conductor: dispatch.yml=' + str(has_dispatch) + ', agent-dispatch.yml=' + str(has_agent))

# 7. Key files
key_files = [
    'AUTONOMOUS_AGENT.py',
    'GRAND_SETUP_WIZARD.py',
    'LIVE_DASHBOARD.py',
    'COMMAND_CENTER.bat',
    'AGENT_ROLE.py',
    'BUILD_MCP_CONFIG.py',
]
print()
print('Key files:')
for f in key_files:
    exists = (base / f).exists()
    print('  ' + ('OK  ' if exists else 'MISS') + ' ' + f)

print()
print('=== VERDICT ===')
print()
if not missing:
    print('Your system is self-sufficient. Run: python AUTONOMOUS_AGENT.py')
else:
    print('ONE THING BLOCKS EVERYTHING: your API keys are not in .secrets')
    print()
    print('Open this file in Notepad and fill in your keys:')
    print('  ' + str(base / 'UltimateAI_Master' / '.secrets'))
    print()
    print('Keys you need to paste in:')
    for k in missing:
        print('  ' + k + '=')
    print()
    print('Where to get each one:')
    howto = {
        'ALPACA_KEY':          'alpaca.markets -> API Keys -> Paper Trading',
        'ALPACA_SECRET':       'same page as ALPACA_KEY',
        'CB_API_KEY':          'coinbase.com/settings/api -> New API Key',
        'CB_API_SECRET':       'same page as CB_API_KEY (EC private key block)',
        'PHANTOM_SOLANA_ADDRESS': 'Open Phantom in Brave -> copy your 44-char address',
        'GUMROAD_TOKEN':       'gumroad.com/oauth/applications -> Access Token',
        'STRIPE_SECRET_KEY':   'dashboard.stripe.com/apikeys -> sk_live_...',
        'PAYPAL_CLIENT_ID':    'developer.paypal.com/dashboard/applications/live',
        'CONDUCTOR_TOKEN':     'github.com/settings/tokens -> repo + workflow scopes',
    }
    for k in missing:
        if k in howto:
            print('  ' + k + ':')
            print('    ' + howto[k])
    print()
    print('After filling .secrets, EVERYTHING runs automatically.')
    print('Your system handles itself from that point forward.')
