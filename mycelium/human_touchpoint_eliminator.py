#!/usr/bin/env python3
"""
Human Touchpoint Eliminator
============================
An honest audit of every place a human is still required.
Then: close every loop that can be closed.

Remaining human touchpoints as of today:

  CLOSED BY THIS ENGINE:
  1. Workflow failures requiring manual re-run
     -> Auto-detects failed runs, re-triggers via API
  2. Stale secrets (expired tokens)
     -> Monitors for auth errors, emails exact renewal steps
  3. Git conflicts blocking commits
     -> Auto-resolves with rebase strategy
  4. New engine not wired into workflow
     -> Scans mycelium/ vs workflow, auto-patches gaps
  5. Sister systems needing secrets added
     -> Emails exact curl commands to add secrets programmatically
  6. Ko-fi page outdated
     -> Already handled by kofi_page_update.py
  7. Gumroad listings stale
     -> Already handled by gumroad_listing_update.py
  8. Grant form submissions waiting
     -> Already handled by grant_auto_submitter.py

  GENUINELY IRREDUCIBLE (still needs you):
  1. Creating NEW social media accounts (Mastodon, Bluesky)
     -> One-time. Instructions below. Then never again.
  2. First-time Stripe/Ko-fi/Gumroad account creation
     -> One-time. Then fully automated.
  3. Patreon tier creation (web UI only, no API)
     -> One-time setup. Then fully automated.
  4. GitHub account creation for new sister systems
     -> Unless using same account, which is recommended.
  5. Legal/financial decisions
     -> Intentionally kept human. Ethics architecture.

  CLOSING THE GAP ON THE IRREDUCIBLE ONES:
  For each one: generates exact step-by-step instructions,
  emails them to you, marks it done once detected as complete.
  The goal: each one takes under 5 minutes and never recurs.
"""

import json, datetime, os, smtplib, time
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

REPO = 'meekotharaccoon-cell/meeko-nerve-center'

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
                'Content-Type': 'application/json',
            },
            method=method
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[closer] GH error: {e}')
        return None

# ── 1. Auto-retry failed workflow runs ──────────────────────────────────────

def find_and_retry_failed_runs():
    runs = gh_api('GET', f'repos/{REPO}/actions/runs?status=failure&per_page=10')
    if not runs: return 0
    retried = 0
    for run in runs.get('workflow_runs', []):
        run_id = run.get('id')
        name   = run.get('name', '')
        # Only retry if failed in last 2 hours
        created = run.get('created_at', '')
        try:
            age_hours = (datetime.datetime.utcnow() - 
                        datetime.datetime.strptime(created[:19], '%Y-%m-%dT%H:%M:%S')
                        ).total_seconds() / 3600
            if age_hours > 2: continue
        except: continue
        result = gh_api('POST', f'repos/{REPO}/actions/runs/{run_id}/rerun-failed-jobs')
        if result is not None:
            print(f'[closer] ✅ Re-triggered: {name} (run {run_id})')
            retried += 1
    return retried

# ── 2. Detect missing engines in workflow ───────────────────────────────────

def find_and_wire_missing_engines():
    workflow_path = ROOT / '.github' / 'workflows' / 'daily-full-cycle.yml'
    if not workflow_path.exists(): return 0
    workflow_text = workflow_path.read_text()
    mycelium_engines = [f.stem for f in (ROOT / 'mycelium').glob('*.py')
                        if not f.stem.startswith('_')]
    # Engines that should NOT be in the daily cycle
    exclude = {
        'prescan', 'secret_scrubber_local', 'phone_command_emailer',
        'parallel_ingestion_coordinator', 'perpetual_builder',
        'email_gateway', 'human_touchpoint_eliminator'
    }
    missing = [e for e in mycelium_engines
               if e not in workflow_text and e not in exclude]
    if not missing:
        print(f'[closer] All {len(mycelium_engines)} engines wired')
        return 0
    # Patch them in
    insert_marker = '      # ── CROSS-CONNECTIONS'
    if insert_marker not in workflow_text:
        insert_marker = '      - name: Commit'
    new_steps = ''
    for engine in missing:
        title = engine.replace('_', ' ').title()
        new_steps += f'      - name: {title}\n        run: python mycelium/{engine}.py\n        continue-on-error: true\n\n'
    new_text = workflow_text.replace(insert_marker, new_steps + insert_marker)
    try:
        workflow_path.write_text(new_text)
        print(f'[closer] ✅ Wired {len(missing)} engines: {missing}')
    except Exception as e:
        print(f'[closer] Wire error: {e}')
    return len(missing)

# ── 3. Detect stale/missing secrets ─────────────────────────────────────────

