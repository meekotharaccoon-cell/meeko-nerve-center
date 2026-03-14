import sys, os, json, base64, time
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


def gh_api(path, method='GET', data=None):
    url = 'https://api.github.com/' + path.lstrip('/')
    req = ur.Request(url, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('User-Agent', 'meeko-mycelium')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode()
    resp = ur.urlopen(req, timeout=20)
    raw = resp.read()
    return json.loads(raw) if raw else {}


def get_file_sha(repo, fpath, branch):
    try:
        d = gh_api(f'repos/{OWNER}/{repo}/contents/{fpath}?ref={branch}')
        return d.get('sha')
    except Exception:
        return None


def put_file(repo, fpath, content_str, message, branch):
    sha = get_file_sha(repo, fpath, branch)
    data = {
        'message': message,
        'content': base64.b64encode(content_str.encode()).decode(),
        'branch': branch,
    }
    if sha:
        data['sha'] = sha
    return gh_api(f'repos/{OWNER}/{repo}/contents/{fpath}', 'PUT', data)


# 1. Find conductor default branch
cond_info = gh_api(f'repos/{OWNER}/atomic-agents-conductor')
cond_branch = cond_info.get('default_branch', 'main')
print(f'Conductor default branch: {cond_branch}')

# 2. List what workflows already exist in conductor
try:
    files = gh_api(f'repos/{OWNER}/atomic-agents-conductor/contents/.github/workflows?ref={cond_branch}')
    wf_names = [f['name'] for f in files]
    print(f'Existing workflows: {wf_names}')
except Exception as e:
    print(f'Could not list workflows: {e}')
    wf_names = []

# 3. Push auto-merge workflow to conductor using correct branch
AUTO_MERGE = """name: Auto-Merge Conductor PRs

on:
  pull_request:
    branches: [master, main]
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: startsWith(github.head_ref, 'conductor/')
    steps:
      - name: Auto-merge conductor branch
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.CONDUCTOR_TOKEN || secrets.GITHUB_TOKEN }}
          script: |
            const pr_num = context.payload.pull_request?.number;
            if (!pr_num) { core.info('No PR found'); return; }
            try {
              await github.rest.pulls.merge({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: pr_num,
                merge_method: 'squash'
              });
              core.info('Auto-merged PR #' + pr_num);
            } catch(e) {
              core.warning('Auto-merge: ' + e.message);
            }
"""

try:
    put_file('atomic-agents-conductor', '.github/workflows/auto-merge.yml',
             AUTO_MERGE, 'feat: auto-merge conductor PRs in target repos', cond_branch)
    print('auto-merge.yml pushed to conductor')
except Exception as e:
    print(f'auto-merge push: {e}')

# 4. Push the same auto-merge to the 3 target repos so THEY self-merge conductor PRs
for repo in ['atomic-agents', 'atomic-agents-staging', 'atomic-agents-demo']:
    try:
        put_file(repo, '.github/workflows/auto-merge.yml',
                 AUTO_MERGE, 'feat: auto-merge conductor PRs', 'master')
        print(f'auto-merge.yml pushed to {repo}')
    except Exception as e:
        print(f'{repo} auto-merge: {str(e)[:80]}')

print()

# 5. Check current workflow run status across all repos
print('=== CURRENT WORKFLOW STATUS ===')
time.sleep(3)
all_repos = REPOS = ['atomic-agents', 'atomic-agents-staging', 'atomic-agents-demo', 'atomic-agents-conductor']
for repo in all_repos:
    try:
        runs = gh_api(f'repos/{OWNER}/{repo}/actions/runs?per_page=3')
        workflow_runs = runs.get('workflow_runs', [])
        if not workflow_runs:
            print(f'  {repo}: no runs yet')
            continue
        for run in workflow_runs[:2]:
            status = run.get('conclusion') or run.get('status', '?')
            name = run.get('name', '?')[:30]
            created = run.get('created_at', '')[:16]
            icon = 'PASS' if status == 'success' else ('FAIL' if status == 'failure' else 'WAIT')
            print(f'  [{icon}] {repo}: {name} -> {status} ({created})')
    except Exception as e:
        print(f'  {repo}: {str(e)[:60]}')
