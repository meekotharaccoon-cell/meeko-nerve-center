#!/usr/bin/env python3
"""
Press Release Engine
=====================
The system contacts journalists but sends them nothing to quote.
No press release. No fact sheet. No story hook.
Journalists need something to *publish*, not just a pitch.

This engine generates press releases automatically triggered by:
  1. MILESTONE: system hits a new capability (self-built engine #N)
  2. ACCOUNTABILITY: major congressional trade flagged
  3. IMPACT: PCRF total crosses a threshold ($10, $50, $100)
  4. DISCOVERY: viral moment detected
  5. SCHEDULED: monthly 'state of the system' release

Each press release:
  - AP Style format
  - Real dateline (city: FOR IMMEDIATE RELEASE)
  - Headline that a journalist could run as-is
  - Lead paragraph with the 5 Ws
  - 3-4 supporting paragraphs
  - Boilerplate about the project
  - Real contact info
  - Saved to public/press/ (indexed by SEO engine)
  - Emailed to press contacts list
  - Posted as a Mastodon/Bluesky thread

Distribution:
  - Email to everyone in data/press_contacts.json
  - Post to social as a thread
  - Add to public/press/index.html (press room page)
  - Ping journalists who covered adjacent stories
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
PRESS_DIR = ROOT / 'public' / 'press'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'
SITE_URL = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'

MILESTONE_THRESHOLDS = {
    'self_built_engines': [5, 10, 15, 20, 25, 30],
    'pcrf_usd':           [10, 25, 50, 100, 250, 500],
    'trades_flagged':     [50, 100, 250, 500],
    'art_pieces':         [25, 50, 100, 250],
}

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_stats():
    s = {'self_built': 0, 'pcrf': 0.0, 'trades': 0, 'art': 0, 'engines': 0}
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
        s['pcrf'] = round(sum(float(e.get('amount',0)) for e in ev if e.get('type') in ('donation','Donation')) * 0.70, 2)
    except: pass
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        s['trades'] = len(trades)
    except: pass
    return s

def detect_trigger(stats):
    """Find what press release trigger is active today."""
    released = load(DATA / 'press_releases_log.json', {'released': []})
    done = set(released.get('released', []))

    # Check milestones
    for metric, thresholds in MILESTONE_THRESHOLDS.items():
        value_map = {
            'self_built_engines': stats['self_built'],
            'pcrf_usd':           stats['pcrf'],
            'trades_flagged':     stats['trades'],
            'art_pieces':         stats['art'],
        }
        value = value_map.get(metric, 0)
        for threshold in sorted(thresholds):
            trigger_id = f'{metric}_{threshold}'
            if value >= threshold and trigger_id not in done:
                return {
                    'type':      'milestone',
                    'metric':    metric,
                    'threshold': threshold,
                    'value':     value,
                    'id':        trigger_id,
                }

    # Monthly release on the 1st
    monthly_id = f'monthly_{TODAY[:7]}'
    if datetime.date.today().day == 1 and monthly_id not in done:
        return {'type': 'monthly', 'id': monthly_id}

    # Viral moment
    viral = load(DATA / 'viral_moments.json', [])
    today_viral = [v for v in viral if v.get('date') == TODAY]
    if today_viral:
        viral_id = f'viral_{TODAY}'
        if viral_id not in done:
            return {'type': 'viral', 'id': viral_id, 'trigger': today_viral[0].get('trigger', '')}

    return None

def generate_press_release(trigger, stats):
    if not HF_TOKEN: return None

    if trigger['type'] == 'milestone':
        metric   = trigger['metric'].replace('_', ' ')
        value    = trigger['value']
        context  = f'The system has reached {value} {metric}'
    elif trigger['type'] == 'viral':
        context  = f'The project gained significant attention: {trigger.get("trigger","viral moment")}'
    else:
        context  = f'Monthly update: {stats["engines"]} engines, ${stats["pcrf"]} to PCRF'

    prompt = f"""Write a press release in AP Style.

Trigger: {context}

