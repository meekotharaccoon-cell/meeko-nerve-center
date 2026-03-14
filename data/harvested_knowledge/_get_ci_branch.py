import sys, os, json, subprocess, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

owner = 'meekotharaccoon-cell'
repo = 'atomic-agents'

# Get ci.yml from the conductor/self-healing-ci branch (the one that's failing)
r = subprocess.run([
    'gh','api',
    f'repos/{owner}/{repo}/contents/.github/workflows/ci.yml',
    '-X','GET','-F','ref=conductor/self-healing-ci'
], capture_output=True, timeout=15)

print("=== ci.yml from conductor/self-healing-ci branch ===")
if r.returncode == 0:
    data = json.loads(r.stdout)
    content = base64.b64decode(data['content'].replace('\n','')).decode('utf-8')
    print(content)
else:
    print("ERROR:", r.stderr.decode()[:200])

print()

# Also get the master branch version
r2 = subprocess.run([
    'gh','api',
    f'repos/{owner}/{repo}/contents/.github/workflows/ci.yml',
    '-X','GET','-F','ref=master'
], capture_output=True, timeout=15)
print("=== ci.yml from master branch ===")
if r2.returncode == 0:
    data2 = json.loads(r2.stdout)
    content2 = base64.b64decode(data2['content'].replace('\n','')).decode('utf-8')
    print(content2)
else:
    print("ERROR:", r2.stderr.decode()[:200])
