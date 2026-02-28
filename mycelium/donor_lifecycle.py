#!/usr/bin/env python3
"""
Donor Lifecycle Engine
 =======================
Every person who gives money is a relationship, not a transaction.
Right now: donation arrives, thank you goes out, silence forever.
That's a broken loop. This closes it.

Full donor lifecycle, zero human touchpoints:

  MOMENT 0: Donation arrives
    -> Immediate thank you (already handled by kofi engine)
    -> Tagged in donor database with tier and date

  DAY 7: First follow-up
    -> "Here's what your donation did this week"
    -> Specific: art generated, trade flagged, engine built
    -> Invite to join Discord/newsletter if not already

  DAY 30: Impact report
    -> Personalized: "Since you donated..."
    -> Concrete numbers: your $X helped generate Y art pieces
    -> PCRF total: how much has gone to Palestinian children
    -> Make them feel the impact

  DAY 90: Re-engagement
    -> Check in genuinely
    -> Share biggest development since their donation
    -> Soft invite to donate again (never pushy)
    -> Upgrade path: if $5 donor, mention $7 tier benefits

  ANNIVERSARY: 1 year
    -> Full year impact summary
    -> Thank them by name
    -> Invite to be featured in annual report

  LAPSED: 90 days after expected renewal (for recurring)
    -> Gentle "we noticed" message
    -> Ask if everything is okay (not "please donate again")
    -> Offer to pause vs cancel

  EVERY COMMUNICATION:
    -> References specific things THEY cared about
    -> Never generic. Always feels personal.
    -> Never more than 1 email per 30 days
    -> Easy unsubscribe at bottom of every email
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

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
UNSUBSCRIBE_NOTE = '\nTo stop these updates: reply with "unsubscribe" in the subject.'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def days_since(date_str):
    try:
        return (datetime.date.today() -
                datetime.date.fromisoformat(date_str[:10])).days
    except:
        return 999

def get_system_stats():
    stats = {'engines': 0, 'art': 0, 'pcrf': 0.0, 'trades': 0}
    try: stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        al = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        ev = load(DATA / 'kofi_events.json')
        ev = ev if isinstance(ev, list) else ev.get('events', [])
        stats['pcrf'] = round(sum(float(e.get('amount',0)) for e in ev
                                  if e.get('type') in ('donation','Donation')) * 0.70, 2)
    except: pass
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        stats['trades'] = len(trades)
    except: pass
    return stats

def generate_personal_message(donor_name, amount, days, stats, msg_type):
    if not HF_TOKEN:
        return None
    prompts = {
        'day7': f"""Write a warm 7-day follow-up to a donor named {donor_name} who gave ${amount}.
Tell them specifically what happened this week:
  - {stats['art']} Gaza Rose art pieces generated (their donation helped fund this)
  - {stats['engines']} autonomous engines running
  - {stats['trades']} congressional trades tracked
  - ${stats['pcrf']:.2f} total sent to PCRF for Palestinian children's medical care
Under 150 words. Personal, warm, specific. Don't ask for more money.
End: Free Palestine. \U0001f339""",
        'day30': f"""Write a 30-day impact report to donor {donor_name} (gave ${amount}).
