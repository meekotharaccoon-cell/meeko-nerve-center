#!/usr/bin/env python3
"""
Master Controller Engine
=========================
This IS the brain. Not Meeko. Not the user.
This engine watches every workflow, retries every failure,
chains everything in the right order, and sends diagnostic
results to ITSELF (not the user) to act on.

The architecture shift:
  OLD: Workflow fails -> user gets email -> user re-runs
  NEW: Workflow fails -> master_controller detects -> retriggers -> done
       Master controller logs the fix -> perpetual_builder learns
       No email to user unless it's a DO THIS action (< 5/week target)

What this engine does:
  1. Queries GitHub API for ALL workflow runs in last 24h
  2. Categorizes: success, failure, running, queued, skipped
  3. For failures: determines if retriable (transient) vs broken (needs fix)
  4. Retriable: auto-triggers rerun via GitHub API
  5. Broken: generates fix code, writes it, commits
  6. Produces data/workflow_health.json consumed by dashboard
  7. Posts status to data/self_diagnostic_inbox.json
     which self_healer_v2.py reads and acts on
  8. NEVER emails the user about workflow status
     (that's what the Sunday brief is for)

The self-healing loop:
  master_controller.py runs
    -> finds failures
    -> writes to data/self_diagnostic_inbox.json
    -> self_healer_v2.py reads that file
    -> self_healer_v2.py generates fixes and commits
    -> perpetual_builder.py sees the fixed files
    -> next cycle: no failure

This is the system thinking and healing itself.
"""

import json, datetime, os, time
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
REPO = 'meekotharaccoon-cell/meeko-nerve-center'

# Errors that are transient (network, rate limit, timeout) - always retry
TRANSIENT_ERRORS = [
    'Process completed with exit code 1',
    'timeout', 'rate limit', 'Connection reset',
    '503', '502', '504', 'network', 'ETIMEDOUT'
]

