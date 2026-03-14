import sys, os, json, urllib.request, base64, subprocess, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

CT = os.environ.get('CONDUCTOR_TOKEN','')
OWNER = 'meekotharaccoon-cell'
REPO  = 'gaza-rose-gallery'

# ── 1. CREATE THE GALLERY REPO ────────────────────────────────
print("=== SETTING UP GAZA ROSE GALLERY REPO ===")

# Check if repo exists
r = subprocess.run(['gh','api',f'repos/{OWNER}/{REPO}'], capture_output=True, timeout=10)
if r.returncode != 0:
    print(f"Creating repo {REPO}...")
    r2 = subprocess.run([
        'gh','repo','create', f'{OWNER}/{REPO}',
        '--public', '--description', 'Gaza Rose — 300 DPI digital art. $1 per piece. 70% to PCRF.',
    ], capture_output=True, timeout=20)
    if r2.returncode == 0:
        print("  Repo created!")
    else:
        print("  Error:", r2.stderr.decode()[:100])
else:
    print(f"Repo {REPO} already exists")

time.sleep(2)

# ── 2. CREATE A GITHUB RELEASE FOR ART FILES ──────────────────
print("\nCreating GitHub release for art downloads...")
release_data = json.dumps({
    'tag_name': 'v1.0-art-collection',
    'name': 'Gaza Rose — Complete Art Collection',
    'body': '69 pieces of 300 DPI digital floral art. $1 each. 70% to PCRF.',
    'draft': False,
    'prerelease': False
}).encode()

r = subprocess.run([
    'gh','api', f'repos/{OWNER}/{REPO}/releases',
    '-X','POST','--input','-'
], input=release_data, capture_output=True, timeout=20)

release_id = None
if r.returncode == 0:
    rel = json.loads(r.stdout)
    release_id = rel['id']
    upload_url = rel['upload_url'].split('{')[0]
    print(f"  Release created! ID: {release_id}")
    print(f"  Upload URL: {upload_url}")
else:
    # Try to get existing release
    r2 = subprocess.run([
        'gh','api', f'repos/{OWNER}/{REPO}/releases/tags/v1.0-art-collection'
    ], capture_output=True, timeout=10)
    if r2.returncode == 0:
        rel = json.loads(r2.stdout)
        release_id = rel['id']
        upload_url = rel['upload_url'].split('{')[0]
        print(f"  Using existing release ID: {release_id}")
    else:
        print("  Could not create or find release:", r.stderr.decode()[:100])

# Save for next script
state = {'release_id': release_id, 'owner': OWNER, 'repo': REPO}
Path(r'C:\Users\meeko\Desktop\_gallery_state.json').write_text(
    json.dumps(state, indent=2), encoding='utf-8')
print(f"\nState saved. release_id={release_id}")