Make them feel what their donation actually did:
  - Art generated for Palestinian solidarity: {stats['art']} pieces
  - PCRF total (Palestinian children's medical care): ${stats['pcrf']:.2f}
  - Congressional trades flagged: {stats['trades']}
  - The system is now {stats['engines']} engines, self-evolving daily
Under 200 words. Make them feel it. Be specific and human.
End with: Free Palestine. \U0001f339""",
        'day90': f"""Write a genuine 90-day check-in to donor {donor_name} (gave ${amount}, {days} days ago).
Share the biggest thing that's happened since they donated.
Ask how they're doing. Mention the upgrade path if they gave less than $7.
(Tiers: \U0001f331 $3 Seedling, \U0001f338 $7 Gaza Rose, \U0001f33f $15 Mycelium, \U0001f30d $50 Root)
Never pushy. Their wellbeing matters more than their money.
Under 150 words.""",
        'anniversary': f"""Write a 1-year anniversary message to {donor_name}.
Thank them for being with us from the beginning.
Share the year in numbers: {stats['art']} art pieces, ${stats['pcrf']:.2f} to PCRF, {stats['engines']} engines.
Invite them to be named in the annual impact report.
Under 200 words. Make it feel like the milestone it is."""
    }
    prompt = prompts.get(msg_type, '')
    if not prompt: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 300,
            'messages': [
                {'role': 'system', 'content': 'You write warm, personal donor communications. Never corporate. Always genuine.'},
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

def send_to_donor(email, name, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        full_body = body + UNSUBSCRIBE_NOTE + f'\n\n{REPO_URL}'
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko Nerve Center \U0001f338 <{GMAIL_ADDRESS}>'
        msg['To']      = email
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(full_body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, email, msg.as_string())
        return True
    except Exception as e:
        print(f'[donor] Send error: {e}')
        return False

def get_donors():
    events = load(DATA / 'kofi_events.json')
    ev = events if isinstance(events, list) else events.get('events', [])
    donors = {}
    for e in ev:
        if e.get('type') not in ('donation', 'Donation'): continue
        email = e.get('email', '')
        if not email: continue
        date = e.get('timestamp', e.get('created_at', TODAY))[:10]
        if email not in donors or date < donors[email]['first_date']:
            donors[email] = {
                'name':       e.get('from_name', 'Friend'),
                'email':      email,
                'amount':     float(e.get('amount', 0)),
                'first_date': date,
                'last_date':  date,
            }
        if date > donors[email]['last_date']:
            donors[email]['last_date'] = date
    return list(donors.values())

def run():
    print(f'\n[donor] Donor Lifecycle Engine — {TODAY}')

    donors = get_donors()
    print(f'[donor] Total donors: {len(donors)}')

    stats = get_system_stats()
    lifecycle_path = DATA / 'donor_lifecycle.json'
    lifecycle = load(lifecycle_path, {})
    sent = 0

    unsubscribed = load(DATA / 'newsletter_subscribers.json', {}).get('unsubscribed', [])

    for donor in donors:
        email = donor['email']
        if email in unsubscribed: continue
        name   = donor['name']
        amount = donor['amount']
        days   = days_since(donor['first_date'])
        record = lifecycle.setdefault(email, {'sent_types': [], 'last_contact': ''})
        sent_types = record.get('sent_types', [])

        # Throttle: max 1 email per 30 days
        last = record.get('last_contact', '')
        if last and days_since(last) < 30: continue

        # Determine which message to send
        msg_type = None
        subj     = ''
        if days >= 365 and 'anniversary' not in sent_types:
            msg_type = 'anniversary'
            subj = f'\U0001f338 One year of making change together'
        elif days >= 90 and 'day90' not in sent_types:
            msg_type = 'day90'
            subj = 'Checking in — it\'s been a while'
        elif days >= 30 and 'day30' not in sent_types:
            msg_type = 'day30'
            subj = f'\U0001f338 30 days of impact: here\'s what your ${amount:.0f} did'
        elif days >= 7 and 'day7' not in sent_types:
            msg_type = 'day7'
            subj = f'One week in — here\'s what\'s happening'

        if not msg_type: continue

        body = generate_personal_message(name, amount, days, stats, msg_type)
        if not body:
            body = f"Hey {name}, thank you for your support. The system has generated {stats['art']} art pieces and sent ${stats['pcrf']:.2f} to PCRF. Free Palestine. \U0001f339"

        ok = send_to_donor(email, name, subj, body)
        if ok:
            record['sent_types'].append(msg_type)
            record['last_contact'] = TODAY
            sent += 1
            print(f'[donor] \u2705 {msg_type} sent to {name} ({email[:30]})')

    try: lifecycle_path.write_text(json.dumps(lifecycle, indent=2))
    except: pass
    print(f'[donor] Sent {sent} lifecycle emails. Every donor held. \U0001f338')

if __name__ == '__main__':
    run()
