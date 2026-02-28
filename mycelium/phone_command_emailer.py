#!/usr/bin/env python3
"""
Phone Command Emailer
======================
Emails all key system commands in a-Shell format.
Every command prefixed with [~meeko_phone_package]$
Copy-paste ready. No thinking required.

Includes:
  - How to trigger any workflow from your phone
  - How to check system status
  - How to push files
  - How to check logs
  - Emergency commands (force run, manual override)
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')

REPO = 'meekotharaccoon-cell/meeko-nerve-center'

COMMANDS = [
    ('SETUP (run once)', [
        ('Install git', 'pkg install git'),
        ('Configure git name', 'git config --global user.name "meeko"'),
        ('Configure git email', 'git config --global user.email "meekotharaccoon@gmail.com"'),
        ('Clone repo', f'git clone https://github.com/{REPO}.git'),
        ('Enter repo', 'cd meeko-nerve-center'),
    ]),
    ('DAILY USE', [
        ('Pull latest', 'git pull'),
        ('Check status', 'git status'),
        ('See recent commits', 'git log --oneline -10'),
        ('Add all changes', 'git add -A'),
        ('Commit changes', 'git commit -m "phone: manual update"'),
        ('Push changes', 'git push'),
    ]),
    ('TRIGGER WORKFLOWS (curl)', [
        ('Trigger full daily cycle',
         f'curl -X POST -H "Authorization: Bearer YOUR_GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/repos/{REPO}/actions/workflows/daily-full-cycle.yml/dispatches -d \'{{"ref":"main"}}\''),
        ('Trigger parallel ingestion',
         f'curl -X POST -H "Authorization: Bearer YOUR_GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/repos/{REPO}/actions/workflows/parallel-ingest.yml/dispatches -d \'{{"ref":"main"}}\''),
        ('Trigger master (triggers all)',
         f'curl -X POST -H "Authorization: Bearer YOUR_GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/repos/{REPO}/actions/workflows/master.yml/dispatches -d \'{{"ref":"main"}}\''),
    ]),
    ('CHECK STATUS', [
        ('List running workflows',
         f'curl -H "Authorization: Bearer YOUR_GITHUB_TOKEN" https://api.github.com/repos/{REPO}/actions/runs?status=in_progress | python3 -c "import json,sys; runs=json.load(sys.stdin)[\'workflow_runs\']; [print(r[\'name\'],r[\'status\']) for r in runs[:5]]"'),
        ('See latest run',
         f'curl -H "Authorization: Bearer YOUR_GITHUB_TOKEN" https://api.github.com/repos/{REPO}/actions/runs?per_page=1 | python3 -c "import json,sys; r=json.load(sys.stdin)[\'workflow_runs\'][0]; print(r[\'name\'],r[\'status\'],r[\'conclusion\'])"'),
        ('Check ingestion progress',
         'cat data/ingestion_progress.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\'Done: {len(d.get(\\"processed\\",[]))}/{d.get(\\"total_found\\",0)}\'"'),
    ]),
    ('FILE OPERATIONS', [
        ('Add a file to solarpunk folder', 'cp /path/to/file solarpunk/ && git add solarpunk/ && git commit -m "add: new file" && git push'),
        ('See what changed today', 'git log --oneline --since="24 hours ago"'),
        ('Check data folder', 'ls data/'),
        ('Read latest signals', 'cat data/crypto_signals_queue.json'),
        ('Read health report', 'cat data/health_report.json'),
    ]),
    ('EMERGENCY', [
        ('Force re-run self evolution', 'python3 mycelium/self_evolution.py'),
        ('Force re-run crypto signals', 'python3 mycelium/crypto_signals.py'),
        ('Run secret scrubber dry run', 'python3 mycelium/secret_scrubber_local.py --dry-run'),
        ('Run secret scrubber LIVE', 'python3 mycelium/secret_scrubber_local.py'),
        ('Check for broken engines', 'python3 mycelium/system_health_alerting.py'),
    ]),
]

def build_email():
    lines = [
        f'Meeko Phone Command Package — {TODAY}',
        f'a-Shell / iSH / Termux compatible',
        f'Replace YOUR_GITHUB_TOKEN with your actual token',
        f'',
        f'Get a GitHub token: github.com/settings/tokens/new',
        f'  Scopes needed: repo, workflow',
        f'',
        '=' * 60,
        '',
    ]

    for section, commands in COMMANDS:
        lines.append(f'\n━━ {section} ' + '━' * (40 - len(section)))
        for label, cmd in commands:
            lines.append(f'\n# {label}')
            lines.append(f'[~meeko_phone_package]$ {cmd}')

    lines += [
        '',
        '=' * 60,
        '',
        'QUICK REFERENCE:',
        '  Full cycle:    workflow dispatch daily-full-cycle.yml',
        '  Fast ingest:   workflow dispatch parallel-ingest.yml',
        '  Check status:  git log --oneline -5',
        '  Emergency:     python3 mycelium/error_self_healing.py',
        '',
        f'Repo: https://github.com/{REPO}',
    ]
    return '\n'.join(lines)

def run():
    print(f'\n[phone] Phone Command Emailer — {TODAY}')
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[phone] No Gmail credentials.')
        return

    body = build_email()
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📱 Meeko Phone Commands — copy-paste ready'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[phone] ✅ Phone commands emailed')
    except Exception as e:
        print(f'[phone] Email error: {e}')

if __name__ == '__main__':
    run()