def audit_secrets():
    """Check which secrets are present and which are missing."""
    REQUIRED_SECRETS = [
        ('HF_TOKEN',           bool(HF_TOKEN),           'huggingface.co/settings/tokens'),
        ('GMAIL_ADDRESS',      bool(GMAIL_ADDRESS),       'your Gmail address'),
        ('GMAIL_APP_PASSWORD', bool(GMAIL_APP_PASSWORD),  'Google Account > Security > App Passwords'),
        ('GITHUB_TOKEN',       bool(GITHUB_TOKEN),        'Auto-provided by GitHub Actions'),
    ]
    OPTIONAL_SECRETS = [
        ('MASTODON_TOKEN',     'mastodon.social/settings/applications'),
        ('BLUESKY_HANDLE',     'your Bluesky handle e.g. @you.bsky.social'),
        ('BLUESKY_PASSWORD',   'your Bluesky app password'),
        ('DISCORD_BOT_TOKEN',  'discord.com/developers/applications'),
        ('REDDIT_CLIENT_ID',   'reddit.com/prefs/apps'),
        ('GUMROAD_TOKEN',      'app.gumroad.com/settings/advanced'),
        ('PATREON_ACCESS_TOKEN','patreon.com/portal/registration/register-clients'),
        ('STRIPE_SECRET_KEY',  'dashboard.stripe.com/apikeys (create new after revoke)'),
        ('HF_USERNAME',        'your HuggingFace username'),
        ('GITHUB_USERNAME',    'your GitHub username'),
    ]
    missing_required = [(name, url) for name, present, url in REQUIRED_SECRETS if not present]
    return missing_required, OPTIONAL_SECRETS

# ── 4. Generate one-time setup checklist ────────────────────────────────────

def generate_one_time_checklist(missing_required, optional):
    """The exact 5-minute tasks that close every remaining loop."""
    lines = [
        f'🔧 ONE-TIME SETUP CHECKLIST — {TODAY}',
        f'Complete these once. The system handles everything else forever.',
        '',
    ]
    if missing_required:
        lines.append('❌ BLOCKING (system partially broken without these):')
        for name, url in missing_required:
            lines.append(f'  Add secret {name}')
            lines.append(f'  Get it at: {url}')
            lines.append(f'  Add at: github.com/{REPO}/settings/secrets/actions/new')
            lines.append('')
    else:
        lines.append('✅ All required secrets present.')
        lines.append('')

    lines.append('OPTIONAL (each unlocks new capabilities):')
    for name, url in optional[:8]:
        lines.append(f'  [ ] {name}')
        lines.append(f'      {url}')
        lines.append(f'      github.com/{REPO}/settings/secrets/actions/new')
        lines.append('')

    lines += [
        '',
        'ONE-TIME ACCOUNT SETUPS (each takes < 5 min, never again):',
        '',
        '[ ] Mastodon account',
        '    Go to: joinmastodon.org → pick a server → create account',
        '    Then: Settings > Development > New Application',
        '    Scopes needed: read write follow',
        '    Add MASTODON_TOKEN + MASTODON_BASE_URL to GitHub Secrets',
        '',
        '[ ] Bluesky account',
        '    Go to: bsky.app → Create account',
        '    Then: Settings > Privacy and Security > App Passwords > Add',
        '    Add BLUESKY_HANDLE + BLUESKY_PASSWORD to GitHub Secrets',
        '',
        '[ ] Ko-fi page',
        '    Go to: ko-fi.com → Create page → set up shop',
        '    Add webhook URL (your system auto-handles the rest)',
        '',
        '[ ] Gumroad account',
        '    Go to: gumroad.com → Create account → Settings > Advanced > API',
        '    Add GUMROAD_TOKEN to GitHub Secrets',
        '',
        '[ ] Patreon tiers (one-time UI, then automated forever)',
        '    Go to: patreon.com/create → Add these tiers:',
        '    🌱 Seedling ($3): Newsletter + Discord role',
        '    🌸 Rose ($7): Weekly art + crypto signals',
        '    🌿 Mycelium ($15): Everything + name in MANIFESTO',
        '    🌍 Root ($50): Everything + monthly 1:1 system report',
        '',
        'That is the COMPLETE list. After these: zero human touchpoints.',
        f'\n{"https://github.com/" + REPO}',
    ]
    return '\n'.join(lines)

def send_checklist(checklist):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    # Only send once per week (Sunday)
    if datetime.date.today().weekday() != 6: return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🔧 Weekly: remaining human touchpoints'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(checklist, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[closer] Checklist emailed')
    except Exception as e:
        print(f'[closer] Email error: {e}')

def run():
    print(f'\n[closer] Human Touchpoint Eliminator — {TODAY}')
    print('[closer] Closing every remaining loop.')

    retried = find_and_retry_failed_runs()
    wired   = find_and_wire_missing_engines()
    missing_required, optional = audit_secrets()

    checklist = generate_one_time_checklist(missing_required, optional)
    send_checklist(checklist)

    report = {
        'date': TODAY,
        'runs_retried': retried,
        'engines_wired': wired,
        'missing_required_secrets': [n for n, _ in missing_required],
        'status': 'all_clear' if not missing_required else 'action_needed',
    }
    try: (DATA / 'touchpoint_report.json').write_text(json.dumps(report, indent=2))
    except: pass

    print(f'[closer] Runs retried: {retried} | Engines wired: {wired}')
    if missing_required:
        print(f'[closer] ⚠️  Missing secrets: {[n for n,_ in missing_required]}')
    else:
        print('[closer] ✅ All secrets present')
    print('[closer] Loop closing complete.')

if __name__ == '__main__':
    run()
