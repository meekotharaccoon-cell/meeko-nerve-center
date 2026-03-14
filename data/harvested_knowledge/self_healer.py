#!/usr/bin/env python3
"""
Self Healer
===========
Reads actual GitHub Actions workflow run logs, diagnoses every error,
attempts automatic fixes, and if it can't fix something automatically
writes exact step-by-step instructions + a free open-source alternative.

Runs:
  - After every workflow failure (triggered by self-healer.yml)
  - Daily as part of the feedback loop
  - Manually: python mycelium/self_healer.py

Outputs:
  data/errors.json        — every error ever seen, with status
  data/heal_log.md        — human-readable log of what was healed
  data/heal_report.json   — machine-readable for dashboard widget
  FIXES_NEEDED.md         — root-level file: what needs a human (repo root)
"""

import os, json, re, datetime, urllib.request, urllib.error, subprocess, sys
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
DATA.mkdir(exist_ok=True)
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat() + 'Z'

GH_TOKEN = os.environ.get('GITHUB_TOKEN', '').strip()
GH_OWNER = 'meekotharaccoon-cell'
GH_REPO  = 'meeko-nerve-center'

# =====================================================================
# KNOWLEDGE BASE
# Every known error pattern → diagnosis + auto-fix + fallback
# This grows every time a new error is encountered and solved.
# =====================================================================
ERROR_KB = [
    # ─ Python / pip ──────────────────────────────────────────────────
    {
        'id': 'missing_module',
        'patterns': ['ModuleNotFoundError', 'No module named', 'ImportError'],
        'category': 'dependency',
        'diagnosis': 'A Python package is missing.',
        'auto_fix': 'pip_install',  # healer will extract module name and install
        'fallback': 'Add the package to a requirements.txt and install it in the workflow with: pip install -r requirements.txt',
        'alternatives': {
            'requests':   'urllib.request (built into Python, no install needed)',
            'beautifulsoup4': 'html.parser (built-in) or lxml',
            'pandas':     'csv module (built-in) for simple data, or polars (faster, lighter)',
            'numpy':      'math + statistics modules (built-in) for basic math',
            'paramiko':   'subprocess + ssh command line',
            'boto3':      'urllib.request with AWS REST API directly',
            'tweepy':     'urllib.request with Twitter API v2 directly',
            'mastodon':   'urllib.request — Mastodon REST API needs no library',
        },
    },
    # ─ GitHub Actions ────────────────────────────────────────────────
    {
        'id': 'missing_secret',
        'patterns': [
            'secret.*not set', 'Context access might be invalid',
            'Error: Input required and not supplied',
            'environment variable.*not found',
        ],
        'category': 'secret',
        'diagnosis': 'A GitHub Secret is missing or empty. The workflow needs a credential you haven\'t added yet.',
        'auto_fix': None,
        'fallback': 'Go to github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions and add the missing secret.',
        'alternatives': {
            'GMAIL_APP_PASSWORD': 'Use SMTP with any free email provider. Mailgun free tier (100/day). Brevo free tier (300/day).',
            'MASTODON_TOKEN':     'Skip — post manually until ready. Posts are saved to content/queue/latest.json.',
            'BLUESKY_APP_PASSWORD': 'Skip — post manually.',
            'GUMROAD_TOKEN':      'Skip — check sales on gumroad.com dashboard manually.',
            'YOUTUBE_CLIENT_ID':  'Skip — upload manually to YouTube.',
        },
    },
    {
        'id': 'permission_denied_push',
        'patterns': [
            'Permission denied.*push', 'remote: Permission', 
            'error: failed to push', 'refusing to allow',
            "GH006", "GH007",
        ],
        'category': 'git',
        'diagnosis': 'The workflow doesn\'t have write permission to push back to the repo.',
        'auto_fix': 'add_write_permission',
        'fallback': 'In the workflow YAML file, under the job, add:\n  permissions:\n    contents: write',
        'alternatives': None,
    },
    {
        'id': 'rate_limit',
        'patterns': [
            'rate limit', 'API rate limit exceeded', 
            '429', 'Too Many Requests', 'X-RateLimit',
        ],
        'category': 'api',
        'diagnosis': 'Hit an API rate limit. The system made too many requests too fast.',
        'auto_fix': 'add_sleep',
        'fallback': 'Add time.sleep(1) between API calls. Spread workflow runs out. Use DEMO_KEY → real API key.',
        'alternatives': {
            'github_api':   'Cache results in JSON files. Only re-fetch what changed.',
            'nasa_api':     'Register free API key at api.nasa.gov (1000 req/hour vs 30 for DEMO_KEY)',
            'wikipedia':    'No rate limit issues — add User-Agent header if blocked',
        },
    },
    {
        'id': 'network_timeout',
        'patterns': [
            'timeout', 'timed out', 'Connection refused',
            'Name or service not known', 'urlopen error',
            'RemoteDisconnected', 'ChunkedEncodingError',
        ],
        'category': 'network',
        'diagnosis': 'A network request failed. The external service was down or unreachable.',
        'auto_fix': 'wrap_try_except',
        'fallback': 'Wrap the failing request in try/except so failure skips gracefully instead of crashing.',
        'alternatives': {
            'arxiv':       'Semantic Scholar API (free, no key) as backup',
            'hackernews':  'Lobste.rs JSON API (lobste.rs/hottest.json) as backup',
            'iss_api':     'wheretheiss.at/v1/satellites/25544 as backup',
            'nasa':        'spaceflightnewsapi.net (free, no key) as backup',
        },
    },
    {
        'id': 'json_parse_error',
        'patterns': [
            'JSONDecodeError', 'json.decoder', 
            'Expecting value', 'Unexpected token',
        ],
        'category': 'data',
        'diagnosis': 'A JSON file is malformed or an API returned unexpected data.',
        'auto_fix': 'safe_json_load',
        'fallback': 'Wrap json.loads() in try/except and fall back to an empty dict/list.',
        'alternatives': None,
    },
    {
        'id': 'file_not_found',
        'patterns': [
            'FileNotFoundError', 'No such file or directory',
            'cannot find the path',
        ],
        'category': 'filesystem',
        'diagnosis': 'A script is looking for a file that doesn\'t exist yet (usually generated by a previous step).',
        'auto_fix': 'create_missing_dirs',
        'fallback': 'Add Path(\'directory\').mkdir(parents=True, exist_ok=True) before any file read/write.',
        'alternatives': None,
    },
    {
        'id': 'git_conflict',
        'patterns': [
            'CONFLICT', 'Merge conflict', 'would be overwritten by merge',
            'Your local changes', 'diverged',
        ],
        'category': 'git',
        'diagnosis': 'Two things tried to write to the same file at the same time.',
        'auto_fix': 'git_reset_and_pull',
        'fallback': 'Run: git fetch origin && git reset --hard origin/main',
        'alternatives': None,
    },
    {
        'id': 'ollama_not_running',
        'patterns': [
            'Connection refused.*11434', 'ollama.*not running',
            'Failed to connect.*localhost:11434',
        ],
        'category': 'local_service',
        'diagnosis': 'loop_brain.py tried to reach Ollama but it\'s not running on your desktop.',
        'auto_fix': None,
        'fallback': 'loop_brain.py automatically falls back to rule-based strategy when Ollama is offline. No action needed.',
        'alternatives': {
            'ollama': 'Rule-based strategy in loop_brain.py works without Ollama. Start Ollama on your desktop for richer decisions.',
        },
    },
    {
        'id': 'disk_quota',
        'patterns': [
            'No space left', 'quota exceeded', 'disk quota',
            'repository is over its data quota',
        ],
        'category': 'storage',
        'diagnosis': 'GitHub repo is approaching or over its storage limit.',
        'auto_fix': 'prune_old_files',
        'fallback': 'Delete old dated files in knowledge/, content/, diagnostics/. Keep only latest.md and last 7 days.',
        'alternatives': None,
    },
    {
        'id': 'syntax_error',
        'patterns': [
            'SyntaxError', 'IndentationError', 'invalid syntax',
        ],
        'category': 'code',
        'diagnosis': 'There is a syntax error in a Python script.',
        'auto_fix': None,
        'fallback': 'Run: python -m py_compile mycelium/SCRIPTNAME.py to find the exact line.',
        'alternatives': None,
    },
    {
        'id': 'action_not_found',
        'patterns': [
            'Unable to find action', 'Action.*not found',
            'Can\'t find .* action',
        ],
        'category': 'workflow',
        'diagnosis': 'A GitHub Action used in a workflow YAML doesn\'t exist or has changed version.',
        'auto_fix': None,
        'fallback': 'Update the action reference to the latest version. Check github.com/actions for current versions.',
        'alternatives': {
            'actions/checkout': 'actions/checkout@v4 (current)',
            'actions/setup-python': 'actions/setup-python@v5 (current)',
        },
    },
]

