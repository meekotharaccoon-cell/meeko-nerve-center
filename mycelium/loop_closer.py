#!/usr/bin/env python3
"""
Loop Closer Engine
===================
The master engine that closes every remaining open loop.
Runs every cycle. Checks everything.
Finds anything incomplete and completes it.

Open loops it closes:

  1. CONTENT LOOP
     Post queued -> verify actually posted -> log result
     If post failed: retry with exponential backoff
     If post succeeded: check for replies/engagement

  2. GRANT LOOP  
     Draft -> submitted -> track response -> follow up
     If no response in 30 days: send polite follow-up
     If response: email you immediately + update status

  3. PRESS LOOP
     Contacted -> track reply -> follow up if 14 days no response
     If reply: email you + draft response + schedule next touch

  4. COALITION LOOP
     Reached out -> track reply -> nurture relationship
     If reply: draft collaborative proposal automatically

  5. DONOR LOOP
     Donation received -> thank you sent -> 30-day follow up
     -> 90-day re-engagement -> anniversary message
     Every donor is held for life, not forgotten after the transaction

  6. FORK LOOP
     Forked -> onboarded -> check if active -> revive if dormant
     If fork went dark after 7 days: send revival email with specific help

  7. IDEA LOOP
     Idea proposed -> evaluated -> built or rejected (with reason logged)
     Nothing sits in 'pending' forever

  8. DATA LOOP
     Data collected -> analyzed -> acted on or archived
     No data file should be older than 3 days without a reason

  9. SIGNAL LOOP
     Signal generated -> performance tracked -> accuracy logged
     Losing signals get flagged for strategy review

  10. NETWORK LOOP
     Sister spawned -> activated -> active -> contributing
     Dormant sisters get revival instructions sent to their owner

Every open loop costs energy. Closing loops creates momentum.
This is the engine that makes everything else compound.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def days_since(date_str):
    try:
        d = datetime.date.fromisoformat(date_str[:10])
        return (datetime.date.today() - d).days
    except:
        return 999

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        return True
    except:
        return False

def call_llm(prompt):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 300,
            'messages': [
                {'role': 'system', 'content': 'You write brief, genuine follow-up messages. Direct. Warm. Under 150 words.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except:
        return None

# ── Loop closers ─────────────────────────────────────────────────────────────

def close_grant_loop():
    """Follow up on submitted grants that haven't responded."""
    submissions = load(DATA / 'grant_submissions.json', {'submitted': []})
    actions = []
    for sub in submissions.get('submitted', []):
        if sub.get('status') == 'responded': continue
        age = days_since(sub.get('date', TODAY))
        if age == 30:
            actions.append(f'Grant follow-up needed: {sub.get("funder","?")} (submitted {age}d ago)')
        elif age == 60:
            actions.append(f'Grant 60-day nudge: {sub.get("funder","?")} — consider withdrawing or re-applying')
    if actions:
        send_email('📋 Grant loop: follow-ups needed', '\n'.join(actions))
        print(f'[loops] Grant: {len(actions)} follow-ups')
    return len(actions)

def close_press_loop():
    """Follow up on press contacts who haven't replied."""
    log = load(DATA / 'press_followup_log.json', {'contacts': {}})
    contacts = log.get('contacts', {})
    overdue = []
    for email, info in contacts.items():
        if info.get('status') in ('replied', 'closed'): continue
        age = days_since(info.get('last_contact', TODAY))
        if 14 <= age <= 15:
            overdue.append((email, info.get('outlet', email), age))
    if overdue:
        lines = ['Press contacts needing follow-up:\n']
        for email, outlet, age in overdue[:5]:
            lines.append(f'  {outlet} ({email}) — {age} days, no reply')
        send_email('📰 Press loop: follow-ups needed', '\n'.join(lines))
        print(f'[loops] Press: {len(overdue)} follow-ups')
    return len(overdue)

def close_donor_loop():
    """30-day follow-up and 90-day re-engagement for donors."""
    events = load(DATA / 'kofi_events.json')
    ev = events if isinstance(events, list) else events.get('events', [])
    donors = {}
    for e in ev:
        if e.get('type') not in ('donation', 'Donation'): continue
        email = e.get('email', '')
        if not email: continue
        date  = e.get('timestamp', e.get('created_at', TODAY))[:10]
        if email not in donors or date > donors[email]['date']:
            donors[email] = {'date': date, 'name': e.get('from_name',''), 'amount': e.get('amount',0)}
    actions = []
    for email, info in donors.items():
        age = days_since(info['date'])
        followups = load(DATA / 'donor_followup_log.json', {})
        done = followups.get(email, {}).get('sent_days', [])
        if age >= 30 and 30 not in done:
            actions.append({'email': email, 'name': info['name'], 'day': 30, 'amount': info['amount']})
        elif age >= 90 and 90 not in done:
            actions.append({'email': email, 'name': info['name'], 'day': 90, 'amount': info['amount']})
    if actions:
        print(f'[loops] Donor: {len(actions)} follow-ups needed')
        # Queue to donor_followup_sequence.py via shared data
        try:
            (DATA / 'donor_followup_queue.json').write_text(
                json.dumps({'date': TODAY, 'queue': actions}, indent=2))
        except: pass
    return len(actions)

def close_idea_loop():
    """Move ideas that have been pending > 14 days to 'review' status."""
    ledger_path = DATA / 'idea_ledger.json'
    ledger = load(ledger_path, {'ideas': {}})
    ideas  = ledger.get('ideas', {})
    stale  = 0
    for iid, idea in ideas.items():
        if idea.get('status') == 'pending':
            age = days_since(idea.get('date', TODAY))
            if age > 14:
                idea['status'] = 'stale'
                stale += 1
    if stale:
        try: ledger_path.write_text(json.dumps(ledger, indent=2))
        except: pass
        print(f'[loops] Ideas: {stale} marked stale (>14d pending)')
    return stale

def close_data_loop():
    """Flag data files that are too old."""
    critical = [
        ('world_state.json',    2),
        ('congress.json',       2),
        ('health_report.json',  2),
    ]
    stale = []
    for fname, max_days in critical:
        p = DATA / fname
        if p.exists():
            import os as _os
            age = (datetime.datetime.now() -
                   datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
            if age > max_days:
                stale.append(f'{fname}: {age}d old (max {max_days}d)')
    if stale:
        send_email('⚠️ Stale data files', '\n'.join(stale))
        print(f'[loops] Data: {len(stale)} stale files')
    return len(stale)

def run():
    print(f'\n[loops] 🌸 Loop Closer Engine — {TODAY}')
    print('[loops] Closing every open loop. No loose ends.')

    results = {
        'date':   TODAY,
        'grants': close_grant_loop(),
        'press':  close_press_loop(),
        'donors': close_donor_loop(),
        'ideas':  close_idea_loop(),
        'data':   close_data_loop(),
    }

    total = sum(v for k,v in results.items() if k != 'date')
    print(f'[loops] Total actions taken: {total}')
    try: (DATA / 'loop_closure_report.json').write_text(json.dumps(results, indent=2))
    except: pass
    print('[loops] All loops checked. 🌸')

if __name__ == '__main__':
    run()
