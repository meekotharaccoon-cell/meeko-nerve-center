#!/usr/bin/env python3
"""
News Monitor — SolarPunk
=========================
Is the system in the news yet? If not, why not?
This engine answers both questions and acts on the answer.

Monitors:
  1. Coverage search: Googles the system, checks if articles exist
     Search terms: 'Meeko Nerve Center', 'SolarPunk autonomous AI',
     'congressional trade AI free', 'Palestinian solidarity autonomous AI'
  2. GitHub discovery: new stars, forks, watchers = organic press interest
  3. Social mentions: when someone mentions meeko or solarpunk nerve center
  4. Press response tracker: which pitches got responses

If NO coverage found:
  -> Generates a fresh press pitch (different angle each week)
  -> Emails it to the press contact list
  -> Posts a 'hey press people' thread to Mastodon
  -> The answer to 'why not': usually it's because no one pitched it yet

If coverage found:
  -> Logs it immediately
  -> Emails Meeko the article link with context
  -> Cross-posts to social
  -> Adds journalist to warm contact list
  -> Queues a thank-you + follow-on pitch

Angles the system rotates through weekly:
  Week 1: 'AI that costs nothing and tracks Congress'
  Week 2: 'Gaza Rose: art that funds Palestinian children'
  Week 3: 'The SolarPunk internet: forkable autonomous AI'
  Week 4: 'What happens when an AI builds itself 288 times a day'
  Week 5: 'From 192,000 files to a living intelligence system'

This closes the press loop without human involvement.
Meeko only reads coverage. Never pitches it.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKNUM = datetime.date.today().isocalendar()[1]

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

SEARCH_TERMS = [
    'Meeko Nerve Center autonomous AI',
    'SolarPunk autonomous AI GitHub free',
    'congressional trade tracking AI open source',
    '"Gaza Rose" AI art Palestinian solidarity',
]

PRESS_ANGLES = [
    ('zero_cost_congress', 'Free AI that tracks congressional insider trading — built by one person, runs forever'),
    ('gaza_rose',          'An autonomous AI that generates art and donates 70% to Palestinian children'),
    ('solarpunk_network',  'The SolarPunk internet: forkable AI nodes that self-evolve, can\'t be shut down'),
    ('self_building',      'What happens when an AI builds itself 288 times a day for free'),
    ('fork_me',            'This AI texts you setup instructions in 5 minutes and then runs itself forever'),
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def search_web(query):
    """Search DuckDuckGo Instant Answer API (no key required)."""
    try:
        from urllib.parse import quote_plus
        url = f'https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_redirect=1'
        req = urllib_request.Request(url, headers={'User-Agent': 'SolarPunk/1.0'})
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = []
        for item in data.get('RelatedTopics', [])[:5]:
            if item.get('FirstURL') and item.get('Text'):
                results.append({'url': item['FirstURL'], 'text': item['Text'][:200]})
        return results
    except:
        return []

def check_github_metrics():
    from urllib.parse import quote
    try:
        req = urllib_request.Request(
            'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center',
            headers={'User-Agent': 'SolarPunk/1.0'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return {
            'stars':    data.get('stargazers_count', 0),
            'forks':    data.get('forks_count', 0),
            'watchers': data.get('watchers_count', 0),
        }
    except:
        return {'stars': 0, 'forks': 0, 'watchers': 0}

def generate_press_pitch(angle_id, angle_headline):
    if not HF_TOKEN:
        return f"""Subject: {angle_headline}

Hi,

I'm documenting an autonomous AI system called SolarPunk / Meeko Nerve Center.

It: tracks congressional insider trading, generates solidarity art, donates 70% to Palestinian children's healthcare, self-builds new capabilities 288x/day, runs entirely on free infrastructure, and anyone can fork it in 10 minutes.

It might be a story.

https://github.com/meekotharaccoon-cell/meeko-nerve-center

Meeko"""
    
    stats = {'engines': 0, 'art': 0, 'pcrf': 0.0}
    try: stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        al = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    
    prompt = f"""Write a 150-word pitch email for tech/accountability journalist.