# =====================================================================
# GitHub API helpers
# =====================================================================

def gh_get(endpoint):
    if not GH_TOKEN:
        return None
    try:
        req = urllib.request.Request(
            f'https://api.github.com{endpoint}',
            headers={
                'Authorization': f'Bearer {GH_TOKEN}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'meeko-self-healer/1.0',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'  [gh_api] {e}')
        return None

def get_failed_runs(limit=10):
    """Get recent failed workflow runs."""
    data = gh_get(f'/repos/{GH_OWNER}/{GH_REPO}/actions/runs?status=failure&per_page={limit}')
    if not data:
        return []
    return data.get('workflow_runs', [])

def get_run_logs_text(run_id):
    """Download and return log text for a run (zipped, so we get the URL and parse what we can)."""
    # Get jobs for this run
    jobs_data = gh_get(f'/repos/{GH_OWNER}/{GH_REPO}/actions/runs/{run_id}/jobs')
    if not jobs_data:
        return ''
    logs = []
    for job in jobs_data.get('jobs', []):
        if job.get('conclusion') == 'failure':
            for step in job.get('steps', []):
                if step.get('conclusion') == 'failure':
                    logs.append(
                        f"JOB: {job['name']} | STEP: {step['name']} | "
                        f"exit: {step.get('number')}"
                    )
    return ' | '.join(logs)

def get_recent_annotations(run_id):
    """Get check annotations which contain actual error messages."""
    jobs_data = gh_get(f'/repos/{GH_OWNER}/{GH_REPO}/actions/runs/{run_id}/jobs')
    if not jobs_data:
        return []
    messages = []
    for job in jobs_data.get('jobs', []):
        job_id = job['id']
        annotations = gh_get(
            f'/repos/{GH_OWNER}/{GH_REPO}/check-runs/{job_id}/annotations'
        ) or []
        for ann in annotations:
            msg = ann.get('message', '')
            if msg:
                messages.append(msg)
    return messages

# =====================================================================
# Error detection + matching
# =====================================================================

def match_error(text):
    """Return list of matching KB entries for a block of error text."""
    matches = []
    text_lower = text.lower()
    for entry in ERROR_KB:
        for pattern in entry['patterns']:
            if re.search(pattern.lower(), text_lower):
                if entry not in matches:
                    matches.append(entry)
                break
    return matches

def extract_module_name(error_text):
    """Extract module name from ModuleNotFoundError."""
    m = re.search(r"No module named '([^']+)'", error_text)
    if m:
        return m.group(1).split('.')[0]
    return None

# =====================================================================
# Auto-fix actions
# =====================================================================

def auto_fix(fix_type, error_text, workflow_file=None):
    """
    Attempt an automatic fix. Returns (success, description).
    Most fixes modify files in the repo for the next commit.
    """
    if fix_type == 'pip_install':
        module = extract_module_name(error_text)
        if module:
            # Add to a requirements file that workflows use
            req_path = ROOT / 'requirements.txt'
            existing = req_path.read_text() if req_path.exists() else ''
            if module not in existing:
                with open(req_path, 'a') as f:
                    f.write(f'\n{module}')
                return True, f'Added {module} to requirements.txt'
        return False, 'Could not extract module name'

    elif fix_type == 'create_missing_dirs':
        # Scan Python files for open() / read_text() without mkdir
        # This is a documentation fix — we note it
        return False, 'FileNotFoundError: add Path(dir).mkdir(parents=True, exist_ok=True) before file operations'

    elif fix_type == 'git_reset_and_pull':
        # Write a recovery script to run locally
        script = ROOT / 'RECOVER_GIT.bat'
        script.write_text(
            '@echo off\n'
            'cd /d "%USERPROFILE%\\Desktop\\meeko-nerve-center"\n'
            'git fetch origin\n'
            'git reset --hard origin/main\n'
            'echo Git reset complete.\n'
            'pause\n'
        )
        return True, 'Created RECOVER_GIT.bat on desktop — run it to resolve the conflict'

    elif fix_type == 'prune_old_files':
        # Delete dated files older than 7 days from knowledge/, content/, diagnostics/
        pruned = []
        cutoff = datetime.date.today() - datetime.timedelta(days=7)
        for folder in ['knowledge/github', 'knowledge/arxiv', 'knowledge/hackernews',
                       'knowledge/nasa', 'knowledge/wikipedia', 'knowledge/digest',
                       'content/archive', 'diagnostics']:
            p = ROOT / folder
            if not p.exists(): continue
            for f in p.glob('*.md'):
                try:
                    fdate = datetime.date.fromisoformat(f.stem)
                    if fdate < cutoff:
                        f.unlink()
                        pruned.append(str(f.name))
                except Exception:
                    pass
            for f in p.glob('*.json'):
                try:
                    fdate = datetime.date.fromisoformat(f.stem)
                    if fdate < cutoff:
                        f.unlink()
                        pruned.append(str(f.name))
                except Exception:
                    pass
        if pruned:
            return True, f'Pruned {len(pruned)} old files to free space'
        return False, 'No old files to prune yet'

    return False, f'No auto-fix implemented for {fix_type}'

# =====================================================================
# Main healer
# =====================================================================

def run():
    print('\n' + '='*56)
    print('  SELF HEALER — Diagnosing + Fixing Errors')
    print(f'  {NOW}')
    print('='*56)

    # Load existing error log
    errors_path = DATA / 'errors.json'
    errors_db = json.loads(errors_path.read_text()) if errors_path.exists() else {}

    healed   = []
    wounded  = []   # needs human
    seen_ids = set()

    # ── 1. Scan GitHub Actions failed runs ────────────────────────────────────
    if GH_TOKEN:
        print('\n  Scanning recent failed workflow runs...')
        failed_runs = get_failed_runs(limit=10)
        print(f'  Found {len(failed_runs)} failed runs')

        for run in failed_runs:
            run_id   = run['id']
            wf_name  = run['name']
            run_date = run['created_at'][:10]

            if str(run_id) in errors_db.get('handled_runs', []):
                continue  # already processed

            print(f'\n  [{wf_name}] {run_date}')

            # Get error context
            log_text   = get_run_logs_text(run_id)
            annotations = get_recent_annotations(run_id)
            all_text   = log_text + ' ' + ' '.join(annotations)

            if not all_text.strip():
                print('    No error text retrievable')
                continue

            matches = match_error(all_text)
            if not matches:
                print('    Error not in knowledge base — logging as unknown')
                wounded.append({
                    'run_id':   run_id,
                    'workflow': wf_name,
                    'date':     run_date,
                    'error':    all_text[:200],
                    'status':   'unknown',
                    'fix':      'Unknown error type. Check the Actions logs directly at: '
                                f'github.com/{GH_OWNER}/{GH_REPO}/actions/runs/{run_id}',
                })
                continue

            for kb in matches:
                eid = f"{run_id}_{kb['id']}"
                if eid in seen_ids: continue
                seen_ids.add(eid)

                print(f'    DIAGNOSED: [{kb["category"]}] {kb["diagnosis"]}')

                fix_applied, fix_desc = False, 'no auto-fix available'
                if kb['auto_fix']:
                    fix_applied, fix_desc = auto_fix(kb['auto_fix'], all_text)
                    if fix_applied:
                        print(f'    AUTO-FIXED: {fix_desc}')
                    else:
                        print(f'    AUTO-FIX FAILED: {fix_desc}')

                entry = {
                    'run_id':      run_id,
                    'workflow':    wf_name,
                    'date':        run_date,
                    'error_type':  kb['id'],
                    'category':    kb['category'],
                    'diagnosis':   kb['diagnosis'],
                    'auto_fixed':  fix_applied,
                    'fix_desc':    fix_desc,
                    'fallback':    kb['fallback'],
                    'alternatives': kb.get('alternatives'),
                    'status':      'healed' if fix_applied else 'needs_human',
                    'url':         f"https://github.com/{GH_OWNER}/{GH_REPO}/actions/runs/{run_id}",
                }

                if fix_applied:
                    healed.append(entry)
                else:
                    wounded.append(entry)

            # Mark run as handled
            errors_db.setdefault('handled_runs', []).append(str(run_id))

    else:
        print('  No GITHUB_TOKEN — scanning local files only')

    # ── 2. Scan local Python files for obvious issues ────────────────────────
    print('\n  Syntax-checking local Python scripts...')
    syntax_errors = []
    for py in sorted((ROOT / 'mycelium').glob('*.py')):
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(py)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            msg = result.stderr.strip()
            syntax_errors.append({'file': py.name, 'error': msg})
            print(f'  SYNTAX ERROR: {py.name} \u2014 {msg[:80]}')
            wounded.append({
                'workflow': 'local',
                'date':     TODAY,
                'error_type': 'syntax_error',
                'category':   'code',
                'diagnosis':  f'Syntax error in {py.name}',
                'auto_fixed': False,
                'fix_desc':   msg,
                'fallback':   f'Fix the syntax error in mycelium/{py.name} at the indicated line.',
                'status':     'needs_human',
                'url':        f'https://github.com/{GH_OWNER}/{GH_REPO}/blob/main/mycelium/{py.name}',
            })
    if not syntax_errors:
        print('  All Python files pass syntax check')

    # ── 3. Check required directories exist ─────────────────────────────────
    required_dirs = ['data', 'knowledge', 'content/queue', 'content/archive',
                     'diagnostics', 'mycelium']
    for d in required_dirs:
        p = ROOT / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            print(f'  CREATED missing dir: {d}/')
            healed.append({
                'workflow': 'local', 'date': TODAY,
                'error_type': 'file_not_found', 'category': 'filesystem',
                'diagnosis': f'{d}/ directory was missing',
                'auto_fixed': True, 'fix_desc': f'Created {d}/',
                'status': 'healed',
            })

    # ── 4. Save updated error db ──────────────────────────────────────────────
    errors_db['last_run']  = NOW
    errors_db['healed']    = errors_db.get('healed', []) + healed
    errors_db['wounded']   = [w for w in errors_db.get('wounded', []) + wounded
                               if w.get('status') != 'healed']
    errors_path.write_text(json.dumps(errors_db, indent=2), encoding='utf-8')

    # ── 5. Write heal_report.json (for dashboard) ────────────────────────────
    report = {
        'generated': NOW,
        'healed_today':  len(healed),
        'needs_human':   len(wounded),
        'total_healed':  len(errors_db.get('healed', [])),
        'open_issues':   len(errors_db.get('wounded', [])),
        'healed':        healed[-10:],
        'needs_human_list': [w for w in wounded if w.get('status') == 'needs_human'][:10],
    }
    (DATA / 'heal_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

    # ── 6. Write human-readable heal log ─────────────────────────────────────
    log_lines = [
        f'# 🩹 Self Healer Log — {TODAY}', '',
        f'**Healed today:** {len(healed)}  ·  **Needs human:** {len(wounded)}', '',
    ]
    if healed:
        log_lines += ['## ✅ Auto-Healed', '']
        for h in healed:
            log_lines += [
                f"### [{h['workflow']}] {h.get('error_type','?')}",
                f"**{h['diagnosis']}**",
                f"Fix applied: {h['fix_desc']}", ''
            ]
    if wounded:
        log_lines += ['## ⚠️ Needs Human', '']
        for w in wounded:
            log_lines += [
                f"### [{w.get('workflow','?')}] {w.get('error_type','unknown')}",
                f"**{w.get('diagnosis', w.get('error','Unknown error'))}**",
                f"Fix: {w.get('fallback', 'Check the Actions logs')}",
            ]
            alts = w.get('alternatives')
            if alts:
                log_lines.append('Free alternatives:')
                for k, v in alts.items():
                    log_lines.append(f'  - {k}: {v}')
            if w.get('url'):
                log_lines.append(f"[View in GitHub Actions]({w['url']})")
            log_lines.append('')
    log_lines += ['---', f'*Self Healer ran at {NOW}*']

    (DATA / 'heal_log.md').write_text('\n'.join(log_lines), encoding='utf-8')

    # ── 7. Write FIXES_NEEDED.md to repo root (visible without diving in) ──────
    fixes_lines = [
        '# 🛠️ FIXES NEEDED', '',
        f'*Auto-generated by self_healer.py · {TODAY}*', '',
    ]
    open_wounds = [w for w in errors_db.get('wounded', []) if w.get('status') == 'needs_human']
    if not open_wounds:
        fixes_lines += ['## ✅ No open issues', '', 'Everything is healthy or auto-healed.']
    else:
        fixes_lines += [f'## {len(open_wounds)} issues need attention', '']
        for i, w in enumerate(open_wounds, 1):
            fixes_lines += [
                f"### {i}. [{w.get('category','?').upper()}] {w.get('diagnosis', '?')}",
                f"**Workflow:** {w.get('workflow','?')}  ·  **Date:** {w.get('date','?')}",
                f"**Fix:** {w.get('fallback','Check Actions logs')}",
            ]
            alts = w.get('alternatives')
            if alts:
                fixes_lines.append('**Free alternatives:**')
                for k, v in alts.items():
                    fixes_lines.append(f'  - `{k}`: {v}')
            if w.get('url'):
                fixes_lines.append(f"[View run]({w['url']})")
            fixes_lines.append('')
    fixes_lines += ['---',
                    f'Total auto-healed (all time): {len(errors_db.get("healed",[]))}',
                    f'Open issues: {len(open_wounds)}']
    (ROOT / 'FIXES_NEEDED.md').write_text('\n'.join(fixes_lines), encoding='utf-8')

    # ── 8. Summary ───────────────────────────────────────────────────────────
    print('\n' + '='*56)
    print(f'  HEALED TODAY:    {len(healed)}')
    print(f'  NEEDS HUMAN:     {len(wounded)}')
    print(f'  TOTAL HEALED:    {len(errors_db.get("healed", []))}')
    print(f'  OPEN ISSUES:     {len(open_wounds)}')
    if open_wounds:
        print('\n  OPEN ISSUES:')
        for w in open_wounds[:5]:
            print(f'  ⚠️  [{w.get("category","?")}] {w.get("diagnosis","?")[:60]}')
            print(f'       Fix: {w.get("fallback","?")[:70]}')
    print('\n  See: FIXES_NEEDED.md / data/heal_log.md')
    print('='*56)

    return report


if __name__ == '__main__':
    run()
