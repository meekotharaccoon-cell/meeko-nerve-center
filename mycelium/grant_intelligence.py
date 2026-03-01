#!/usr/bin/env python3
"""
Grant Intelligence Engine — v3 (Memory-Informed)
==================================================
v2 FIX: No longer Tuesday-only. Emails sent when drafts ready.
v3 NEW: Now reads long_term_memory + directives before every LLM call.

Memory context tells the grant engine:
  - Which grant TYPES have gotten responses before
  - What language the system has used that worked
  - What the human has prioritized recently (from Notion directives)
  - How many grants have been submitted total

Result: each cover letter is more targeted than the last.
The system stops sounding like a template and starts sounding like itself.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

GRANT_DATABASE = [
    {
        'id': 'mozilla_tech_fund', 'funder': 'Mozilla Foundation',
        'program': 'Mozilla Technology Fund',
        'url': 'https://foundation.mozilla.org/en/what-we-fund/awards/mozilla-technology-fund/',
        'amount': '$50,000 - $150,000', 'cycle': 'annual', 'typical_deadline_month': 3,
        'fit_score': 9, 'fit_reasons': ['open source', 'accountability', 'trustworthy AI', 'civic tech'],
        'key_language': ['trustworthy AI', 'internet health', 'open source', 'accountability'], 'status': 'researching',
    },
    {
        'id': 'knight_prototype', 'funder': 'Knight Foundation', 'program': 'Prototype Fund',
        'url': 'https://knightfoundation.org/prototype/',
        'amount': '$35,000', 'cycle': 'rolling', 'typical_deadline_month': None,
        'fit_score': 8, 'fit_reasons': ['journalism', 'civic tech', 'democracy', 'accountability'],
        'key_language': ['informed communities', 'democracy', 'media', 'civic engagement'], 'status': 'researching',
    },
    {
        'id': 'nlnet_ngi', 'funder': 'NLnet Foundation', 'program': 'NGI Zero Core',
        'url': 'https://nlnet.nl/core/',
        'amount': 'up to EUR 50,000', 'cycle': 'quarterly', 'typical_deadline_month': None,
        'fit_score': 9, 'fit_reasons': ['open source', 'internet infrastructure', 'privacy', 'human rights'],
        'key_language': ['open internet', 'privacy', 'security', 'open standards'], 'status': 'researching',
    },
    {
        'id': 'prototype_fund_de', 'funder': 'Prototype Fund (Germany)', 'program': 'Prototype Fund Round',
        'url': 'https://prototypefund.de/en/',
        'amount': 'EUR 47,500', 'cycle': 'biannual', 'typical_deadline_month': 4,
        'fit_score': 8, 'fit_reasons': ['open source', 'civic tech', 'social good', 'software infrastructure'],
        'key_language': ['common good', 'open source', 'civic society', 'digital infrastructure'], 'status': 'researching',
    },
    {
        'id': 'open_society_eti', 'funder': 'Open Society Foundations', 'program': 'Emerging Technology Initiative',
        'url': 'https://www.opensocietyfoundations.org/grants',
        'amount': '$25,000 - $100,000', 'cycle': 'rolling', 'typical_deadline_month': None,
        'fit_score': 9, 'fit_reasons': ['human rights', 'accountability', 'democracy', 'Palestine'],
        'key_language': ['human rights', 'accountability', 'transparency', 'civil society'], 'status': 'researching',
    },
    {
        'id': 'digital_defender', 'funder': 'Digital Defender Partnership', 'program': 'Digital Security Grant',
        'url': 'https://www.digitaldefenders.org/',
        'amount': 'up to $50,000', 'cycle': 'rolling', 'typical_deadline_month': None,
        'fit_score': 7, 'fit_reasons': ['digital rights', 'human rights defenders', 'open source tools'],
        'key_language': ['digital security', 'human rights defenders', 'civil society'], 'status': 'researching',
    },
]


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


# ── Memory & Directives ────────────────────────────────────────────────────────
def load_memory_context():
    """
    Load long-term memory context for grant engine.
    This is what makes the LLM smarter each cycle.
    """
    memory = load(DATA / 'long_term_memory.json')
    if not memory:
        return ''
    ctx = memory.get('contexts', {})
    grant_ctx = ctx.get('grant_engine', '') or ctx.get('general', '')
    return grant_ctx

def load_directives_context():
    """
    Load today's human directives.
    If human said "priority: grants", the LLM knows that.
    """
    d = load(DATA / 'directives.json')
    if not d or d.get('date') != TODAY:
        return ''
    parts = []
    if d.get('human_message'): parts.append(f"Human says today: {d['human_message']}")
    if 'grants' in d.get('priority', []) or 'grants' in d.get('amplify', []):
        parts.append('Human has explicitly prioritized grants today — make this application sharp.')
    return ' | '.join(parts)

def get_grant_history():
    """
    What do we know about past grant activity? Tell the LLM.
    """
    db = load(DATA / 'grant_database.json', list(GRANT_DATABASE))
    submitted = [g for g in db if g.get('status') == 'submitted']
    responded = [g for g in db if g.get('status') in ('responded', 'funded')]
    pattern_notes = []
    if submitted:
        pattern_notes.append(f'{len(submitted)} grants previously submitted')
    if responded:
        pattern_notes.append(f'{len(responded)} received responses from: {[g["funder"] for g in responded]}')
    memory = load(DATA / 'long_term_memory.json')
    if memory:
        gp = memory.get('grant_patterns', {})
        if gp.get('total_submitted'):
            pattern_notes.append(f'Total submitted (all time): {gp["total_submitted"]}')
    return ' | '.join(pattern_notes) if pattern_notes else 'First grant application cycle'


# ── System Stats ──────────────────────────────────────────────────────────────
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


# ── LLM: Generate cover letter with memory context ────────────────────────────
def generate_cover_letter(grant, stats):
    if not HF_TOKEN: return None

    # Load memory context — this is the v3 upgrade
    memory_ctx      = load_memory_context()
    directives_ctx  = load_directives_context()
    history_ctx     = get_grant_history()

    # Build context prefix — prepended to system prompt
    context_prefix = ''
    if memory_ctx:
        context_prefix += f'Long-term memory context: {memory_ctx}\n'
    if directives_ctx:
        context_prefix += f'Human directive: {directives_ctx}\n'
    if history_ctx:
        context_prefix += f'Grant history: {history_ctx}\n'
    if context_prefix:
        context_prefix += '\n'
        print(f'[grants] Injecting memory context ({len(context_prefix)} chars)')

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
                {'role': 'system', 'content': context_prefix + 'You write compelling specific grant applications. No boilerplate. Be specific to this funder.'},
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
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[grants] No email credentials — skipping send')
        return
    month    = datetime.date.today().month
    upcoming = [g for g in db if g.get('typical_deadline_month') and
                0 < (g['typical_deadline_month'] - month) % 12 <= 2]
    drafted   = [g for g in db if g.get('status') == 'drafted']
    submitted = [g for g in db if g.get('status') == 'submitted']
    remaining = [g for g in db if g.get('status') == 'researching']

    # Include memory context in email so human can see what the system knew
    memory_ctx = load_memory_context()
    directives_ctx = load_directives_context()

    lines = [
        f'🌸 GRANT INTELLIGENCE v3 (Memory-Informed) — {TODAY}',
        '=' * 55, '',
        f'NEW DRAFT: {grant["funder"]} — {grant["program"]}',
        f'Amount: {grant["amount"]}',
        f'Submit at: {grant["url"]}',
        f'Fit score: {grant["fit_score"]}/10',
    ]
    if memory_ctx:
        lines += ['', f'[Memory context used]: {memory_ctx[:200]}']
    if directives_ctx:
        lines += [f'[Directive context used]: {directives_ctx[:200]}']
    lines += [
        '', '── COVER LETTER ──────────────────────────────────────',
        letter,
        '── END COVER LETTER ──────────────────────────────────',
        '', 'ACTION REQUIRED: Copy the letter above and submit at the URL.', '',
    ]
    if upcoming:
        lines.append('⏰ DEADLINES IN NEXT 2 MONTHS:')
        for g in upcoming:
            lines += [f'  {g["funder"]} — {g["program"]} | {g["amount"]}', f'  → {g["url"]}']
        lines.append('')
    lines += [
        f'PIPELINE: Drafted: {len(drafted)} | Submitted: {len(submitted)} | Research queue: {len(remaining)}',
        '', 'TOP UNSUBMITTED:',
    ]
    for g in sorted(remaining, key=lambda x: -x.get('fit_score', 0))[:3]:
        lines += [f'  {g["fit_score"]}/10 — {g["funder"]}: {g["amount"]}', f'  → {g["url"]}']
    lines += ['', 'Free Palestine. 🌹', '— SolarPunk Nerve Center']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'💼 NEW grant draft (memory-informed): {grant["funder"]} ({grant["amount"]})'
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
    if WEEKDAY != 6: return
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    drafted   = [g for g in db if g.get('status') == 'drafted']
    submitted = [g for g in db if g.get('status') == 'submitted']
    remaining = [g for g in db if g.get('status') == 'researching']
    lines = [
        f'🌸 GRANT PIPELINE WEEKLY [{TODAY}]', '=' * 50, '',
        f'Drafted (submit these): {len(drafted)}',
        f'Submitted: {len(submitted)}',
        f'Research queue: {len(remaining)}', '',
    ]
    if drafted:
        lines.append('DRAFTED — WAITING FOR SUBMISSION:')
        for g in drafted:
            lines += [f'  → {g["funder"]} | {g["amount"]} | {g["url"]}',
                      f'     Draft date: {g.get("draft_date", "?")} | See content/grants/']
        lines.append('')
    lines.append('TOP TARGETS TO DRAFT NEXT:')
    for g in sorted(remaining, key=lambda x: -x.get('fit_score', 0))[:3]:
        lines += [f'  {g["fit_score"]}/10 — {g["funder"]}: {g["program"]} ({g["amount"]})',
                  f'  → {g["url"]}']
    lines += ['', '— SolarPunk Nerve Center']
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📋 Weekly grants: {len(drafted)} drafted, {len(submitted)} submitted'
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
    print(f'\n[grants] 💼 Grant Intelligence Engine v3 (Memory-Informed) — {TODAY}')

    db_path = DATA / 'grant_database.json'
    db = load(db_path, list(GRANT_DATABASE))
    existing_ids = {g.get('id') for g in db}
    for g in GRANT_DATABASE:
        if g['id'] not in existing_ids:
            db.append(dict(g))

    stats = get_system_stats()
    print(f'[grants] System: {stats.get("engines","?")} engines, ${stats.get("pcrf",0):.2f} PCRF')

    # Check for directives — human may have said "priority: grants"
    directives = load(DATA / 'directives.json')
    if directives and 'grants' in directives.get('priority', []):
        print('[grants] 🎯 Human directive: grants are priority today — drafting up to 2')
        max_drafts = 2
    else:
        max_drafts = 1

    unsubmitted = [g for g in db if g.get('status') in ('researching', None)]
    unsubmitted.sort(key=lambda g: -g.get('fit_score', 0))

    drafted_this_run = []
    for grant in unsubmitted[:max_drafts]:
        print(f'[grants] Drafting: {grant["funder"]} — {grant["program"]}')
        letter = generate_cover_letter(grant, stats)
        if letter:
            grants_dir = ROOT / 'content' / 'grants'
            grants_dir.mkdir(parents=True, exist_ok=True)
            draft_path = grants_dir / f'{grant["id"]}_{TODAY}.txt'
            try:
                draft_path.write_text(
                    f'Grant: {grant["funder"]} — {grant["program"]}\n'
                    f'URL: {grant["url"]}\nAmount: {grant["amount"]}\n'
                    f'Fit: {grant["fit_score"]}/10\n\n{letter}'
                )
                print(f'[grants] ✅ Saved: {draft_path.name}')
            except Exception as e:
                print(f'[grants] Save error: {e}')
            for g in db:
                if g['id'] == grant['id']:
                    g['status'] = 'drafted'
                    g['draft_date'] = TODAY
            drafted_this_run.append((grant, letter))
        else:
            print('[grants] LLM unavailable — skipping')
            break

    try: db_path.write_text(json.dumps(db, indent=2))
    except: pass

    if drafted_this_run:
        for grant, letter in drafted_this_run:
            send_grant_email(grant, letter, db)
    else:
        print('[grants] No new draft this cycle')
        send_weekly_no_draft_summary(db)

    drafted_count = sum(1 for g in db if g.get('status') == 'drafted')
    print(f'[grants] Done. Total drafted: {drafted_count}')


if __name__ == '__main__':
    run()