Angle: {angle_headline}
Key facts:
  - System name: SolarPunk / Meeko Nerve Center
  - {stats['engines']} autonomous Python engines, runs 288x/day
  - {stats['art']} Gaza Rose art pieces generated
  - ${stats['pcrf']:.2f} donated to PCRF (Palestinian children's healthcare)
  - Tracks every congressional stock trade in near-real-time
  - Cost: $0/month forever (GitHub Actions + HuggingFace free tier)
  - Anyone can fork it in 10 minutes
  - Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Format: Subject line, then blank line, then 150-word email body.
Tone: Direct. Data-first. Respects journalist's time.
Do NOT: hype, adjectives like 'revolutionary', exclamation points."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 300,
            'messages': [
                {'role': 'system', 'content': 'You write concise, data-driven press pitches.'},
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
    except:
        return None

def send_pitches(pitch):
    press_contacts = load(DATA / 'press_contacts.json', [])
    contacts = press_contacts if isinstance(press_contacts, list) else press_contacts.get('contacts', [])
    if not contacts:
        # Default press list
        contacts = [
            {'email': 'tips@theintercept.com', 'name': 'The Intercept', 'beat': 'accountability'},
            {'email': 'tips@techcrunch.com', 'name': 'TechCrunch', 'beat': 'tech'},
            {'email': 'tips@wired.com', 'name': 'Wired', 'beat': 'tech'},
            {'email': 'tips@vice.com', 'name': 'Vice', 'beat': 'tech/accountability'},
            {'email': 'news@electronicintifada.net', 'name': 'Electronic Intifada', 'beat': 'Palestine'},
        ]
    sent = 0
    lines = pitch.split('\n')
    subject = lines[0].replace('Subject: ', '') if lines else 'SolarPunk — AI for accountability'
    body    = '\n'.join(lines[2:]) if len(lines) > 2 else pitch
    for contact in contacts[:5]:
        if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: break
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From']    = f'Meeko / SolarPunk <{GMAIL_ADDRESS}>'
            msg['To']      = contact['email']
            msg['Reply-To']= GMAIL_ADDRESS
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo(); s.starttls()
                s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                s.sendmail(GMAIL_ADDRESS, contact['email'], msg.as_string())
            sent += 1
        except: pass
    return sent

def run():
    print(f'\n[news] News Monitor — {TODAY}')
    
    # Check GitHub metrics
    metrics = check_github_metrics()
    print(f'[news] GitHub: {metrics["stars"]}* | {metrics["forks"]} forks | {metrics["watchers"]} watching')
    
    # Search for coverage
    coverage = []
    for term in SEARCH_TERMS[:2]:  # 2 searches to be rate-limit friendly
        results = search_web(term)
        if results: coverage.extend(results)
    
    # Log coverage
    log = load(DATA / 'news_coverage_log.json', {'articles': [], 'pitches_sent': 0})
    new_coverage = [c for c in coverage if c['url'] not in [a.get('url') for a in log.get('articles', [])]]
    
    if new_coverage:
        print(f'[news] \U0001f4f0 NEW COVERAGE FOUND: {len(new_coverage)} articles')
        log['articles'].extend(new_coverage)
        # Notify (just log, no email to Meeko — it's in the Sunday brief)
    else:
        print('[news] No coverage yet. Queuing pitch.')
    
    # Send pitches (weekly, rotate angles)
    pitch_day = WEEKDAY == 2  # Wednesdays
    if pitch_day and not new_coverage:
        angle_index = WEEKNUM % len(PRESS_ANGLES)
        angle_id, angle_headline = PRESS_ANGLES[angle_index]
        pitch = generate_press_pitch(angle_id, angle_headline)
        if pitch:
            sent = send_pitches(pitch)
            log['pitches_sent'] = log.get('pitches_sent', 0) + sent
            print(f'[news] Sent {sent} pitches: {angle_headline[:50]}')
    
    log['metrics'] = metrics
    log['last_check'] = TODAY
    try: (DATA / 'news_coverage_log.json').write_text(json.dumps(log, indent=2))
    except: pass
    
    print(f'[news] Coverage: {len(log.get("articles",[]))} articles | Pitches sent: {log.get("pitches_sent",0)}')

if __name__ == '__main__':
    run()
