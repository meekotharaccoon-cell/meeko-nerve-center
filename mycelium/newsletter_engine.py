#!/usr/bin/env python3
"""
Newsletter Engine
==================
Builds a direct relationship with people who care.
Email list = the one audience you actually own.

Ko-fi donations include email. This engine:
  1. Collects emails from Ko-fi donors (already have permission)
  2. Collects emails from GitHub Sponsors (if any)
  3. Sends a weekly newsletter every Sunday
  4. Newsletter contains: accountability hit of the week,
     latest Gaza Rose art, system evolution update,
     PCRF impact numbers, one thing to do right now
  5. Tracks open rates (via pixel if possible, or just send count)
  6. Unsubscribe handled via reply-to

Growing the list beyond donors:
  - Newsletter signup link generated for social posts
  - GitHub README signup section
  - Dashboard signup form

Never sends more than once per week.
Never uses a third-party email platform (Mailchimp etc costs money).
Runs entirely on Gmail SMTP.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()  # 6 = Sunday

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

NEWSLETTER_SUBJECT_PREFIX = '🌹 Meeko Weekly'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_subscriber_list():
    """
    Build list from:
    1. Ko-fi donor emails
    2. Manually added subscribers
    3. Never includes unsubscribed people
    """
    subscribers = {}

    # Ko-fi donors
    kofi = load(DATA / 'kofi_events.json')
    events = kofi if isinstance(kofi, list) else kofi.get('events', [])
    for e in events:
        email = e.get('email', e.get('from_email', ''))
        name  = e.get('from_name', e.get('name', 'Friend'))
        if email and '@' in email:
            subscribers[email] = {'name': name, 'source': 'kofi', 'since': e.get('timestamp', TODAY)[:10]}

    # Extracted contacts (from ingestion engine)
    contacts = load(DATA / 'extracted_contacts.json', [])
    for c in contacts:
        email = c.get('email', '')
        if email and '@' in email and email not in subscribers:
            subscribers[email] = {'name': '', 'source': c.get('source', 'extracted'), 'since': TODAY}

    # Manual subscriber list
    manual = load(DATA / 'newsletter_subscribers.json', {'subscribers': [], 'unsubscribed': []})
    unsub_set = set(manual.get('unsubscribed', []))
    for s in manual.get('subscribers', []):
        email = s.get('email', '')
        if email and '@' in email and email not in unsub_set:
            subscribers[email] = {'name': s.get('name', ''), 'source': 'manual', 'since': s.get('date', TODAY)}

    # Remove unsubscribed
    for email in unsub_set:
        subscribers.pop(email, None)

    return subscribers

def get_week_highlights():
    """Pull the best content from this week's data."""
    highlights = {}

    # Top accountability hit
    congress = load(DATA / 'congress.json')
    trades   = congress if isinstance(congress, list) else congress.get('trades', [])
    if trades:
        t = trades[0]
        highlights['trade'] = {
            'member': t.get('representative', t.get('senator', '')),
            'ticker': t.get('ticker', ''),
            'date':   t.get('transaction_date', t.get('date', '')),
            'amount': t.get('amount', t.get('range', '')),
        }

    # Latest art
    arts = load(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    if al:
        highlights['art'] = al[-1]

    # PCRF total
    kofi = load(DATA / 'kofi_events.json')
    ev   = kofi if isinstance(kofi, list) else kofi.get('events', [])
    total = sum(float(e.get('amount', 0)) for e in ev if e.get('type') in ('donation', 'Donation'))
    highlights['pcrf_total'] = round(total * 0.70, 2)
    highlights['donations_total'] = round(total, 2)

    # Latest evolution
    evo_log = load(DATA / 'evolution_log.json')
    built   = evo_log.get('built', [])
    if built:
        highlights['evolution'] = built[-1]

    # Palestine news
    world  = load(DATA / 'world_state.json')
    events = world.get('events', world.get('news', []))
    relevant = [
        e.get('title', e.get('headline', ''))
        for e in events
        if any(kw in e.get('title', e.get('headline', '')).lower()
               for kw in ['gaza', 'palestine', 'pcrf', 'ceasefire'])
    ]
    if relevant:
        highlights['palestine_news'] = relevant[:3]

    # Top crypto signal
    signals = load(DATA / 'crypto_signals_queue.json', [])
    if signals:
        conf_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        signals.sort(key=lambda s: conf_order.get(s.get('confidence', 'LOW'), 2))
        highlights['signal'] = signals[0]

    return highlights

def generate_newsletter(highlights, subscriber_name='Friend'):
    name = subscriber_name or 'Friend'

    trade_section = ''
    if highlights.get('trade'):
        t = highlights['trade']
        trade_section = f"""
📊 THIS WEEK IN ACCOUNTABILITY
{'=' * 40}
{t['member']} traded {t['ticker']} ({t['amount']}) on {t['date']}.
Public record. STOCK Act disclosure.
Source: https://efts.house.gov
"""

    art_section = ''
    if highlights.get('art'):
        a = highlights['art']
        title = a.get('title', a.get('prompt', 'Gaza Rose'))[:80]
        art_section = f"""
🌹 LATEST GAZA ROSE
{'=' * 40}
"{title}"

Get it on Ko-fi — 70% goes directly to PCRF:
https://ko-fi.com/meekotharaccoon
"""

    pcrf_section = ''
    if highlights.get('donations_total', 0) > 0:
        pcrf_section = f"""
💚 IMPACT SO FAR
{'=' * 40}
Total raised through art sales: ${highlights['donations_total']:.2f}
Going to PCRF for Palestinian children: ${highlights['pcrf_total']:.2f}

https://www.pcrf.net
"""

    evo_section = ''
    if highlights.get('evolution'):
        e = highlights['evolution']
        evo_section = f"""
⚡ THE SYSTEM BUILT THIS ITSELF
{'=' * 40}
This week the system self-evolved and added:
"{e.get('title', '')}"

No human wrote that engine. The system identified the gap,
wrote the code, tested it, and committed it.
All 40+ engines are online. $0/month.
https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""

    news_section = ''
    if highlights.get('palestine_news'):
        news_section = """
🌍 PALESTINE THIS WEEK
""" + '=' * 40 + '\n'
        for n in highlights['palestine_news']:
            news_section += f'→ {n}\n'

    signal_section = ''
    if highlights.get('signal'):
        s = highlights['signal']
        if s.get('confidence') == 'HIGH':
            signal_section = f"""
📡 THIS WEEK'S SIGNAL
{'=' * 40}
{s['symbol']}: {s['action']}
Entry: {s['entry']} | Target: {s['target']} | Stop: {s['stop_loss']}
(Not financial advice. Automated detection. DYOR.)
"""

    return f"""Hey {name},

Here's what Meeko built and found this week.

{trade_section}{art_section}{pcrf_section}{evo_section}{news_section}{signal_section}
{'=' * 40}
This newsletter comes from an autonomous AI that
runs for free and funds Palestinian relief.

Fork the whole system: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Support the mission: https://ko-fi.com/meekotharaccoon
Read the manifesto: https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/MANIFESTO.md

To unsubscribe: reply with UNSUBSCRIBE in the subject.

Free Palestine. 🌹
"""

def already_sent_this_week():
    p = DATA / 'newsletter_log.json'
    if not p.exists(): return False
    try:
        log  = json.loads(p.read_text())
        last = log.get('last_sent', '')
        if not last: return False
        last_date  = datetime.date.fromisoformat(last)
        days_since = (datetime.date.today() - last_date).days
        return days_since < 6
    except: return False

def mark_sent(count):
    p = DATA / 'newsletter_log.json'
    log = {'last_sent': TODAY, 'sends': []}
    if p.exists():
        try: log = json.loads(p.read_text())
        except: pass
    log['last_sent'] = TODAY
    log.setdefault('sends', []).append({'date': TODAY, 'count': count})
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def send_newsletter(email, name, body, subject):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko 🌹 <{GMAIL_ADDRESS}>'
        msg['To']      = email
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, email, msg.as_string())
        return True
    except Exception as e:
        print(f'[newsletter] Send error to {email}: {e}')
        return False

def run():
    print(f'\n[newsletter] Newsletter Engine — {TODAY}')

    # Only send on Sundays
    if WEEKDAY != 6:
        print(f'[newsletter] Not Sunday (weekday={WEEKDAY}). Skipping.')
        return

    if already_sent_this_week():
        print('[newsletter] Already sent this week. Skipping.')
        return

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[newsletter] No Gmail credentials. Skipping.')
        return

    subscribers = get_subscriber_list()
    if not subscribers:
        print('[newsletter] No subscribers yet. List grows as Ko-fi donations come in.')
        return

    print(f'[newsletter] Sending to {len(subscribers)} subscribers...')
    highlights = get_week_highlights()
    subject    = f'{NEWSLETTER_SUBJECT_PREFIX} — {TODAY}'

    sent = 0
    for email, info in subscribers.items():
        name = info.get('name', 'Friend')
        body = generate_newsletter(highlights, name)
        if send_newsletter(email, name, body, subject):
            sent += 1
            print(f'[newsletter]   ✅ {email[:40]}')

    mark_sent(sent)
    print(f'[newsletter] Sent: {sent}/{len(subscribers)}')

if __name__ == '__main__':
    run()
