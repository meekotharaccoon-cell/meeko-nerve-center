#!/usr/bin/env python3
"""
Outreach Sender
================
Reads data/outreach_queue.json.
Sends ONLY entries where approved: true.
You control everything. Nothing sends without your explicit approval.

Workflow:
  1. System populates outreach_queue.json with real targets
  2. YOU review each entry
  3. YOU set approved: true on ones you want sent
  4. This script runs and sends only approved entries
  5. Sent entries get marked sent: true so they don't re-send

To approve an entry:
  Open data/outreach_queue.json
  Find the entry
  Change "approved": false  to  "approved": true
  Save the file
  git add data/outreach_queue.json && git commit -m "approve: [name]" && git push
  Next workflow run will send it
"""

import json, datetime, os
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def load_queue():
    path = DATA / 'outreach_queue.json'
    if path.exists():
        return json.loads(path.read_text())
    return {'grants': [], 'press': []}

def save_queue(queue):
    (DATA / 'outreach_queue.json').write_text(json.dumps(queue, indent=2))

def send_email(to, subject, body):
    """Send via Gmail SMTP."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f'[outreach] No Gmail credentials. Cannot send to {to}')
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
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
        print(f'[outreach] Failed: {e}')
        return False

def build_grant_email(grant):
    subject = f'Application: {grant["name"]}'
    body = f"""Hello,

I'm applying for the {grant['name']}.

{grant.get('what_to_say', '')}

The system is live and open source:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/
https://github.com/meekotharaccoon-cell/meeko-nerve-center

Key facts:
- 100% open source (AGPL-3.0)
- Runs on free-tier GitHub Actions, $0/month cost
- Forkable by anyone for any cause ($5 fork guide)
- Autonomous: generates its own ideas, tests them, builds them
- Gaza Rose art: 70% of sales to PCRF (Palestinian Children's Relief Fund)
- Congress stock watcher: transparency + accountability tool
- Privacy-first: zero tracking, data scrubbed after use

I'd love to discuss how this fits {grant['name']}.

Meeko
{GMAIL_ADDRESS}
https://github.com/meekotharaccoon-cell/meeko-nerve-center"""
    return subject, body

def build_press_email(contact):
    subject = f'Story pitch: {contact["pitch_angle"]}'
    body = f"""Hi,

I built something I think fits your beat: {contact['beat']}.

The Meeko Nerve Center is an autonomous humanitarian AI that:

- Generates and sells Gaza Rose digital art (70% to PCRF)
- Monitors Congressional stock trades for conflicts of interest
- Watches 20+ free APIs daily (earthquakes, carbon, crypto, world data)
- Self-generates content, tests its own ideas, learns from failures
- Runs entirely on GitHub Actions — $0/month, no server
- Can be forked by anyone for $5 and repurposed for any cause
- Zero tracking, privacy-first architecture

It's live right now:
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

SolarPunk real-time dashboard (no account needed):
https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html

Full open source code:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to walk you through it, share more details, or answer any questions.

Meeko
{GMAIL_ADDRESS}"""
    return subject, body

def run():
    print(f'[outreach] Outreach Sender — {TODAY}')

    queue   = load_queue()
    sent    = 0
    pending = 0

    # Process grants
    for grant in queue.get('grants', []):
        if grant.get('sent'):
            continue
        if not grant.get('approved'):
            pending += 1
            print(f'[outreach] PENDING APPROVAL: {grant["name"]} (deadline: {grant.get("deadline","?")}) — set approved:true to send')
            continue
        email = grant.get('contact_email')
        if not email:
            print(f'[outreach] No email for {grant["name"]} — apply manually at {grant.get("apply_at","")}')
            grant['sent'] = f'manual_{TODAY}'
            continue
        subject, body = build_grant_email(grant)
        if send_email(email, subject, body):
            grant['sent'] = TODAY
            sent += 1

    # Process press
    for contact in queue.get('press', []):
        if contact.get('sent'):
            continue
        if not contact.get('approved'):
            pending += 1
            print(f'[outreach] PENDING APPROVAL: {contact["name"]} @ {contact["outlet"]} — set approved:true to send')
            continue
        email = contact.get('contact_email') or contact.get('email')
        if not email:
            print(f'[outreach] No email for {contact["name"]} — contact manually at {contact.get("contact","")}')
            contact['sent'] = f'manual_{TODAY}'
            continue
        subject, body = build_press_email(contact)
        if send_email(email, subject, body):
            contact['sent'] = TODAY
            sent += 1

    save_queue(queue)

    print(f'[outreach] Done. Sent: {sent} | Awaiting your approval: {pending}')
    print(f'[outreach] Review data/outreach_queue.json and set approved:true to send')
    return {'sent': sent, 'pending': pending}

if __name__ == '__main__':
    run()
