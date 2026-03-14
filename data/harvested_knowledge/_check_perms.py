import sys, os, json, base64, subprocess
import urllib.request as ur, urllib.error
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path(r'C:\Users\meeko\Desktop')
OWNER = 'meekotharaccoon-cell'

for line in (BASE / 'UltimateAI_Master' / '.secrets').read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        if k.strip() and v.strip():
            os.environ[k.strip()] = v.strip()

TOKEN = os.environ.get('CONDUCTOR_TOKEN', '')

# Check token scopes
req = ur.Request('https://api.github.com/user', headers={
    'Authorization': 'Bearer ' + TOKEN,
    'User-Agent': 'meeko'
})
resp = ur.urlopen(req, timeout=10)
print('Token scopes:', resp.headers.get('X-OAuth-Scopes', 'none listed'))
print('Login:', json.loads(resp.read()).get('login'))

# Check repo permissions directly
for repo in ['atomic-agents', 'atomic-agents-staging', 'atomic-agents-demo']:
    try:
        req2 = ur.Request(
            f'https://api.github.com/repos/{OWNER}/{repo}',
            headers={'Authorization': 'Bearer ' + TOKEN, 'User-Agent': 'meeko',
                     'Accept': 'application/vnd.github+json'}
        )
        d = json.loads(ur.urlopen(req2, timeout=10).read())
        perms = d.get('permissions', {})
        print(f'{repo}: push={perms.get("push")}, admin={perms.get("admin")}, default_branch={d.get("default_branch")}')
    except Exception as e:
        print(f'{repo}: {e}')
