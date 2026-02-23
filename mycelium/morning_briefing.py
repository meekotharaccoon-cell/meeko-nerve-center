#!/usr/bin/env python3
"""
MEEKO MORNING BRIEFING
Runs every morning as part of mycelium-morning.yml
Now wired into the orchestrator data bus:
  - Pulls ISS position + crew from bus
  - Pulls solar weather
  - Pulls revenue snapshot
  - Pulls grant scan results
  - Includes all system status from ORCHESTRATOR
"""
import os, json, smtplib
from datetime import datetime, timezone
from pathlib import Path
try:
    import requests
except ImportError:
    requests = None
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER  = os.environ.get('GMAIL_USER', 'mickowood86@gmail.com')
GMAIL_PASS  = os.environ.get('GMAIL_APP_PASSWORD', '')
OR_KEY      = os.environ.get('OPENROUTER_KEY', '')
GH_TOKEN    = os.environ.get('GITHUB_TOKEN', '')

REPO_ROOT   = Path(__file__).parent.parent
BUS_PATH    = REPO_ROOT / 'data' / 'orchestrator_bus.json'
REVENUE_PATH= REPO_ROOT / 'data' / 'revenue_snapshot.json'
GRANT_PATH  = REPO_ROOT / 'data' / 'grants'


# ─────────────────────────────────────────────────────
# DATA BUS READER
# ─────────────────────────────────────────────────────
def read_bus():
    try:
        if BUS_PATH.exists():
            return json.loads(BUS_PATH.read_text())
    except:
        pass
    return {}

def read_revenue():
    try:
        if REVENUE_PATH.exists():
            return json.loads(REVENUE_PATH.read_text())
    except:
        pass
    return {}


# ─────────────────────────────────────────────────────
# SPACE DATA (from bus OR live API)
# ─────────────────────────────────────────────────────
def get_space_data():
    bus = read_bus()
    # Try bus first (fast, already fetched by orchestrator)
    iss = bus.get('iss_position', {})
    crew = bus.get('iss_crew', [])
    solar = bus.get('solar_wind_kms', 0)

    # If bus is empty, fetch live
    if not iss and requests:
        try:
            d = requests.get('http://api.open-notify.org/iss-now.json', timeout=6).json()
            iss = d.get('iss_position', {})
        except:
            pass
        try:
            d = requests.get('http://api.open-notify.org/astros.json', timeout=6).json()
            crew = [p['name'] for p in d.get('people',[]) if p.get('craft')=='ISS']
        except:
            pass
        try:
            d = requests.get('https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json', timeout=6).json()
            if isinstance(d, list) and len(d) > 1:
                solar = float(d[-1][2] or 0)
        except:
            pass

    return iss, crew, solar


# ─────────────────────────────────────────────────────
# GALLERY STATS
# ─────────────────────────────────────────────────────
def get_gallery_stats():
    if not GH_TOKEN or not requests:
        return {'views': '?', 'uniques': '?'}
    try:
        r = requests.get(
            'https://api.github.com/repos/meekotharaccoon-cell/gaza-rose-gallery/traffic/views',
            headers={'Authorization': f'Bearer {GH_TOKEN}', 'User-Agent': 'mycelium'},
            timeout=10
        )
        d = r.json()
        return {'views': d.get('count', 0), 'uniques': d.get('uniques', 0)}
    except:
        return {'views': '?', 'uniques': '?'}


# ─────────────────────────────────────────────────────
# AI BRIEFING
# ─────────────────────────────────────────────────────
def get_ai_briefing(stats, space_summary, revenue_summary):
    if not OR_KEY or not requests:
        return ''
    prompt = f"""Write Meeko's morning briefing. Today: {datetime.now(timezone.utc).strftime('%A %B %d, %Y')}.

Gallery stats: {stats['views']} views, {stats['uniques']} unique visitors.
Space: {space_summary}
Revenue status: {revenue_summary}

Write a SHORT (150 word max), warm, personal morning briefing. Real. Brief. No corporate speak.
Note what the system did overnight, the most important action today, and something encouraging."""
    try:
        r = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OR_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 250},
            timeout=20
        )
        return r.json()['choices'][0]['message']['content'].strip()
    except:
        return ''


# ─────────────────────────────────────────────────────
# LOAD GRANTS
# ─────────────────────────────────────────────────────
BUILT_IN_GRANTS = [
    {'name': 'GitHub Sponsors', 'deadline': 'NOW — Enable on your profile', 'url': 'https://github.com/sponsors'},
    {'name': 'NLnet Foundation', 'deadline': 'Next cycle ~April 2026', 'url': 'https://nlnet.nl/propose'},
    {'name': 'Mozilla Tech Fund', 'deadline': 'Rolling', 'url': 'https://foundation.mozilla.org/en/what-we-fund'},
    {'name': 'Creative Capital', 'deadline': 'June 2026', 'url': 'https://creative-capital.org/apply'},
    {'name': 'Awesome Foundation', 'deadline': 'Monthly recurring', 'url': 'https://www.awesomefoundation.org'},
    {'name': 'Wikimedia Rapid Fund', 'deadline': 'Rolling (up to $50k)', 'url': 'https://meta.wikimedia.org/wiki/Grants:Start'},
    {'name': 'Knight Prototype Fund', 'deadline': 'Rolling', 'url': 'https://knightfoundation.org/prototype'},
]

