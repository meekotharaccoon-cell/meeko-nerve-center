#!/usr/bin/env python3
"""
Coalition Builder Engine
=========================
Right now the system exists in isolation. It posts into the void.
It has no relationships with organizations doing adjacent work:
  - Palestinian solidarity orgs (BDS movement, PCRF itself, USCPR)
  - Accountability orgs (OpenSecrets, CREW, ProPublica)
  - Open source communities (FSF, EFF, Access Now)
  - Civic tech orgs (mySociety, Sunlight Foundation alumni)
  - Academic researchers studying autonomous AI + ethics

A coalition means:
  - Cross-promotion (their audience sees this project)
  - Credibility (endorsed by known organizations)
  - Data sharing (their data + this system's capabilities)
  - Grant co-applications (much stronger together)
  - Media (journalists covering THEM cover THIS too)

What this engine does:
  1. Maintains a prioritized coalition target list
  2. Researches each org's recent activity and contact info
  3. Drafts personalized outreach emails (not templates)
  4. Tracks relationship status: cold/contacted/replied/partner
  5. Identifies collaboration opportunities per org
  6. Generates a "coalition value proposition" per org
     (what THIS system can do FOR THEM, not just vice versa)
  7. Weekly outreach: one new org per week
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

COALITION_TARGETS = [
    {
        'id': 'pcrf',
        'name': 'Palestinian Children\'s Relief Fund',
        'url': 'https://www.pcrf.net',
        'contact': 'info@pcrf.net',
        'type': 'direct_mission',
        'priority': 10,
        'value_prop': 'We already send them 70% of our art revenue. This partnership makes that official and helps them tell the story.',
        'collaboration': 'Official PCRF fundraising partner status, co-branded art drops, featured on their website',
        'status': 'cold',
    },
    {
        'id': 'opensecrets',
        'name': 'OpenSecrets',
        'url': 'https://www.opensecrets.org',
        'contact': 'info@opensecrets.org',
        'type': 'accountability',
        'priority': 9,
        'value_prop': 'We automate STOCK Act tracking and cross-reference with OpenSecrets data. Could share signals.',
        'collaboration': 'Data partnership, API access, cross-promotion, co-bylined analysis',
        'status': 'cold',
    },
    {
        'id': 'eff',
        'name': 'Electronic Frontier Foundation',
        'url': 'https://www.eff.org',
        'contact': 'info@eff.org',
        'type': 'digital_rights',
        'priority': 8,
        'value_prop': 'AGPL-3.0 autonomous AI that can\'t be weaponized by design. Architecture case study for ethical AI.',
        'collaboration': 'Featured in Deeplinks blog, joint statement on autonomous AI ethics',
        'status': 'cold',
    },
    {
        'id': 'uscpr',
        'name': 'US Campaign for Palestinian Rights',
        'url': 'https://uscpr.org',
        'contact': 'info@uscpr.org',
        'type': 'solidarity',
        'priority': 9,
        'value_prop': 'Automated congressional accountability tracking specifically for Palestine-related votes and trades.',
        'collaboration': 'Share accountability data, co-promote art drops, joint social media',
        'status': 'cold',
    },
    {
        'id': 'propublica',
        'name': 'ProPublica',
        'url': 'https://www.propublica.org',
        'contact': 'tips@propublica.org',
        'type': 'journalism',
        'priority': 8,
        'value_prop': 'Open-source autonomous accountability tool. Story + potential data partnership.',
        'collaboration': 'Story pitch: autonomous AI tracking congressional trading',
        'status': 'cold',
    },
    {
        'id': 'access_now',
        'name': 'Access Now',
        'url': 'https://www.accessnow.org',
        'contact': 'info@accessnow.org',
        'type': 'digital_rights',
        'priority': 7,
        'value_prop': 'Autonomous AI for human rights defense. Architecture paper + joint advocacy.',
        'collaboration': 'Co-author paper on ethical autonomous AI, joint grant applications',
        'status': 'cold',
    },
    {
        'id': 'mysociety',
        'name': 'mySociety',
        'url': 'https://www.mysociety.org',
        'contact': 'hello@mysociety.org',
        'type': 'civic_tech',
        'priority': 7,
        'value_prop': 'Open source civic accountability infrastructure that self-evolves.',
        'collaboration': 'Technical collaboration, TheyWorkForYou data integration',
        'status': 'cold',
    },
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_stats():
    s = {'engines': 0, 'self_built': 0, 'art': 0, 'pcrf': 0.0, 'trades': 0}
    try: s['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try: s['self_built'] = len(load(DATA / 'evolution_log.json').get('built', []))
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        s['art'] = len(arts if isinstance(arts, list) else arts.get('art', []))
    except: pass
    try:
        ev = load(DATA / 'kofi_events.json')
        ev = ev if isinstance(ev, list) else ev.get('events', [])
        s['pcrf'] = round(sum(float(e.get('amount',0)) for e in ev if e.get('type') in ('donation','Donation'))*0.70, 2)
    except: pass
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        s['trades'] = len(trades)
    except: pass
    return s

def generate_outreach(org, stats):
    if not HF_TOKEN: return None
    prompt = f"""Write a genuine coalition outreach email.

