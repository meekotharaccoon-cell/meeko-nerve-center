#!/usr/bin/env python3
"""
System Health Alerting Engine
================================
Generates a daily health score and alerts if critical engines are broken.

Scores each engine:
  - Ran today and produced output: 100
  - Ran but no output detected: 60
  - Did not run / failed: 0

Overall score = average across all engines.
Alerts you if score drops below 70.
Includes health score in daily status email via data/health_report.json.
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO        = 'meekotharaccoon-cell/meeko-nerve-center'

ALERT_THRESHOLD = 70

# Map engine names to output files they should produce/update
ENGINE_OUTPUTS = {
    'idea_engine':           DATA / 'idea_ledger.json',
    'world_intelligence':    DATA / 'world_state.json',
    'donation_engine':       DATA / 'donation_context.json',
    'crypto_wallet_display': DATA / 'wallet_balances.json',
    'content_performance':   DATA / 'content_performance.json',
    'language_engine':       ROOT / 'knowledge' / 'language' / 'word_of_day.json',
    'open_library_reader':   DATA / 'books.json',
    'music_intelligence':    DATA / 'music.json',
    'email_responder':       DATA / 'email_log.json',
    'autonomy_audit':        DATA / 'autonomy_audit.json',
    'error_self_healing':    DATA / 'healing_log.json',
    'self_evolution':        DATA / 'evolution_log.json',
}

def score_engine(name, output_path):
    """Return (score 0-100, status string) for one engine."""
    if not output_path.exists():
        return 0, 'no output file'
    try:
        mtime = datetime.datetime.fromtimestamp(output_path.stat().st_mtime).date()
        if mtime.isoformat() == TODAY:
            return 100, 'ran today'
        days_ago = (datetime.date.today() - mtime).days
        if days_ago <= 1:
            return 80, 'ran yesterday'
        if days_ago <= 3:
            return 50, f'last ran {days_ago}d ago'
        return 20, f'stale ({days_ago}d ago)'
    except:
        return 0, 'error checking'

def get_workflow_health():
    """Check GitHub Actions for failed steps in the last run."""
    if not GITHUB_TOKEN: return None
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=1&status=completed'
        headers = {
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github+json',
        }
        req = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(req, timeout=15) as r:
            runs = json.loads(r.read())
        if not runs.get('workflow_runs'): return None
        run = runs['workflow_runs'][0]
        return {
            'conclusion':   run.get('conclusion'),
            'run_number':   run.get('run_number'),
            'created_at':   run.get('created_at','')[:10],
        }
    except:
        return None

def send_alert(score, report):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    failing = [r for r in report if r['score'] < 50]
    lines = [
        f'System health score: {score}/100 — below alert threshold ({ALERT_THRESHOLD})',
        '',
        'Engines with issues:',
    ]
    for r in failing:
        lines.append(f'  [{r["score"]:3d}] {r["engine"]:30s} {r["status"]}')
    lines += ['', 'The self-healing engine should address code failures automatically.']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'⚠️ System health: {score}/100'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[health] Alert sent: score={score}')
    except Exception as e:
        print(f'[health] Alert email failed: {e}')

def run():
    print(f'\n[health] System Health Alerting — {TODAY}')

    report = []
    for name, path in ENGINE_OUTPUTS.items():
        score, status = score_engine(name, path)
        report.append({'engine': name, 'score': score, 'status': status})

    report.sort(key=lambda r: r['score'])
    overall = round(sum(r['score'] for r in report) / max(len(report), 1))

    wf = get_workflow_health()

    health = {
        'date':             TODAY,
        'score':            overall,
        'engines':          report,
        'alert_threshold':  ALERT_THRESHOLD,
        'alerted':          overall < ALERT_THRESHOLD,
        'workflow':         wf,
    }

    try:
        (DATA / 'health_report.json').write_text(json.dumps(health, indent=2))
    except Exception as e:
        print(f'[health] Save error: {e}')

    print(f'[health] Score: {overall}/100')
    for r in report:
        icon = '✅' if r['score'] >= 80 else ('⚠️' if r['score'] >= 50 else '❌')
        print(f'[health]   {icon} {r["engine"]:30s} {r["score"]:3d} — {r["status"]}')

    if overall < ALERT_THRESHOLD:
        print(f'[health] Score below {ALERT_THRESHOLD}! Sending alert.')
        send_alert(overall, report)
    else:
        print(f'[health] System healthy.')

if __name__ == '__main__':
    run()
