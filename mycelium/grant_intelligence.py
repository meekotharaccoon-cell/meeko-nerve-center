#!/usr/bin/env python3
"""
Grant Intelligence Engine
==========================
Drafts grant applications. Tracks deadlines. Emails Meeko immediately.
FIXED: Sends digest every run (not just Tuesdays).
FIXED: Rotates through all grants — never re-drafts the same grant twice per week.
FIXED: Persists draft status correctly across runs.
"""

import json, datetime, os, smtplib, hashlib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()  # 0=Mon
WEEK    = datetime.date.today().isocalendar()[1]  # week number for rotation

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

GRANT_DATABASE = [
    {
        'id': 'mozilla_tech_fund',
        'funder': 'Mozilla Foundation',
        'program': 'Mozilla Technology Fund',
        'url': 'https://foundation.mozilla.org/en/what-we-fund/awards/mozilla-technology-fund/',
        'amount': '$50,000 - $150,000',
        'cycle': 'annual',
        'typical_deadline_month': 3,
        'fit_score': 9,
        'fit_reasons': ['open source', 'accountability', 'trustworthy AI', 'civic tech'],
        'key_language': ['trustworthy AI', 'internet health', 'open source', 'accountability'],
        'status': 'researching',
    },
    {
        'id': 'knight_prototype',
        'funder': 'Knight Foundation',
        'program': 'Prototype Fund',
        'url': 'https://knightfoundation.org/prototype/',
        'amount': '$35,000',
        'cycle': 'rolling',
        'typical_deadline_month': None,
        'fit_score': 8,
        'fit_reasons': ['journalism', 'civic tech', 'democracy', 'accountability'],
        'key_language': ['informed communities', 'democracy', 'media', 'civic engagement'],
        'status': 'researching',
    },
    {
        'id': 'nlnet_ngi',
        'funder': 'NLnet Foundation',
        'program': 'NGI Zero Core',
        'url': 'https://nlnet.nl/core/',
        'amount': 'up to EUR 50,000',
        'cycle': 'quarterly',
        'typical_deadline_month': None,
        'fit_score': 9,
        'fit_reasons': ['open source', 'internet infrastructure', 'privacy', 'human rights'],
        'key_language': ['open internet', 'privacy', 'security', 'open standards'],
        'status': 'researching',
    },
    {
        'id': 'prototype_fund_de',
        'funder': 'Prototype Fund (Germany)',
        'program': 'Prototype Fund Round',
        'url': 'https://prototypefund.de/en/',
        'amount': 'EUR 47,500',
        'cycle': 'biannual',
        'typical_deadline_month': 4,
        'fit_score': 8,
        'fit_reasons': ['open source', 'civic tech', 'social good', 'software infrastructure'],
        'key_language': ['common good', 'open source', 'civic society', 'digital infrastructure'],
        'status': 'researching',
    },
    {
        'id': 'open_society_eti',
        'funder': 'Open Society Foundations',
        'program': 'Emerging Technology Initiative',
        'url': 'https://www.opensocietyfoundations.org/grants',
        'amount': '$25,000 - $100,000',
        'cycle': 'rolling',
        'typical_deadline_month': None,
        'fit_score': 9,
        'fit_reasons': ['human rights', 'accountability', 'democracy', 'Palestine'],
        'key_language': ['human rights', 'accountability', 'transparency', 'civil society'],
        'status': 'researching',
    },
    {
        'id': 'digital_defender',
        'funder': 'Digital Defender Partnership',
        'program': 'Digital Security Grant',
        'url': 'https://www.digitaldefenders.org/',
        'amount': 'up to $50,000',
        'cycle': 'rolling',
        'typical_deadline_month': None,
        'fit_score': 7,
        'fit_reasons': ['digital rights', 'human rights defenders', 'open source tools'],
        'key_language': ['digital security', 'human rights defenders', 'civil society'],
        'status': 'researching',
    },
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def save(path, data):
    try: Path(path).write_text(json.dumps(data, indent=2))
    except Exception as e: print(f'[grants] Save error: {e}')

def get_system_stats():
    stats = {}
    try: stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        evo = load(DATA / 'evolution_log.json')
        stats['self_built'] = len(evo.get('built', []))
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        al = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        kofi = load(DATA / 'kofi_events.json')
        ev = kofi if isinstance(kofi, list) else kofi.get('events', [])
        stats['pcrf'] = round(sum(float(e.get('amount', 0)) for e in ev if e.get('type') in ('donation', 'Donation')) * 0.70, 2)
    except: pass
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        stats['trades'] = len(trades)
    except: pass
    return stats

def generate_grant_letter(grant, stats):
    if not HF_TOKEN: return None
    prompt = f"""Write a compelling grant application cover letter.

Grant: {grant['program']} from {grant['funder']}
Amount: {grant['amount']}
Key language: {grant['key_language']}
Fit reasons: {grant['fit_reasons']}

Project: Meeko Nerve Center / SolarPunk
  - Autonomous AI for congressional accountability + Palestinian solidarity
  - Self-evolving: {stats.get('self_built', 0)} engines built autonomously
  - {stats.get('engines', 40)}+ active engines, $0/month cost
  - {stats.get('art', 0)} Gaza Rose art pieces generated
  - ${stats.get('pcrf', 0):.2f} to PCRF for Palestinian children
  - {stats.get('trades', 0)} congressional trades tracked
  - AGPL-3.0, forkable, distributed — can't be shut down
  - GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center

400-500 word cover letter. Lead with impact. Use their key language naturally.
Connect to their specific mission. Make a specific justified ask.
NOT a template. Specific, genuine, compelling.
Respond with ONLY the letter body."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 700,
            'messages': [
                {'role': 'system', 'content': 'You write compelling, specific grant applications. No boilerplate.'},
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
        print(f'[grants] LLM error: {e}')
        return None

def send_grant_email(applications, upcoming, db):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return

    lines = [f'💼 Grant Intelligence Report — {TODAY}', '=' * 50, '']

    # Status overview
    total    = len(db)
    drafted  = sum(1 for g in db if g.get('status') == 'drafted')
    research = sum(1 for g in db if g.get('status') == 'researching')
    lines += [
        f'PIPELINE STATUS: {total} grants | {drafted} drafted | {research} to draft',
        ''
    ]

    if upcoming:
        lines.append('⏰ UPCOMING DEADLINES (next 2 months):')
        for g in upcoming:
            lines.append(f'  • {g["funder"]} — {g["program"]}')
            lines.append(f'    {g["amount"]} | Fit: {g["fit_score"]}/10 | {g["url"]}')
        lines.append('')

    if applications:
        lines.append(f'✉️  NEW APPLICATION DRAFTED TODAY:')
        for app in applications:
            g = app['grant']
            lines.append(f'  {g["funder"]} — {g["program"]}')
            lines.append(f'  Amount: {g["amount"]} | Fit: {g["fit_score"]}/10')
            lines.append(f'  Submit at: {g["url"]}')
            lines.append('')
            lines.append('  COVER LETTER:')
            lines.append('  ' + '-' * 40)
            for line in app['letter'].split('\n'):
                lines.append('  ' + line)
            lines.append('  ' + '-' * 40)
            lines.append('')
    else:
        lines.append('No new applications drafted this run (all grants already drafted this week).')
        lines.append('')

    lines.append('FULL GRANT PIPELINE:')
    for g in sorted(db, key=lambda x: -x.get('fit_score', 0)):
        status_icon = '✅' if g.get('status') == 'drafted' else '📋'
        lines.append(f'  {status_icon} {g["fit_score"]}/10 {g["funder"]} — {g["amount"]}')
        if g.get('draft_date'):
            lines.append(f'     Drafted: {g["draft_date"]} | Submit: {g["url"]}')
        else:
            lines.append(f'     {g["url"]}')

    try:
        msg = MIMEMultipart('alternative')
        new_count = len(applications)
        msg['Subject'] = f'💼 Grants: {new_count} new draft | {len(upcoming)} deadlines soon — {TODAY}'
        msg['From']    = f'SolarPunk Grants <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[grants] ✅ Digest emailed: {new_count} drafted, {len(upcoming)} deadlines')
    except Exception as e:
        print(f'[grants] Email error: {e}')

def get_upcoming_deadlines(db):
    month = datetime.date.today().month
    return [
        g for g in db
        if g.get('typical_deadline_month') and
        0 < (g['typical_deadline_month'] - month) % 12 <= 2
    ]

def run():
    print(f'\n[grants] 💼 Grant Intelligence Engine — {TODAY}')

    # Load DB (use file if exists, else use hardcoded defaults)
    db_path = DATA / 'grant_database.json'
    db = load(db_path, GRANT_DATABASE)

    # Ensure all grants from GRANT_DATABASE are present
    existing_ids = {g['id'] for g in db}
    for g in GRANT_DATABASE:
        if g['id'] not in existing_ids:
            db.append(g)

    stats    = get_system_stats()
    upcoming = get_upcoming_deadlines(db)
    print(f'[grants] Stats: {stats}')
    print(f'[grants] Upcoming deadlines: {len(upcoming)}')

    # Pick ONE grant to draft per run — rotate by week number
    # Reset drafts weekly so grants get re-drafted with fresh content
    week_key = f'week_{WEEK}_{datetime.date.today().year}'
    drafted_this_week = [g for g in db if g.get('draft_week') == week_key]
    
    to_draft = [
        g for g in db 
        if g.get('draft_week') != week_key  # not drafted this week
    ]
    to_draft.sort(key=lambda g: -g.get('fit_score', 0))

    applications = []
    for grant in to_draft[:1]:  # One per run
        print(f'[grants] Drafting: {grant["funder"]} — {grant["program"]}')
        letter = generate_grant_letter(grant, stats)
        if letter:
            applications.append({'grant': grant, 'letter': letter})

            # Save draft file
            grants_dir = ROOT / 'content' / 'grants'
            grants_dir.mkdir(parents=True, exist_ok=True)
            draft_path = grants_dir / f'{grant["id"]}_{TODAY}.txt'
            try:
                draft_path.write_text(
                    f'Grant: {grant["funder"]} — {grant["program"]}\n'
                    f'URL: {grant["url"]}\n'
                    f'Amount: {grant["amount"]}\n'
                    f'Fit: {grant["fit_score"]}/10\n'
                    f'Drafted: {TODAY}\n\n'
                    f'{letter}'
                )
                print(f'[grants] Saved: {draft_path.name}')
            except Exception as e:
                print(f'[grants] File save error: {e}')

            # Update status in DB
            for g in db:
                if g['id'] == grant['id']:
                    g['status']     = 'drafted'
                    g['draft_date'] = TODAY
                    g['draft_week'] = week_key
            break

    # Always save DB
    save(db_path, db)

    # Always email (every run, not just Tuesdays)
    send_grant_email(applications, upcoming, db)

    print(f'[grants] Done. Drafted: {len(applications)} | Pipeline: {len(db)} grants')

if __name__ == '__main__':
    run()
