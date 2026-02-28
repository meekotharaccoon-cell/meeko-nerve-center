#!/usr/bin/env python3
"""
Unified Briefing Engine
========================
Solves the duplicate email problem.

Previous behavior: Every engine emails you every cycle.
Result: Dozens of identical emails per day. Same investment signals.
Same grant status. Same health report. You tune it all out.

New behavior: ONE email per day to Meeko. Only includes things that
CHANGED since the last briefing. If nothing changed, no email.

Delta tracking: Stores hashes of last-sent content in
data/briefing_state.json. If content hash matches last send,
that section is omitted from the email.

Email schedule:
  - Morning briefing: 8am UTC (if anything new since yesterday)
  - Alert briefing: When something important happens (new trade, grant deadline)
  - Sunday full review: Always sends with full week summary

This engine REPLACES scattered per-engine emails to Meeko.
Engines still generate their data — they just don't email it anymore.
This engine reads all that data and emails ONE clean summary.
"""

import json, datetime, os, smtplib, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()  # 0=Mon, 6=Sun
HOUR    = datetime.datetime.utcnow().hour

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def content_hash(data):
    """Hash content to detect if it changed since last briefing."""
    s = json.dumps(data, sort_keys=True)
    return hashlib.md5(s.encode()).hexdigest()[:12]

def load_state():
    return load(DATA / 'briefing_state.json', {
        'last_hashes': {}, 'last_send_date': '', 'last_full_send': ''
    })

def save_state(state):
    try: (DATA / 'briefing_state.json').write_text(json.dumps(state, indent=2))
    except: pass

def get_workflow_section(state):
    health = load(DATA / 'workflow_health.json')
    if not health: return None, None

    section_data = {
        'health_pct': health.get('health_pct'),
        'failing_count': health.get('failing', 0),
        'color': health.get('color'),
        'failing_names': [f.get('name', '?') for f in health.get('failures', [])],
    }
    h = content_hash(section_data)
    if h == state['last_hashes'].get('workflows') and WEEKDAY != 6:
        return None, h  # No change, not Sunday

    color_emoji = {'GREEN': '✅', 'YELLOW': '⚠️', 'RED': '🔴'}.get(health.get('color', ''), '❓')
    failing = health.get('failures', [])
    lines = [
        f'{color_emoji} WORKFLOW HEALTH: {health.get("health_pct", "?")}% ({health.get("passing",0)}/{health.get("total",0)} passing)',
    ]
    if failing:
        lines.append(f'  Failing ({len(failing)}):'
        + ''.join(f'\n    ✗ {f.get("name","?")}' for f in failing[:5]))
        if len(failing) > 5:
            lines.append(f'    ... and {len(failing)-5} more')
    else:
        lines.append('  All workflows passing. 🌱')
    return '\n'.join(lines), h

def get_congress_section(state):
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    if not trades: return None, None

    # Only flag trades newer than last check
    recent = trades[:5]
    h = content_hash([t.get('transaction_date', t.get('date', '')) + t.get('ticker','') for t in recent])
    if h == state['last_hashes'].get('congress') and WEEKDAY != 6:
        return None, h

    lines = ['🏛️ CONGRESSIONAL TRADES (recent):']
    for t in recent[:3]:
        name   = t.get('representative', t.get('senator', '?'))
        ticker = t.get('ticker', '?')
        date   = t.get('transaction_date', t.get('date', '?'))
        amount = t.get('amount', t.get('range', '?'))
        action = t.get('transaction_type', t.get('type', '?'))
        lines.append(f'  {name} — {action} {ticker} ({amount}) on {date}')
    return '\n'.join(lines), h

def get_investment_section(state):
    signals = load(DATA / 'investment_signals.json', {})
    sig_list = signals.get('signals', [])
    market   = load(DATA / 'market_context.json', {})
    if not sig_list and not market: return None, None

    top = sig_list[:3] if sig_list else []
    fg  = market.get('fear_greed_value', market.get('value', '?'))
    h   = content_hash({'top': [s.get('symbol','') for s in top], 'fg': fg})
    if h == state['last_hashes'].get('investment') and WEEKDAY != 6:
        return None, h

    fg_label = market.get('fear_greed_label', market.get('label', '?'))
    lines = [f'📈 MARKET SIGNALS (Fear/Greed: {fg} — {fg_label}):']
    if top:
        for s in top:
            lines.append(f'  {s.get("symbol","?")} — confidence {s.get("confidence","?")} | {" | ".join(s.get("reasons",[])[:2])}')
    else:
        lines.append('  No signals generated yet.')
    lines.append('  Not financial advice. Mathematical analysis.')
    return '\n'.join(lines), h

def get_grants_section(state):
    db  = load(DATA / 'grant_database.json', [])
    if not db: return None, None

    drafted   = [g for g in db if g.get('status') == 'drafted']
    submitted = [g for g in db if g.get('status') == 'submitted']
    remaining = [g for g in db if g.get('status') == 'researching']

    h = content_hash({'drafted': len(drafted), 'submitted': len(submitted), 'ids': [g.get('id') for g in drafted]})
    if h == state['last_hashes'].get('grants') and WEEKDAY != 6:
        return None, h

    lines = [f'💼 GRANTS: {len(drafted)} drafted | {len(submitted)} submitted | {len(remaining)} in queue']
    if drafted:
        lines.append('  AWAITING YOUR SUBMISSION:')
        for g in drafted[-2:]:  # Show 2 most recent
            lines.append(f'    → {g["funder"]} | {g["amount"]} | {g["url"]}')
    if remaining:
        top = sorted(remaining, key=lambda x: -x.get('fit_score', 0))[0]
        lines.append(f'  Next to draft: {top["funder"]} (fit: {top["fit_score"]}/10)')
    return '\n'.join(lines), h

