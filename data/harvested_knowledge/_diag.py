import subprocess, sys, os, sqlite3, json, ast
from pathlib import Path

base = Path(r'C:\Users\meeko\Desktop')

pkgs = ['alpaca','coinbase','ccxt','yfinance','pandas','numpy','ta',
        'stripe','reportlab','crewai','litellm','openai','langchain',
        'requests','fastapi','flask','schedule','playwright']
print('PACKAGES:')
for p in pkgs:
    try:
        __import__(p)
        print('  OK   ' + p)
    except ImportError:
        print('  MISS ' + p)

print()
try:
    import urllib.request
    data = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3).read())
    models = [m['name'] for m in data.get('models', [])]
    print('OLLAMA: running | models: ' + str(models))
except Exception as e:
    print('OLLAMA: OFFLINE (' + str(e) + ')')

print()
db = base / 'UltimateAI_Master' / 'gaza_rose.db'
try:
    conn = sqlite3.connect(str(db))
    tables = conn.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',)).fetchall()
    print('DB TABLES:')
    for t in tables:
        c = conn.execute('SELECT COUNT(*) FROM ' + t[0]).fetchone()[0]
        print('  ' + t[0] + ': ' + str(c) + ' rows')
    conn.close()
except Exception as e:
    print('DB ERROR: ' + str(e))

print()
print('ENV SECRETS:')
for v in ['ALPACA_KEY','ALPACA_SECRET','CB_API_KEY','PHANTOM_SOLANA_ADDRESS',
          'GUMROAD_TOKEN','STRIPE_SECRET_KEY','CONDUCTOR_TOKEN']:
    val = os.environ.get(v, '')
    print('  ' + v + ': ' + ('SET' if val else 'NOT SET'))

print()
r = subprocess.run(['gh', 'auth', 'status'], capture_output=True)
out = (r.stdout or r.stderr).decode()
for line in out.strip().split('\n')[:4]:
    if line.strip():
        print('GH: ' + line.strip())
