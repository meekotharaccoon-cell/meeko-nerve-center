#!/usr/bin/env python3
"""
Grant Intelligence Engine — v2 (FIXED)
========================================
BIG FIX: Previous version only sent email on Tuesdays (WEEKDAY == 1).
That's why you never got grant updates — if it ran on any other day, silence.

New behavior:
  - Sends email EVERY TIME a new draft is generated (not day-gated)
  - If no new draft: sends a weekly summary on Sundays only (not silently nothing)
  - Tracks application status: researching → drafted → submitted → responded
  - Shows which grants are coming up in the next 30 days
  - Never re-drafts something already drafted (prevents duplicate emails)

Grants tracked: Mozilla, Knight, NLnet, Prototype Fund (DE), Open Society,
Digital Defender Partnership — all fit score 7-9/10 for this project.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()  # 0=Mon, 6=Sun

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
        al   = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        kofi = load(DATA / 'kofi_events.json')
        ev   = kofi if isinstance(kofi, list) else kofi.get('events', [])
        stats['pcrf'] = round(sum(float(e.get('amount', 0)) for e in ev
                                  if e.get('type') in ('donation', 'Donation')) * 0.70, 2)
    except: pass
    return stats

def generate_cover_letter(grant, stats):
    if not HF_TOKEN: return None
    prompt = f"""Write a compelling grant cover letter.

Grant: {grant['program']} from {grant['funder']}
Amount: {grant['amount']}
Key language: {grant['key_language']}
Fit reasons: {grant['fit_reasons']}

Project: Meeko Nerve Center / SolarPunk
  - Self-evolving AI for congressional accountability + Palestinian solidarity
  - Built {stats.get('self_built', 0)} of its own engines autonomously
  - {stats.get('engines', 40)}+ active engines, $0/month infrastructure
  - {stats.get('art', 0)} Gaza Rose art pieces generated
  - ${stats.get('pcrf', 0):.2f} donated to PCRF for Palestinian children
  - AGPL-3.0 licensed, fully open source, forkable
  - GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Write 350-450 words. Lead with impact. Use their key language naturally.
Connect to their mission explicitly. Specific ask. NOT a template.
Respond with letter body only."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 700,
            'messages': [
                {'role': 'system', 'content': 'You write compelling specific grant applications. No boilerplate.'},
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

def send_grant_email(grant, letter, db):
    """Send email immediately when a new draft is ready — not day-gated.""""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[grants] No email credentials — skipping send')
        return

    # Upcoming deadlines
    month = datetime.date.today().month
    upcoming = [
        g for g in db
        if g.get('typical_deadline_month') and
        0 < (g['typical_deadline_month'] - month) % 12 <= 2
    ]

    # All drafts status
    drafted   = [g for g in db if g.get('status') == 'drafted']
    submitted = [g for g in db if g.get('status') == 'submitted']
    remaining = [g for g in db if g.get('status') == 'researching']

    lines = [
        f'🌸 GRANT INTELLIGENCE — New Draft Ready [{TODAY}]',
        '=' * 55,
        '',
        f'NEW DRAFT: {grant["funder"]} — {grant["program"]}',
        f'Amount: {grant["amount"]}',
        f'Submit at: {grant["url"]}',
        f'Fit score: {grant["fit_score"]}/10',
        '',
        '── COVER LETTER ──────────────────────────────────────',
        letter,
        '── END COVER LETTER ──────────────────────────────────',
        '',
        'ACTION REQUIRED: Copy the letter above and submit at the URL.',
        '',
    ]

    if upcoming:
        lines.append('⏰ DEADLINES IN NEXT 2 MONTHS:')
        for g in upcoming:
            lines.append(f'  {g["funder"]} — {g["program"]} | {g["amount"]}')
            lines.append(f'  → {g["url"]}')
        lines.append('')

    lines += [
        f'PIPELINE STATUS:',
        f'  📝 Drafted (not yet submitted): {len(drafted)}',
        f'  📬 Submitted: {len(submitted)}',
        f'  🔍 Still researching: {len(remaining)}',
        '',
        'TOP UNSUBMITTED BY FIT:',
    ]
    for g in sorted(remaining, key=lambda x: -x.get('fit_score', 0))[:3]:
        lines.append(f'  {g["fit_score"]}/10 — {g["funder"]}: {g["amount"]}')
        lines.append(f'  → {g["url"]}')

    lines += ['', 'Free Palestine. 🌹', '— SolarPunk Nerve Center']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'💼 NEW grant draft: {grant["funder"]} ({grant["amount"]}) — ACTION NEEDED'
        msg['From']    = f'SolarPunk <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[grants] ✅ Email sent: {grant["funder"]}')
    except Exception as e:
        print(f'[grants] Email error: {e}')