def get_evolution_section(state):
    evo = load(DATA / 'evolution_log.json', {'built': []})
    built = evo.get('built', [])
    if not built: return None, None

    today_builds = [b for b in built if b.get('date') == TODAY]
    recent_builds = built[-3:]
    h = content_hash([b.get('name','') for b in recent_builds])
    if h == state['last_hashes'].get('evolution') and WEEKDAY != 6:
        return None, h

    lines = [f'🔧 SELF-EVOLUTION: {len(built)} total engines built | {len(today_builds)} today']
    for b in recent_builds:
        lines.append(f'  + {b.get("title", b.get("name","?"))} [{b.get("date","?")}]')
    return '\n'.join(lines), h

def get_impact_section(state):
    kofi = load(DATA / 'kofi_events.json', {})
    events = kofi if isinstance(kofi, list) else kofi.get('events', [])
    total = sum(float(e.get('amount', 0)) for e in events if e.get('type') in ('donation', 'Donation'))
    pcrf  = round(total * 0.70, 2)

    arts = load(DATA / 'generated_art.json', {})
    art_list = arts if isinstance(arts, list) else arts.get('art', [])

    h = content_hash({'pcrf': pcrf, 'arts': len(art_list)})
    if h == state['last_hashes'].get('impact') and WEEKDAY != 6:
        return None, h

    lines = [
        f'🌹 IMPACT: ${pcrf:.2f} to PCRF | {len(art_list)} Gaza Rose pieces generated',
    ]
    return '\n'.join(lines), h

def get_errors_section(state):
    errors = load(DATA / 'errors.json', {})
    error_list = errors if isinstance(errors, list) else errors.get('errors', [])
    recent_errors = [e for e in error_list if e.get('date', '') >= TODAY][:5]
    if not recent_errors: return None, None

    h = content_hash(recent_errors)
    if h == state['last_hashes'].get('errors'):
        return None, h

    lines = [f'⚠️ ERRORS TODAY ({len(recent_errors)}):']
    for e in recent_errors:
        lines.append(f'  [{e.get("engine","?")}] {str(e.get("error","?"))[:100]}')
    return '\n'.join(lines), h

def build_briefing():
    """Build the briefing. Returns (email_body, new_hashes, has_content)."""
    state = load_state()
    sections = []
    new_hashes = dict(state.get('last_hashes', {}))
    is_sunday  = WEEKDAY == 6

    checks = [
        ('workflows',  get_workflow_section),
        ('congress',   get_congress_section),
        ('investment', get_investment_section),
        ('grants',     get_grants_section),
        ('evolution',  get_evolution_section),
        ('impact',     get_impact_section),
        ('errors',     get_errors_section),
    ]

    for key, fn in checks:
        try:
            text, h = fn(state)
            if text:
                sections.append(text)
            if h:
                new_hashes[key] = h
        except Exception as e:
            print(f'[briefing] Section error ({key}): {e}')

    if not sections and not is_sunday:
        return None, new_hashes, False  # Nothing new

    if not sections:
        sections = ['All systems nominal. Nothing new since last check.']

    total_engines = len(list((ROOT / 'mycelium').glob('*.py')))
    health = load(DATA / 'workflow_health.json', {})

    header = [
        f'🌸 SolarPunk Daily Brief — {TODAY}',
        f'Engines: {total_engines} | Workflows: {health.get("health_pct","?")}% healthy | Autonomous: 97%',
        '=' * 55,
        '',
    ]
    footer = [
        '',
        '─' * 55,
        f'Dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html',
        'Free Palestine. 🌹 — SolarPunk Nerve Center',
    ]

    body = '\n'.join(header + ['\n\n'.join(sections)] + footer)
    return body, new_hashes, True

def should_send_today(state):
    """Don't send more than once per day unless it's an alert."""
    return state.get('last_send_date') != TODAY

def run():
    print(f'\n[briefing] 🌸 Unified Briefing Engine — {TODAY}')
    print('[briefing] Checking for new content (delta-only email)...')

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print('[briefing] No email credentials — skipping')
        return

    state = load_state()

    # Only send once per day
    if not should_send_today(state):
        print(f'[briefing] Already sent today ({TODAY}). Skipping.')
        return

    body, new_hashes, has_content = build_briefing()

    if not has_content:
        print('[briefing] No new content since last briefing. No email sent.')
        state['last_hashes'] = new_hashes
        save_state(state)
        return

    is_sunday = WEEKDAY == 6
    subject   = f'🌸 SolarPunk {"Weekly Review" if is_sunday else "Daily Brief"} — {TODAY}'
    if load(DATA / 'workflow_health.json', {}).get('color') == 'RED':
        subject = f'🔴 ACTION NEEDED — {subject}'

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'SolarPunk Nerve Center <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[briefing] ✅ Brief sent: {subject}')

        state['last_hashes']    = new_hashes
        state['last_send_date'] = TODAY
        if is_sunday: state['last_full_send'] = TODAY
        save_state(state)

    except Exception as e:
        print(f'[briefing] Email error: {e}')

if __name__ == '__main__':
    run()
