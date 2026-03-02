#!/usr/bin/env python3
"""
SolarPunk Phone Controller
===========================
Run this from a-Shell on iOS to control your system from your phone.

Commands:
  --setup                          First-time setup, saves your GitHub token
  --status                         Show system status (revenue, jobs, grants)
  --trigger                        Trigger a full MASTER CONTROLLER cycle
  --trigger-quick                  Trigger revenue check only
  --directive "your words here"    Write a directive and trigger cycle
  --revenue                        Show all revenue data
  --jobs                           Show job applications
  --grants                         Show grant pipeline
  --wallets                        Show all wallet balances
  --distribute NAME EMAIL REGION   Send system to someone (region: gaza/sudan/drc/generic)

Examples:
  python3 phone_controller.py --status
  python3 phone_controller.py --directive "urgent: focus on grants today"
  python3 phone_controller.py --trigger
  python3 phone_controller.py --distribute "Ahmad" "ahmad@example.com" "gaza"
"""

import json, sys, os, getpass
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode
import datetime

CONFIG_FILE = Path.home() / '.solarpunk_config.json'
GITHUB_REPO = 'meekotharaccoon-cell/meeko-nerve-center'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except: pass
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    CONFIG_FILE.chmod(0o600)  # Owner read/write only

def get_token():
    cfg = load_config()
    return cfg.get('github_token', os.environ.get('GITHUB_TOKEN', ''))

def gh(path, method='GET', body=None):
    token = get_token()
    if not token:
        print('No token. Run: python3 phone_controller.py --setup')
        return None
    url = f'https://api.github.com/repos/{GITHUB_REPO}{path}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
    }
    data = json.dumps(body).encode() if body else None
    req  = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()) if r.read else {}
    except urllib_request.HTTPError as e:
        try: return json.loads(e.read())
        except: return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}

def raw_get(url, token):
    req = urllib_request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
    })
    with urllib_request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_setup():
    print('\n🌸 SolarPunk Phone Setup')
    print('This saves your GitHub token to ~/.solarpunk_config.json')
    print('Get a token at: https://github.com/settings/tokens')
    print('Needs: repo + actions scopes\n')
    token = getpass.getpass('GitHub Personal Access Token: ').strip()
    if not token:
        print('No token entered. Exiting.')
        return
    cfg = load_config()
    cfg['github_token'] = token
    cfg['repo'] = GITHUB_REPO
    cfg['setup_date'] = TODAY
    save_config(cfg)
    print('\n✅ Token saved to ~/.solarpunk_config.json (chmod 600)')
    print('Test it: python3 phone_controller.py --status')


def cmd_status():
    print(f'\n🌸 SolarPunk Status — {TODAY}\n')
    token = get_token()
    if not token:
        print('Run --setup first')
        return

    # Repo info
    try:
        repo = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}', token)
        print(f'Repo:     {repo.get("full_name")}')
        print(f'Stars:    {repo.get("stargazers_count", 0)}')
        print(f'Forks:    {repo.get("forks_count", 0)}')
        print(f'Watchers: {repo.get("watchers_count", 0)}')
    except Exception as e:
        print(f'Repo info error: {e}')

    # Latest workflow run
    try:
        runs = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=5', token)
        latest = runs.get('workflow_runs', [])
        if latest:
            r = latest[0]
            status = '✅' if r.get('conclusion') == 'success' else ('⏳' if r.get('status') == 'in_progress' else '❌')
            print(f'\nLast run: {status} {r.get("name", "?")} — {r.get("conclusion", r.get("status", "?"))}')
            print(f'  Time:   {r.get("created_at", "?")[:16]}')
    except Exception as e:
        print(f'Workflow error: {e}')

    # Traffic
    try:
        clones = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/traffic/clones', token)
        views  = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/traffic/views', token)
        print(f'\nTraffic (14d):')
        print(f'  Clones: {clones.get("uniques", "?")} unique')
        print(f'  Views:  {views.get("uniques", "?")} unique')
    except Exception as e:
        print(f'Traffic error: {e}')


def cmd_trigger(workflow='MASTER_CONTROLLER.yml'):
    print(f'\n⚡ Triggering {workflow}...')
    result = gh(f'/actions/workflows/{workflow}/dispatches',
                method='POST',
                body={'ref': 'main'})
    if result is None or result.get('message') == '':
        print('✅ Triggered! Check Actions tab for progress.')
    elif 'error' in result:
        print(f'❌ Error: {result["error"]}')
    else:
        print(f'✅ Dispatched. Result: {result}')


