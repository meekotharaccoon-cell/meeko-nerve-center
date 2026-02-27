#!/usr/bin/env python3
"""
Grant Application Submission Engine
=====================================
Grant applications still require manual form submission.
This gets as close to zero-touch as possible.

Strategy:
  - Grants with email submission: send automatically
  - Grants with web forms: generate a pre-filled application package
    and email it to you ready to copy-paste in under 2 minutes
  - Tracks all submissions in data/grant_submissions.json
  - Never submits the same grant twice

Grant sources it monitors:
  - outreach_queue.json (grants queued by cross_engine + idea_engine)
  - data/mozilla_grant.json (Mozilla Responsible AI track)
  - data/tech_for_palestine.json
  - Hardcoded high-value grant opportunities with known submission emails
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

# Known grant opportunities with direct email submission
EMAIL_GRANTS = [
    {
        'id':       'techforpalestine_2026',
        'name':     'Tech for Palestine Open Source Grant',
        'email':    'grants@techforpalestine.org',
        'deadline': '2026-06-01',
        'max_ask':  5000,
        'focus':    'open source tools for Palestinian communities',
    },
    {
        'id':       'nlnet_2026',
        'name':     'NLnet Foundation — NGI Zero',
        'email':    'open@nlnet.nl',
        'deadline': '2026-08-01',
        'max_ask':  50000,
        'focus':    'open internet and privacy-preserving technology',
    },
    {
        'id':       'otf_2026',
        'name':     'Open Technology Fund — Core Infrastructure',
        'email':    'info@opentech.fund',
        'deadline': '2026-12-31',
        'max_ask':  300000,
        'focus':    'open source internet freedom tools',
    },
]

def ask_llm(prompt, max_tokens=800):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You write compelling, specific, honest grant applications for humanitarian open-source AI projects. Concrete impact numbers. No fluff. Direct.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[grant] LLM error: {e}')
        return None

def get_system_stats():
    """Pull live stats to make the application concrete."""
    stats = {
        'ideas_tested': 0,
        'ideas_passed': 0,
        'engines':      0,
        'uptime_days':  0,
        'auto_evolutions': 0,
    }
    try:
        ledger = json.loads((DATA / 'idea_ledger.json').read_text())
        ideas  = ledger.get('ideas', {})
        il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
        stats['ideas_tested'] = len(il)
        stats['ideas_passed'] = sum(1 for i in il if i.get('status') in ('passed','wired'))
    except: pass
    try:
        engines = list((ROOT / 'mycelium').glob('*.py'))
        stats['engines'] = len(engines)
    except: pass
    try:
        evo = json.loads((DATA / 'evolution_log.json').read_text())
        stats['auto_evolutions'] = len(evo.get('built', []))
    except: pass
    try:
        start = datetime.date(2026, 2, 1)
        stats['uptime_days'] = (datetime.date.today() - start).days
    except: pass
    return stats

def draft_application(grant, stats):
    """Write a complete grant application email."""
    prompt = f"""Write a grant application email for:

Grant: {grant['name']}
Focus: {grant['focus']}
Max award: ${grant['max_ask']:,}

Project: Meeko Nerve Center
GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Live site: https://meekotharaccoon-cell.github.io/meeko-nerve-center/

Live stats:
  - {stats['engines']} autonomous engines running on GitHub Actions
  - {stats['ideas_tested']} ideas self-tested, {stats['ideas_passed']} implemented
  - {stats['auto_evolutions']} self-built engines (system writes its own code)
  - Running {stats['uptime_days']} days with $0 monthly infrastructure cost
  - 70% of all art sales go to Palestinian children via PCRF
  - AGPL-3.0 licensed, fully forkable

The email should:
1. Open with the single most compelling thing about this project for this grant's focus
2. Describe what it does concretely (not abstractly)
3. Explain the humanitarian impact
4. Make a specific, justified ask (suggest an amount up to ${grant['max_ask']:,})
5. End with a clear call to action
6. Be under 400 words
7. Sound human, not like a grant template

