import sys, os, subprocess, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

base = Path(r'C:\Users\meeko\Desktop')
auto = {}

# 1. GH token from gh CLI
r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
if r.stdout.strip():
    auto['CONDUCTOR_TOKEN'] = r.stdout.strip()
    print('AUTO-GOT: CONDUCTOR_TOKEN from gh CLI -> ' + auto['CONDUCTOR_TOKEN'][:12] + '...')

# 2. Kraken from Windows Credential Manager
ps_cmd = r"""
try {
  Add-Type -AssemblyName System.Security
  $cred = Get-StoredCredential -Target 'key_pair_es384.kraken' -ErrorAction SilentlyContinue
  if ($cred) { Write-Output $cred.GetNetworkCredential().Password }
} catch {}
"""
r2 = subprocess.run(['powershell', '-c', ps_cmd], capture_output=True, text=True, timeout=10)
if r2.stdout.strip() and len(r2.stdout.strip()) > 10:
    auto['KRAKEN_PRIVATE_KEY'] = r2.stdout.strip()
    print('AUTO-GOT: KRAKEN_PRIVATE_KEY from credential store')

ps_cmd2 = r"""
try {
  $cred = Get-StoredCredential -Target 'key_pair_es384_id.kraken' -ErrorAction SilentlyContinue
  if ($cred) { Write-Output $cred.GetNetworkCredential().Password }
} catch {}
"""
r3 = subprocess.run(['powershell', '-c', ps_cmd2], capture_output=True, text=True, timeout=10)
if r3.stdout.strip() and len(r3.stdout.strip()) > 5:
    auto['KRAKEN_API_KEY'] = r3.stdout.strip()
    print('AUTO-GOT: KRAKEN_API_KEY from credential store')

# 3. Phantom address from connect_crypto.py
for fname in ['connect_crypto.py', 'connect_revenue.py']:
    cp = base / 'UltimateAI_Master' / fname
    if cp.exists():
        content = cp.read_text(encoding='utf-8', errors='ignore')
        sol_matches = re.findall(r'[1-9A-HJ-NP-Za-km-z]{43,44}', content)
        for addr in sol_matches:
            if not any(addr.startswith(x) for x in ['sk_', 'pk_', 'rk_']):
                if 'PHANTOM_SOLANA_ADDRESS' not in auto:
                    auto['PHANTOM_SOLANA_ADDRESS'] = addr
                    print('AUTO-GOT: PHANTOM_SOLANA_ADDRESS from ' + fname + ' -> ' + addr[:10] + '...')

# 4. Scan config.json files for any tokens
for cfg in list(base.rglob('config.json'))[:10]:
    try:
        flat = cfg.read_text(encoding='utf-8', errors='ignore')
        tokens = re.findall(r'gh[pos]_[A-Za-z0-9]{36,}', flat)
        if tokens and 'CONDUCTOR_TOKEN' not in auto:
            auto['CONDUCTOR_TOKEN'] = tokens[0]
            print('AUTO-GOT: CONDUCTOR_TOKEN from config.json -> ' + tokens[0][:12] + '...')
        # Gumroad tokens
        gum = re.findall(r'[a-zA-Z0-9_\-]{40,64}', flat)
        for g in gum:
            if 'gumroad' in flat.lower() and 'GUMROAD_TOKEN' not in auto:
                pass  # too broad, skip
    except:
        pass

# 5. Check the .secrets file for anything already filled in
sf = base / 'UltimateAI_Master' / '.secrets'
if sf.exists():
    for line in sf.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip()
            if k and v and k not in auto:
                auto[k] = v
                print('ALREADY IN .secrets: ' + k)

print()
print('=' * 50)
print('AUTO-RECOVERED SECRETS: ' + str(len(auto)))
for k, v in auto.items():
    print('  ' + k + ' = ' + v[:12] + '...' + v[-4:] if len(v) > 16 else '  ' + k + ' = ' + v)

print()
all_needed = [
    'ALPACA_KEY', 'ALPACA_SECRET',
    'CB_API_KEY', 'CB_API_SECRET',
    'COINBASE_COMMERCE_KEY',
    'KRAKEN_API_KEY', 'KRAKEN_PRIVATE_KEY',
    'PHANTOM_SOLANA_ADDRESS',
    'GUMROAD_TOKEN',
    'STRIPE_SECRET_KEY',
    'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET',
    'CONDUCTOR_TOKEN',
]
still_need = [k for k in all_needed if k not in auto]
print('STILL NEED FROM MEEKO (' + str(len(still_need)) + '):')
for k in still_need:
    print('  ' + k)

# Save what we found to a temp file for the launcher to read
import json as j
tmp = base / 'UltimateAI_Master' / '_auto_secrets.json'
tmp.write_text(j.dumps(auto, indent=2))
print()
print('Auto-secrets saved to: ' + str(tmp))