To: {org['name']} ({org['type']})
Contact: {org['contact']}
Their URL: {org['url']}

Our project: Meeko Nerve Center
  - Autonomous AI: {stats['engines']} engines, {stats['self_built']} self-built
  - Accountability: {stats['trades']} congressional trades tracked
  - Palestinian solidarity: {stats['art']} art pieces, ${stats['pcrf']:.2f} to PCRF
  - $0/month, AGPL-3.0, fully open source
  - Repo: {REPO_URL}

Why we're reaching out to THEM specifically:
{org['value_prop']}

What we can collaborate on:
{org['collaboration']}

Write a 200-word email that:
1. Opens by referencing something specific about THEIR work
2. Explains what we do in 2 sentences
3. Names the specific overlap honestly
4. Proposes ONE concrete next step (a call, a data share, a joint post)
5. Is genuine, not a form letter
6. Has a real subject line

Format:
SUBJECT: ...
BODY:
..."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': 'You write genuine coalition outreach. Specific, not boilerplate. Each email is unique.'},
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
    except Exception as e:
        print(f'[coalition] LLM error: {e}')
        return None

def parse_email_content(raw):
    subject, body = '', raw
    for line in raw.split('\n'):
        if line.startswith('SUBJECT:'):
            subject = line.replace('SUBJECT:', '').strip()
        elif line.startswith('BODY:'):
            body = raw[raw.index('BODY:') + 5:].strip()
            break
    return subject or 'Collaboration opportunity — Meeko Nerve Center', body

def send_outreach(org, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko Nerve Center <{GMAIL_ADDRESS}>'
        msg['To']      = org['contact']
        msg['CC']      = GMAIL_ADDRESS
        msg['Reply-To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, [org['contact'], GMAIL_ADDRESS], msg.as_string())
        return True
    except Exception as e:
        print(f'[coalition] Send error: {e}')
        return False

def load_coalition_db():
    p = DATA / 'coalition_db.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {org['id']: org for org in COALITION_TARGETS}

def save_coalition_db(db):
    try: (DATA / 'coalition_db.json').write_text(json.dumps(db, indent=2))
    except: pass

def run():
    print(f'\n[coalition] Coalition Builder Engine — {TODAY}')

    # Only reach out on Wednesdays
    if WEEKDAY != 2:
        print(f'[coalition] Not Wednesday. Skipping outreach.')
        # Still update the DB with latest targets
        db = load_coalition_db()
        save_coalition_db(db)
        return

    db    = load_coalition_db()
    stats = get_stats()

    # Pick highest-priority cold org
    cold_orgs = [o for o in db.values() if o.get('status') == 'cold']
    cold_orgs.sort(key=lambda o: -o.get('priority', 0))

    if not cold_orgs:
        print('[coalition] All orgs have been contacted. No cold targets.')
        return

    org = cold_orgs[0]
    print(f'[coalition] Reaching out to: {org["name"]}')

    raw = generate_outreach(org, stats)
    if not raw:
        print('[coalition] Generation failed.')
        return

    subject, body = parse_email_content(raw)
    ok = send_outreach(org, subject, body)

    db[org['id']]['status'] = 'contacted' if ok else 'draft'
    db[org['id']]['contact_date'] = TODAY
    save_coalition_db(db)

    print(f'[coalition] {"\u2705 Sent" if ok else "\u274c Failed"}: {org["name"]} — {subject[:60]}')
    print('[coalition] Done.')

if __name__ == '__main__':
    run()