def get_grants():
    # Try to read from grant scanner output first
    if GRANT_PATH.exists():
        scans = sorted(GRANT_PATH.glob('scan_*.json'), reverse=True)
        if scans:
            try:
                data = json.loads(scans[0].read_text())
                return sorted(data, key=lambda g: g.get('fit_score', 0), reverse=True)[:5]
            except:
                pass
    return BUILT_IN_GRANTS[:5]


# ─────────────────────────────────────────────────────
# BUILD EMAIL
# ─────────────────────────────────────────────────────
def build_email():
    now = datetime.now(timezone.utc).strftime('%A, %B %d %Y — %H:%M UTC')
    stats = get_gallery_stats()
    iss, crew, solar = get_space_data()
    bus = read_bus()
    revenue = read_revenue()

    # Build summaries for AI
    space_summary = (
        f"ISS at {iss.get('latitude','?')}°, {iss.get('longitude','?')}° — "
        f"crew: {', '.join(crew) if crew else 'unknown'} — "
        f"solar wind: {solar:.0f} km/s"
    ) if iss else 'Space data unavailable'

    revenue_summary = 'Gallery live · Fork guide product ready · Gumroad listing still needed'
    if revenue:
        live = [k for k,v in revenue.get('sources',{}).items() if isinstance(v,dict) and v.get('status')=='live']
        revenue_summary = f"Live: {', '.join(live)} | Next action: {revenue.get('next_action','')}"

    ai_text = get_ai_briefing(stats, space_summary, revenue_summary)

    # Grants section
    grants = get_grants()
    grants_lines = ''
    for g in grants:
        name = g.get('name', g.get('label','?'))
        deadline = g.get('next_deadline', g.get('deadline','?'))
        url = g.get('url','?')
        score = g.get('fit_score', '')
        score_str = f" [{score}% fit]" if score else ''
        grants_lines += f"  • {name}{score_str}\n    Deadline: {deadline}\n    {url}\n\n"

    # System status from bus
    sys_status = ''
    for k, v in bus.items():
        if k.startswith('_') or k in ('iss_position','iss_crew','solar_wind_kms','space_summary'): continue
        v_str = str(v)[:80]
        sys_status += f"  {k}: {v_str}\n"

    body = f"""MEEKO MYCELIUM — MORNING BRIEFING
{now}
{'='*55}

{ai_text if ai_text else 'AI briefing unavailable — all other data below.'}

{'='*55}
🛸 SPACE STATUS (via ISS API + NOAA)
  ISS position: {iss.get('latitude','?')}° lat, {iss.get('longitude','?')}° lon
  ISS crew:     {', '.join(crew) if crew else 'unknown'}
  Solar wind:   {f'{solar:.0f} km/s' if solar else 'unavailable'}

{'='*55}
🌹 GALLERY TRAFFIC (last 14 days)
  Views:   {stats['views']}
  Uniques: {stats['uniques']}
  URL: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

{'='*55}
💰 REVENUE STATUS
  ✓ Gaza Rose Gallery: LIVE (PayPal inline)
  ✓ Fork guide product: READY (products/fork-guide.md)
  ◦ Gumroad listing: NEEDED → gumroad.com (5 min setup)
  ◦ Ko-fi: NEEDED → ko-fi.com (5 min setup)
  ◦ GitHub Sponsors: NEEDED → enable at github.com/sponsors
  ◦ GMAIL_APP_PASSWORD: {"SET" if GMAIL_PASS else "MISSING → GitHub Secrets"}

{'='*55}
🌱 GRANT OPPORTUNITIES

{grants_lines}{'='*55}
🧠 ORCHESTRATOR BUS
{sys_status if sys_status else '  (no bus data yet — run ORCHESTRATOR.py)'}

{'='*55}
YOUR JOBS TODAY
  Priority 1: Enable GitHub Sponsors at github.com/sponsors/meekotharaccoon-cell
  Priority 2: Create $5 Gumroad listing — content at products/fork-guide.md
  Priority 3: Create Ko-fi page and add link to spawn.html
  Everything else: handled.

— Meeko Mycelium"""
    return body


# ─────────────────────────────────────────────────────
# SEND
# ─────────────────────────────────────────────────────
def send_briefing(body):
    if not GMAIL_PASS:
        print('[Briefing] No GMAIL_APP_PASSWORD — printing instead:')
        print(body)
        return
    msg = MIMEMultipart()
    msg['From'] = f'Mycelium System <{GMAIL_USER}>'
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'🌿 Mycelium Briefing — {datetime.now(timezone.utc).strftime("%b %d %H:%M")}'
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print(f'[Briefing] Sent to {GMAIL_USER}')


def run():
    body = build_email()
    send_briefing(body)

if __name__ == '__main__':
    run()