Include a subject line on the first line prefixed with SUBJECT:
"""
    return ask_llm(prompt)

def send_grant_email(grant, application_text):
    """Send the grant application directly."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False

    lines = application_text.split('\n')
    subject = 'Grant Application — Meeko Nerve Center'
    body_lines = lines

    for i, line in enumerate(lines[:3]):
        if line.startswith('SUBJECT:'):
            subject = line.replace('SUBJECT:', '').strip()
            body_lines = lines[i+1:]
            break

    body = '\n'.join(body_lines).strip()

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = grant['email']
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, grant['email'], msg.as_string())
        print(f'[grant] ✅ Application sent to {grant["email"]}')
        # BCC yourself so you have a copy
        msg['To'] = GMAIL_ADDRESS
        msg['Subject'] = f'[SENT] {subject}'
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        return True
    except Exception as e:
        print(f'[grant] Send failed: {e}')
        return False

def email_application_package(grant, application_text):
    """For web-form grants, email a ready-to-paste package."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    body = f"""Grant application ready to submit — copy-paste in under 2 minutes.

Grant:    {grant['name']}
Max ask:  ${grant['max_ask']:,}
Deadline: {grant['deadline']}
Submit:   {grant.get('url', grant.get('email', 'see grant website'))}

{'='*60}
{application_text}
{'='*60}

This was drafted automatically based on live system stats.
Review, adjust the ask amount if needed, then submit.
"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📋 Grant ready: {grant["name"][:50]}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[grant] Package emailed for {grant["name"]}')
    except Exception as e:
        print(f'[grant] Email failed: {e}')

def load_submissions():
    p = DATA / 'grant_submissions.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'submitted': []}

def save_submissions(log):
    try: (DATA / 'grant_submissions.json').write_text(json.dumps(log, indent=2))
    except: pass

def run():
    print(f'\n[grant] Grant Application Engine — {TODAY}')

    if not GMAIL_ADDRESS:
        print('[grant] No GMAIL_ADDRESS. Skipping.')
        return

    log   = load_submissions()
    submitted_ids = {s['grant_id'] for s in log.get('submitted', [])}
    stats = get_system_stats()

    print(f'[grant] System stats: {stats}')

    # Also pull queued grants from outreach_queue
    queued_grants = []
    queue_path = DATA / 'outreach_queue.json'
    if queue_path.exists():
        try:
            queue = json.loads(queue_path.read_text())
            items = queue if isinstance(queue, list) else queue.get('items', [])
            for item in items:
                if item.get('type') == 'grant' and item.get('status') != 'sent':
                    queued_grants.append({
                        'id':    item.get('id', item.get('title', '')[:20]),
                        'name':  item.get('title', item.get('name', 'Unknown Grant')),
                        'email': item.get('email', item.get('contact_email', '')),
                        'deadline': item.get('deadline', '2026-12-31'),
                        'max_ask':  item.get('max_ask', 5000),
                        'focus':    item.get('focus', item.get('description', '')),
                    })
        except: pass

    all_grants = EMAIL_GRANTS + queued_grants
    sent_count = 0

    for grant in all_grants:
        grant_id = grant.get('id', grant['name'][:20])

        # Skip already submitted
        if grant_id in submitted_ids:
            print(f'[grant] Already submitted: {grant["name"]}')
            continue

        # Skip past deadline
        try:
            deadline = datetime.date.fromisoformat(grant['deadline'])
            if deadline < datetime.date.today():
                print(f'[grant] Past deadline: {grant["name"]}')
                continue
        except: pass

        print(f'[grant] Drafting application: {grant["name"]}')
        application = draft_application(grant, stats)
        if not application:
            print(f'[grant] Could not draft application. Skipping.')
            continue

        # Send directly if email grant, otherwise package for you
        success = False
        if grant.get('email') and '@' in grant['email']:
            success = send_grant_email(grant, application)
        else:
            email_application_package(grant, application)
            success = True  # packaged = success

        if success:
            log['submitted'].append({
                'grant_id':   grant_id,
                'grant_name': grant['name'],
                'date':       TODAY,
                'method':     'email' if grant.get('email') else 'packaged',
            })
            save_submissions(log)
            sent_count += 1

        # Max 2 per run to avoid spam
        if sent_count >= 2:
            break

    print(f'[grant] Done. Applications processed: {sent_count}')

if __name__ == '__main__':
    run()
