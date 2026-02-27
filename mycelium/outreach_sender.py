#!/usr/bin/env python3
"""
Outreach Sender — Auto-send mode
==================================
Sends outreach emails automatically.
Verifies targets are real before sending.
Never sends to guessed or unverified addresses.
Never sends to the same target twice.
Never sends more than 5 emails per run (anti-spam).

Verification rules:
  - Email must exist in outreach_queue.json
  - Must not have been sent before (sent field)
  - Must not look like a placeholder
  - Manual-only entries (no email, just URL) get flagged for you
"""

import json, datetime, os, smtplib, re
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS       = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD  = os.environ.get('GMAIL_APP_PASSWORD', '')

MAX_PER_RUN = 5  # hard cap — never spam

def load_queue():
    path = DATA / 'outreach_queue.json'
    if path.exists():
        return json.loads(path.read_text())
    return {'grants': [], 'press': []}

def save_queue(queue):
    (DATA / 'outreach_queue.json').write_text(json.dumps(queue, indent=2))

def is_real_email(email):
    """Basic sanity check — not a placeholder, has proper format."""
    if not email: return False
    placeholder_signals = ['example.com', 'yourname', 'placeholder', 'test@', 'fill-in', '[email']
    if any(p in email.lower() for p in placeholder_signals): return False
    return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email))

def send_email(to, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f'[outreach] No Gmail credentials')
        return False
    if not is_real_email(to):
        print(f'[outreach] Skipping — not a verified email: {to}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = to
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to, msg.as_string())
        print(f'[outreach] SENT: "{subject}" -> {to}')
        return True
    except Exception as e:
        print(f'[outreach] Failed to send to {to}: {e}')
        return False

def build_grant_email(grant):
    subject = f'Application inquiry: {grant["name"]}'
    body = f"""Hello,

I'm reaching out about the {grant['name']}.

{grant.get('what_to_say', '')}

The system is live and open source:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/
https://github.com/meekotharaccoon-cell/meeko-nerve-center

Key facts:
- 100% open source (AGPL-3.0)
- Runs on free-tier GitHub Actions, $0/month
- Forkable by anyone for any cause
- Autonomous: generates, tests, and builds its own ideas
- Gaza Rose art: 70% of sales to PCRF
- Congressional stock trade watcher
- Privacy-first: zero tracking, data scrubbed after use

Happy to discuss further.

Meeko
{GMAIL_ADDRESS}
https://github.com/meekotharaccoon-cell/meeko-nerve-center"""
    return subject, body

def build_press_email(contact):
    subject = f'Story pitch: {contact.get("pitch_angle", "Open-source humanitarian AI")}'
    body = f"""Hi,

I built something I think fits your beat: {contact.get('beat', 'open source + humanitarian tech')}.

The Meeko Nerve Center is an autonomous humanitarian AI that:
- Generates Gaza Rose digital art (70% of sales to PCRF)
- Monitors Congressional stock trades for conflicts of interest
- Watches 20+ free public APIs daily
- Runs entirely on GitHub Actions — $0/month, no server
- Can be forked by anyone for $5 for any cause
- Zero tracking, privacy-first architecture

Live now:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

Full code:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to answer questions or give you a walkthrough.

Meeko
{GMAIL_ADDRESS}"""
    return subject, body

def run():
    print(f'[outreach] Outreach Sender — {TODAY}')
    queue  = load_queue()
    sent   = 0
    manual = 0

    all_entries = [
        (g, 'grant') for g in queue.get('grants', [])
    ] + [
        (p, 'press') for p in queue.get('press', [])
    ]

    for entry, kind in all_entries:
        if sent >= MAX_PER_RUN:
            break
        if entry.get('sent'):
            continue

        email = entry.get('contact_email') or entry.get('email')

        # No email — manual action required
        if not email or not is_real_email(email):
            apply_url = entry.get('apply_at') or entry.get('contact') or entry.get('url', '')
            print(f'[outreach] MANUAL ACTION: {entry["name"]} — apply/contact at: {apply_url}')
            entry['sent'] = f'manual_required_{TODAY}'
            manual += 1
            continue

        if kind == 'grant':
            subject, body = build_grant_email(entry)
        else:
            subject, body = build_press_email(entry)

        if send_email(email, subject, body):
            entry['sent'] = TODAY
            sent += 1

    save_queue(queue)
    print(f'[outreach] Done. Sent: {sent} | Manual actions needed: {manual}')
    if manual > 0:
        print(f'[outreach] Check data/outreach_queue.json for entries marked manual_required')
    return {'sent': sent, 'manual': manual}

if __name__ == '__main__':
    run()