def cmd_directive(text):
    print(f'\n🎯 Writing directive: "{text}"')
    # Update the DIRECTIVES file via GitHub API
    # First get current file
    current = gh('/contents/data/directives_override.json')
    directives = []
    import base64
    if current and not current.get('error') and current.get('content'):
        try:
            directives = json.loads(base64.b64decode(current['content']).decode())
        except: pass

    directives.append({'date': TODAY, 'time': NOW, 'text': text, 'source': 'phone'})
    directives = directives[-10:]  # Keep last 10

    content_b64 = base64.b64encode(json.dumps(directives, indent=2).encode()).decode()
    body = {
        'message': f'phone directive: {text[:60]}',
        'content': content_b64,
    }
    if current and current.get('sha'):
        body['sha'] = current['sha']

    result = gh('/contents/data/directives_override.json', method='PUT', body=body)
    if result and not result.get('error'):
        print('✅ Directive saved to repo')
        print('Triggering cycle to apply it...')
        cmd_trigger()
    else:
        print(f'❌ Could not save directive: {result}')


def cmd_revenue():
    print(f'\n💰 Revenue Summary — {TODAY}\n')
    token = get_token()
    import base64
    for filename, label in [
        ('data/gumroad_sales.json', 'Gumroad'),
        ('data/etsy_sales.json',    'Etsy'),
        ('data/compound_tracker.json', 'Compound Tracker'),
    ]:
        try:
            result = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}', token)
            if result.get('content'):
                data = json.loads(base64.b64decode(result['content']).decode())
                if label == 'Compound Tracker':
                    print(f'All-time total:   ${data.get("total_ever", 0):.2f}')
                    print(f'All-time PCRF:    ${data.get("total_pcrf", 0):.2f}')
                    print(f'Compound balance: ${data.get("total_compound", 0):.2f}')
                else:
                    print(f'{label}: ${data.get("total_revenue_usd", 0):.2f} ({data.get("sales_count", 0)} sales)')
        except: pass


def cmd_jobs():
    print(f'\n💼 Job Agent Status — {TODAY}\n')
    token = get_token()
    import base64
    try:
        result = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/data/job_applications.json', token)
        data = json.loads(base64.b64decode(result['content']).decode())
        applied = data.get('applied', [])
        pending = data.get('pending', [])
        print(f'Applied: {len(applied)}')
        print(f'Pending review: {len(pending)}')
        if pending:
            print('\nPending applications:')
            for j in pending[:3]:
                print(f'  [{j.get("score", 0)}/10] {j.get("title", "?")} @ {j.get("company", "?")} ({j.get("platform", "?")})')
    except Exception as e:
        print(f'Error: {e}')


def cmd_distribute(name, email, region='generic'):
    print(f'\n🌍 Queuing system distribution to {name} ({email}) [{region}]...')
    token = get_token()
    import base64
    path = 'data/fork_requests.json'
    try:
        result = raw_get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}', token)
        existing = json.loads(base64.b64decode(result['content']).decode())
        sha = result['sha']
    except:
        existing = []
        sha = None

    existing.append({'name': name, 'email': email, 'region': region, 'date': TODAY, 'sent': False})
    content_b64 = base64.b64encode(json.dumps(existing, indent=2).encode()).decode()
    body = {'message': f'queue fork distribution: {email}', 'content': content_b64}
    if sha: body['sha'] = sha

    result = gh(f'/contents/{path}', method='PUT', body=body)
    if result and not result.get('error'):
        print(f'✅ Queued. Next cycle will email {name} the full system.')
    else:
        print(f'❌ Error: {result}')


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--help':
        print(__doc__)
    elif args[0] == '--setup':
        cmd_setup()
    elif args[0] == '--status':
        cmd_status()
    elif args[0] == '--trigger':
        workflow = args[1] if len(args) > 1 else 'MASTER_CONTROLLER.yml'
        cmd_trigger(workflow)
    elif args[0] == '--trigger-quick':
        cmd_trigger('revenue-check.yml')
    elif args[0] == '--directive':
        text = ' '.join(args[1:]) if len(args) > 1 else ''
        if text: cmd_directive(text)
        else: print('Usage: --directive "your words here"')
    elif args[0] == '--revenue':
        cmd_revenue()
    elif args[0] == '--jobs':
        cmd_jobs()
    elif args[0] == '--distribute':
        if len(args) >= 3:
            cmd_distribute(args[1], args[2], args[3] if len(args) > 3 else 'generic')
        else:
            print('Usage: --distribute NAME EMAIL [REGION]')
    else:
        print(f'Unknown command: {args[0]}')
        print('Run --help for commands')
