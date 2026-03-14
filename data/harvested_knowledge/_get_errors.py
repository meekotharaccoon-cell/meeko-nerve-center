import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Get the actual failure reason from CI runs
repos = ['atomic-agents', 'atomic-agents-staging', 'atomic-agents-demo']
owner = 'meekotharaccoon-cell'

for repo in repos:
    # Get latest failed run id
    r = subprocess.run(['gh','api',f'repos/{owner}/{repo}/actions/runs'],
        capture_output=True, timeout=15)
    if r.returncode != 0:
        continue
    runs = json.loads(r.stdout)
    failed = [x for x in runs.get('workflow_runs',[]) if x.get('conclusion') == 'failure']
    if not failed:
        print(f"{repo}: no failures")
        continue
    
    run_id = failed[0]['id']
    print(f"\n{repo} run {run_id}:")
    
    # Get jobs for this run
    r2 = subprocess.run(['gh','api',f'repos/{owner}/{repo}/actions/runs/{run_id}/jobs'],
        capture_output=True, timeout=15)
    if r2.returncode != 0:
        print(f"  jobs error: {r2.stderr.decode()[:80]}")
        continue
    
    jobs = json.loads(r2.stdout)
    for job in jobs.get('jobs', []):
        print(f"  Job: {job['name']} -> {job['conclusion']}")
        for step in job.get('steps', []):
            if step.get('conclusion') == 'failure':
                print(f"    FAIL STEP: {step['name']}")
        # Get annotations (actual error message)
        r3 = subprocess.run(['gh','api',
            f'repos/{owner}/{repo}/check-runs/{job["id"]}/annotations'],
            capture_output=True, timeout=15)
        if r3.returncode == 0:
            try:
                notes = json.loads(r3.stdout)
                for n in notes[:3]:
                    print(f"    ERROR: {n.get('message','')[:200]}")
            except:
                pass