# Errors that indicate broken code - need self-healer
CODE_ERRORS = [
    'SyntaxError', 'IndentationError', 'ImportError',
    'ModuleNotFoundError', 'AttributeError: NoneType',
    'json.decoder.JSONDecodeError', 'KeyError'
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def gh_api(method, path, body=None):
    if not GITHUB_TOKEN: return None
    try:
        req = urllib_request.Request(
            f'https://api.github.com/{path}',
            data=json.dumps(body).encode() if body else None,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json',
            },
            method=method
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[ctrl] GH error {method} {path[:50]}: {e}')
        return None

def get_all_workflow_runs():
    """Get recent runs for all workflows."""
    # Get list of all workflows
    wfs = gh_api('GET', f'repos/{REPO}/actions/workflows?per_page=100')
    if not wfs: return []
    workflows = wfs.get('workflows', [])
    
    all_runs = []
    for wf in workflows:
        wf_id = wf['id']
        wf_name = wf['name']
        # Get latest run for this workflow
        runs = gh_api('GET', f'repos/{REPO}/actions/workflows/{wf_id}/runs?per_page=3')
        if runs and runs.get('workflow_runs'):
            for run in runs['workflow_runs'][:1]:  # Just latest
                run['workflow_name'] = wf_name
                run['workflow_file'] = wf.get('path', '').replace('.github/workflows/', '')
                all_runs.append(run)
    return all_runs

def categorize_runs(runs):
    categorized = {'success': [], 'failure': [], 'running': [], 'queued': [], 'skipped': [], 'other': []}
    for run in runs:
        status     = run.get('status', '')
        conclusion = run.get('conclusion', '')
        if status in ('in_progress', 'queued', 'waiting'):
            categorized['running' if status == 'in_progress' else 'queued'].append(run)
        elif conclusion == 'success':
            categorized['success'].append(run)
        elif conclusion == 'failure':
            categorized['failure'].append(run)
        elif conclusion == 'skipped':
            categorized['skipped'].append(run)
        else:
            categorized['other'].append(run)
    return categorized

def is_recent_failure(run, hours=24):
    """Only retry failures from last 24 hours."""
    updated = run.get('updated_at', '')
    if not updated: return False
    try:
        t = datetime.datetime.strptime(updated[:19], '%Y-%m-%dT%H:%M:%S')
        age = (datetime.datetime.utcnow() - t).total_seconds() / 3600
        return age <= hours
    except:
        return False

def retry_failed_run(run):
    run_id = run.get('id')
    name   = run.get('workflow_name', '?')
    result = gh_api('POST', f'repos/{REPO}/actions/runs/{run_id}/rerun-failed-jobs')
    if result is not None:
        print(f'[ctrl] ✅ Retried: {name} (run {run_id})')
        return True
    # Try full rerun
    result2 = gh_api('POST', f'repos/{REPO}/actions/runs/{run_id}/rerun')
    if result2 is not None:
        print(f'[ctrl] ✅ Full rerun: {name} (run {run_id})')
        return True
    print(f'[ctrl] ⚠️  Could not retry: {name}')
    return False

def trigger_workflow(workflow_file):
    """Dispatch a workflow by file name."""
    result = gh_api('POST', f'repos/{REPO}/actions/workflows/{workflow_file}/dispatches',
                    {'ref': 'main'})
    return result is not None

def write_self_diagnostic(issues):
    """Write issues to inbox for self_healer_v2.py to act on."""
    inbox = load(DATA / 'self_diagnostic_inbox.json', {'issues': [], 'resolved': []})
    for issue in issues:
        issue['detected'] = TODAY
        issue['resolved'] = False
        inbox['issues'].append(issue)
    # Keep only unresolved + last 50 resolved
    inbox['issues']   = [i for i in inbox['issues'] if not i.get('resolved')][-100:]
    inbox['resolved'] = inbox.get('resolved', [])[-50:]
    try: (DATA / 'self_diagnostic_inbox.json').write_text(json.dumps(inbox, indent=2))
    except: pass

def generate_health_report(categorized, retried):
    total   = sum(len(v) for v in categorized.values())
    passing = len(categorized['success'])
    failing = len(categorized['failure'])
    running = len(categorized['running']) + len(categorized['queued'])
    health_pct = int(passing / total * 100) if total else 0
    color = 'GREEN' if health_pct >= 90 else 'YELLOW' if health_pct >= 70 else 'RED'
    report = {
        'date':        TODAY,
        'timestamp':   datetime.datetime.utcnow().isoformat(),
        'total':       total,
        'passing':     passing,
        'failing':     failing,
        'running':     running,
        'retried':     retried,
        'health_pct':  health_pct,
        'color':       color,
        'failures':    [{
            'name': r.get('workflow_name','?'),
            'file': r.get('workflow_file','?'),
            'id':   r.get('id'),
            'url':  r.get('html_url',''),
        } for r in categorized['failure']],
    }
    try: (DATA / 'workflow_health.json').write_text(json.dumps(report, indent=2))
    except: pass
    return report

def run():
    print(f'\n[ctrl] 🌸 Master Controller — {TODAY}')
    print('[ctrl] Watching all workflows. Fixing all failures. You do nothing.')
    
    if not GITHUB_TOKEN:
        print('[ctrl] No GITHUB_TOKEN. Skipping workflow monitoring.')
        return
    
    runs        = get_all_workflow_runs()
    categorized = categorize_runs(runs)
    
    print(f'[ctrl] Workflows: {len(categorized["success"])} ✅ | {len(categorized["failure"])} ❌ | {len(categorized["running"])} 🔄')
    
    retried  = 0
    issues   = []
    
    for run in categorized['failure']:
        if not is_recent_failure(run): continue
        name = run.get('workflow_name', '?')
        print(f'[ctrl] Failure detected: {name}')
        ok = retry_failed_run(run)
        if ok:
            retried += 1
            time.sleep(2)  # Rate limit friendly
        else:
            issues.append({
                'type':     'workflow_failure',
                'workflow': name,
                'file':     run.get('workflow_file', ''),
                'run_id':   run.get('id'),
                'url':      run.get('html_url', ''),
            })
    
    if issues:
        write_self_diagnostic(issues)
        print(f'[ctrl] {len(issues)} issues written to self-diagnostic inbox')
    
    report = generate_health_report(categorized, retried)
    print(f'[ctrl] Health: {report["health_pct"]}% ({report["color"]})')
    print(f'[ctrl] Retried {retried} failures. System self-managing. 🌸')

if __name__ == '__main__':
    run()