def send_weekly_no_draft_summary(db):
    """On Sundays when no new draft: send pipeline overview so you don't go blind."""
    if WEEKDAY != 6: return  # Only Sundays
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return

    drafted   = [g for g in db if g.get('status') == 'drafted']
    submitted = [g for g in db if g.get('status') == 'submitted']
    remaining = [g for g in db if g.get('status') == 'researching']

    lines = [
        f'🌸 GRANT PIPELINE WEEKLY SUMMARY [{TODAY}]',
        '=' * 50,
        '',
        f'📝 Drafted (awaiting your submission): {len(drafted)}',
        f'📬 Submitted: {len(submitted)}',
        f'🔍 In research queue: {len(remaining)}',
        '',
    ]

    if drafted:
        lines.append('DRAFTED — WAITING FOR YOU TO SUBMIT:')
        for g in drafted:
            lines.append(f'  → {g["funder"]} | {g["amount"]} | {g["url"]}')
            lines.append(f'     Draft date: {g.get("draft_date", "?")} | See content/grants/')
        lines.append('')

    lines.append('TOP TARGETS TO DRAFT NEXT:')
    for g in sorted(remaining, key=lambda x: -x.get('fit_score', 0))[:3]:
        lines.append(f'  {g["fit_score"]}/10 — {g["funder"]}: {g["program"]} ({g["amount"]})')
        lines.append(f'  → {g["url"]}')

    lines += ['', '— SolarPunk Nerve Center']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📋 Weekly grant pipeline: {len(drafted)} drafted, {len(submitted)} submitted'
        msg['From']    = f'SolarPunk <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[grants] Weekly summary sent')
    except Exception as e:
        print(f'[grants] Weekly summary error: {e}')

def run():
    print(f'\n[grants] 💼 Grant Intelligence Engine v2 — {TODAY}')
    print('[grants] FIXED: Emails now sent when drafts are ready, not Tuesday-only.')

    db_path = DATA / 'grant_database.json'
    db = load(db_path, list(GRANT_DATABASE))

    # Merge any new grants from default db that aren't in loaded db
    existing_ids = {g.get('id') for g in db}
    for g in GRANT_DATABASE:
        if g['id'] not in existing_ids:
            db.append(dict(g))

    stats = get_system_stats()
    print(f'[grants] System: {stats.get("engines","?")} engines, ${stats.get("pcrf",0):.2f} PCRF')

    # Find one unsubmitted grant to draft
    unsubmitted = [g for g in db if g.get('status') in ('researching', None)]
    unsubmitted.sort(key=lambda g: -g.get('fit_score', 0))

    drafted_this_run = None
    for grant in unsubmitted[:1]:
        print(f'[grants] Drafting: {grant["funder"]} — {grant["program"]}')
        letter = generate_cover_letter(grant, stats)
        if letter:
            # Save draft file
            grants_dir = ROOT / 'content' / 'grants'
            grants_dir.mkdir(parents=True, exist_ok=True)
            draft_path = grants_dir / f'{grant["id"]}_{TODAY}.txt'
            try:
                draft_path.write_text(
                    f'Grant: {grant["funder"]} — {grant["program"]}\n'
                    f'URL: {grant["url"]}\n'
                    f'Amount: {grant["amount"]}\n'
                    f'Fit: {grant["fit_score"]}/10\n\n'
                    f'{letter}'
                )
                print(f'[grants] ✅ Saved: {draft_path.name}')
            except Exception as e:
                print(f'[grants] Save error: {e}')

            # Update status in db
            for g in db:
                if g['id'] == grant['id']:
                    g['status'] = 'drafted'
                    g['draft_date'] = TODAY
            drafted_this_run = (grant, letter)
            break
        else:
            print('[grants] LLM unavailable — skipping draft')

    # Save updated db
    try: db_path.write_text(json.dumps(db, indent=2))
    except: pass

    # Send email immediately if new draft ready (NOT day-gated)
    if drafted_this_run:
        send_grant_email(drafted_this_run[0], drafted_this_run[1], db)
    else:
        print('[grants] No new draft this cycle')
        send_weekly_no_draft_summary(db)  # Only on Sundays

    drafted_count = sum(1 for g in db if g.get('status') == 'drafted')
    print(f'[grants] Done. Drafted: {drafted_count} total in pipeline.')

if __name__ == '__main__':
    run()
