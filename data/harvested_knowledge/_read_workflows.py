import sys, os, json, subprocess, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

repos = ['atomic-agents', 'atomic-agents-staging', 'atomic-agents-demo', 'atomic-agents-conductor']
owner = 'meekotharaccoon-cell'

for repo in repos:
    print(f"\n{'='*50}")
    print(f"REPO: {repo}")
    print('='*50)
    
    # Get workflow files
    r = subprocess.run(
        ['gh','api',f'repos/{owner}/{repo}/contents/.github/workflows'],
        capture_output=True, timeout=15
    )
    if r.returncode != 0:
        print(f"  No workflows dir or error: {r.stderr.decode()[:80]}")
        continue
    
    try:
        files = json.loads(r.stdout)
    except:
        print("  Could not parse response")
        continue
        
    for f in files:
        fname = f['name']
        print(f"\n  FILE: {fname}")
        
        # Get content
        r2 = subprocess.run(
            ['gh','api',f'repos/{owner}/{repo}/contents/.github/workflows/{fname}','--jq','.content'],
            capture_output=True, timeout=15
        )
        if r2.returncode == 0:
            try:
                content_b64 = r2.stdout.decode().strip().strip('"').replace('\\n','')
                content = base64.b64decode(content_b64).decode('utf-8')
                for line in content.splitlines()[:30]:
                    print(f"    {line}")
            except Exception as e:
                print(f"  Could not decode: {e}")
    
    # Latest run failure details
    r3 = subprocess.run(
        ['gh','api',f'repos/{owner}/{repo}/actions/runs','--jq',
         '.workflow_runs[:1] | .[] | {conclusion, name, id: .id}'],
        capture_output=True, timeout=15
    )
    if r3.returncode == 0:
        print(f"\n  LATEST RUN: {r3.stdout.decode().strip()[:200]}")
        
        # Get the actual job logs for the failure
        try:
            run_data = json.loads(r3.stdout.decode().strip())
            run_id = run_data.get('id')
            if run_data.get('conclusion') == 'failure' and run_id:
                r4 = subprocess.run(
                    ['gh','api',f'repos/{owner}/{repo}/actions/runs/{run_id}/jobs',
                     '--jq','.jobs[].steps[] | select(.conclusion=="failure") | .name + ": " + (.conclusion // "?")'],
                    capture_output=True, timeout=15
                )
                if r4.returncode == 0:
                    print(f"  FAILED STEPS: {r4.stdout.decode().strip()[:300]}")
        except Exception as e:
            print(f"  Could not get job details: {e}")
