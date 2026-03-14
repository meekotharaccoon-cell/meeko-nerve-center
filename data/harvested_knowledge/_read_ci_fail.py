import sys, os, json
import urllib.request as ur
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

def gh_api(path):
    url = 'https://api.github.com/' + path.lstrip('/')
    req = ur.Request(url)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('User-Agent', 'meeko')
    req.add_header('Accept', 'application/vnd.github+json')
    return json.loads(ur.urlopen(req, timeout=15).read())

# Get latest failed run ID from atomic-agents
runs = gh_api('repos/meekotharaccoon-cell/atomic-agents/actions/runs?per_page=1')
run = runs['workflow_runs'][0]
run_id = run['id']
print(f'Latest run: {run_id} - {run.get("name")} - {run.get("conclusion")}')

# Get jobs for that run
jobs = gh_api(f'repos/meekotharaccoon-cell/atomic-agents/actions/runs/{run_id}/jobs')
for job in jobs.get('jobs', []):
    print(f'\nJob: {job["name"]} - {job.get("conclusion")}')
    for step in job.get('steps', []):
        if step.get('conclusion') == 'failure':
            print(f'  FAILED STEP: {step["name"]}')

# Get the logs for the first failed job
failed_jobs = [j for j in jobs.get('jobs', []) if j.get('conclusion') == 'failure']
if failed_jobs:
    job_id = failed_jobs[0]['id']
    import subprocess
    r = subprocess.run(
        ['gh', 'run', 'view', str(run_id), '--repo',
         'meekotharaccoon-cell/atomic-agents', '--log-failed'],
        capture_output=True, timeout=20
    )
    log = r.stdout.decode('utf-8', 'replace')
    # Print just the error lines
    for line in log.splitlines():
        if any(x in line for x in ['Error', 'error', 'failed', 'FAIL', 'Cannot', 'No module', 'Traceback', 'exit code']):
            print(line[-120:])