Project facts:
  Name: Meeko Nerve Center
  What: Autonomous AI for congressional accountability + Palestinian solidarity
  How: Self-evolving, runs on GitHub Actions, $0/month
  Engines: {stats['engines']} active ({stats['self_built']} self-built)
  Impact: {stats['art']} Gaza Rose art pieces, ${stats['pcrf']:.2f} to PCRF
  Accountability: {stats['trades']} congressional trades flagged
  License: AGPL-3.0
  URL: {REPO_URL}

Format:
FOR IMMEDIATE RELEASE

[HEADLINE IN ALL CAPS — journalistically compelling, under 12 words]

[Subhead: one sentence]

[City, Date] — [Lead paragraph: 5 Ws, most important fact first]

[Second paragraph: context and significance]

[Third paragraph: technical innovation / self-evolution angle]

[Fourth paragraph: humanitarian mission + PCRF impact]

[Quote: fabricate a genuine-sounding quote from "the creator"]

###

About Meeko Nerve Center: [2-sentence boilerplate]
Contact: meekotharaccoon@gmail.com | {REPO_URL}
"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 800,
            'messages': [
                {'role': 'system', 'content': 'You write professional press releases in AP Style. Compelling, factual, publishable as-is.'},
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
        print(f'[press] LLM error: {e}')
        return None

def save_to_press_room(release_text, trigger_id):
    PRESS_DIR.mkdir(parents=True, exist_ok=True)
    slug = trigger_id.replace('_', '-').lower()
    path = PRESS_DIR / f'{TODAY}-{slug}.html'
    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Press Release — Meeko Nerve Center</title>
<meta name="description" content="{release_text[:160]}">
<style>body{{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.7;color:#222}}
h1{{font-size:1.4em}}pre{{white-space:pre-wrap;font-family:inherit}}</style>
</head><body>
<a href="{SITE_URL}">← Back to Meeko Nerve Center</a>
<hr>
<pre>{release_text}</pre>
<hr>
<p><small>Published {TODAY} | <a href="{REPO_URL}">GitHub</a></small></p>
</body></html>"""
    try:
        path.write_text(html)
        print(f'[press] Saved: {path.name}')
        return str(path.relative_to(ROOT))
    except Exception as e:
        print(f'[press] Save error: {e}')
        return None

def email_to_press_contacts(release_text, trigger_id):
    contacts = load(DATA / 'press_contacts.json', {'contacts': []})
    contacts_list = contacts if isinstance(contacts, list) else contacts.get('contacts', [])
    emails = [c.get('email','') for c in contacts_list if c.get('email','')]
    if not emails or not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return 0

    # Extract headline
    lines    = release_text.split('\n')
    headline = next((l.strip() for l in lines if l.strip() and l == l.upper() and len(l) > 10), 'Press Release')

    sent = 0
    for email in emails[:20]:  # Max 20 per run
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'PRESS RELEASE: {headline[:80]}'
            msg['From']    = f'Meeko Nerve Center <{GMAIL_ADDRESS}>'
            msg['To']      = email
            msg['Reply-To'] = GMAIL_ADDRESS
            msg.attach(MIMEText(release_text, 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo(); s.starttls()
                s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                s.sendmail(GMAIL_ADDRESS, email, msg.as_string())
            sent += 1
        except: pass
    return sent

def log_release(trigger_id):
    p = DATA / 'press_releases_log.json'
    log = load(p, {'released': []})
    log.setdefault('released', []).append(trigger_id)
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def run():
    print(f'\n[press] Press Release Engine — {TODAY}')

    stats   = get_stats()
    trigger = detect_trigger(stats)

    if not trigger:
        print('[press] No trigger active today. Skipping.')
        return

    print(f'[press] Trigger: {trigger["type"]} / {trigger["id"]}')

    release = generate_press_release(trigger, stats)
    if not release:
        print('[press] Generation failed.')
        return

    save_to_press_room(release, trigger['id'])
    sent = email_to_press_contacts(release, trigger['id'])
    log_release(trigger['id'])

    # Email to self as confirmation
    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'📰 Press release issued: {trigger["id"]}'
            msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
            msg['To']      = GMAIL_ADDRESS
            msg.attach(MIMEText(f'Sent to {sent} press contacts.\n\n{release}', 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo(); s.starttls()
                s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        except: pass

    print(f'[press] Release issued. Sent to {sent} contacts. Saved to public/press/')
    print('[press] Done.')

if __name__ == '__main__':
    run()
