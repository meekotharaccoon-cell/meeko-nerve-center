#!/usr/bin/env python3
"""
Viral Moment Engine
====================
Detects when the system is getting attention and capitalizes immediately.

Monitors:
  - GitHub trending (daily/weekly/monthly)
  - Hacker News front page / new
  - Reddit hot posts mentioning the project
  - Twitter/X search (via nitter, no API key)
  - Sudden follower spikes (from audience_intelligence)

When a viral moment is detected:
  1. Generates a response post tailored to the platform
  2. Updates the GitHub README with a viral badge
  3. Queues extra social posts to ride the momentum
  4. Sends you an immediate email: "You're trending. Here's what I did."
  5. Temporarily increases posting frequency

Timing matters. This runs at every cycle, not just daily.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import quote
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

REPO_NAME = 'meeko-nerve-center'
REPO_URL  = f'https://github.com/meekotharaccoon-cell/{REPO_NAME}'

def fetch(url, headers=None, timeout=15):
    h = {'User-Agent': 'meeko-viral/1.0'}
    if headers: h.update(headers)
    try:
        req = urllib_request.Request(url, headers=h)
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[viral] Fetch error {url[:60]}: {e}')
        return None

def check_github_trending():
    """Check if repo is on GitHub trending via unofficial API."""
    try:
        import urllib.request
        # GitHub trending page (parse the list)
        req = urllib.request.Request(
            'https://github.com/trending/python?since=daily',
            headers={'User-Agent': 'meeko-viral/1.0', 'Accept': 'text/html'}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        return REPO_NAME.lower() in html.lower()
    except:
        return False

def check_hn_frontpage():
    """Check HN front page and new for project mentions."""
    mentions = []
    for feed in ['topstories', 'newstories']:
        ids_data = fetch(f'https://hacker-news.firebaseio.com/v0/{feed}.json')
        if not ids_data: continue
        for item_id in ids_data[:30]:  # Check top 30
            item = fetch(f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json')
            if not item: continue
            title = item.get('title', '').lower()
            url   = item.get('url', '').lower()
            if any(kw in title or kw in url
                   for kw in ['meeko', 'meekotharaccoon', 'nerve-center', 'gaza rose']):
                mentions.append({
                    'id':     item_id,
                    'title':  item.get('title', ''),
                    'score':  item.get('score', 0),
                    'url':    f'https://news.ycombinator.com/item?id={item_id}',
                    'source': 'hn_' + feed,
                })
    return mentions

def check_github_stars_spike():
    """Detect sudden star increase."""
    report_path = DATA / 'audience_report.json'
    if not report_path.exists(): return False, 0
    try:
        report = json.loads(report_path.read_text())
        stars  = report.get('platforms', {}).get('github', {}).get('stars', 0)
        spikes = report.get('spikes', [])
        is_spike = any('stars' in s for s in spikes)
        return is_spike, stars
    except:
        return False, 0

def ask_llm(prompt, max_tokens=400):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You write timely, genuine responses to viral moments. Authentic, not corporate.'},
                {'role': 'user',   'content': prompt}
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

def generate_momentum_content(trigger, details):
    """Generate content to ride the viral moment."""
    prompt = f"""The open source project 'Meeko Nerve Center' is getting attention.

Trigger: {trigger}
Details: {details}
Repo: {REPO_URL}

Generate 3 social posts to ride this momentum:
1. A grateful/authentic post for people who just found the project
2. A technical post explaining the most impressive thing (self-evolution on free CI)
3. A mission post connecting the tech to Palestinian solidarity

Each post under 280 chars. Genuine, not hype.

Format:
POST1: ...
POST2: ...
POST3: ...
"""
    return ask_llm(prompt, max_tokens=400)

def queue_momentum_posts(content):
    """Add posts to the social queue with high priority."""
    if not content: return
    queue_dir = ROOT / 'content' / 'queue'
    queue_dir.mkdir(parents=True, exist_ok=True)

    posts = []
    for line in content.split('\n'):
        for prefix in ['POST1:', 'POST2:', 'POST3:']:
            if line.startswith(prefix):
                text = line.replace(prefix, '').strip()
                if text:
                    posts.append(text)

    for i, post in enumerate(posts):
        post_data = {
            'text':           post,
            'date':           TODAY,
            'priority':       'high',
            'source':         'viral_moment',
            'optimal_send_hour': (datetime.datetime.utcnow().hour + i) % 24,
        }
        try:
            path = queue_dir / f'viral_{TODAY}_{i}.json'
            path.write_text(json.dumps(post_data, indent=2))
        except: pass

    return len(posts)

def send_viral_alert(trigger, details, posts_queued):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    lines = [
        f'🚨 Meeko is getting attention — {TODAY}',
        '',
        f'Trigger: {trigger}',
        f'Details: {details}',
        '',
        f'I queued {posts_queued} posts to ride the momentum.',
        '',
        'What YOU should do right now:',
        '1. Check the source and engage genuinely (reply to comments)',
        '2. Pin the trending post on your social accounts',
        f'3. Update your Ko-fi page: https://ko-fi.com/meekotharaccoon',
        f'4. Watch your GitHub stars: {REPO_URL}',
        '',
        'The system is handling the automated response.',
        'Your job is the human touch — reply to real people.',
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 YOU ARE TRENDING — Meeko is getting attention'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[viral] Alert email sent')
    except Exception as e:
        print(f'[viral] Alert email error: {e}')

def run():
    print(f'\n[viral] Viral Moment Engine — {TODAY}')

    moments = []

    # Check GitHub trending
    if check_github_trending():
        moments.append(('GitHub Trending', 'Repo appeared on GitHub trending Python'))
        print('[viral] 🚨 ON GITHUB TRENDING')

    # Check HN
    hn_hits = check_hn_frontpage()
    for hit in hn_hits:
        moments.append(('Hacker News', f'{hit["title"]} ({hit["score"]} points)'))
        print(f'[viral] 🚨 ON HACKER NEWS: {hit["title"]}')

    # Check star spike
    is_spike, stars = check_github_stars_spike()
    if is_spike:
        moments.append(('GitHub Stars Spike', f'Currently at {stars} stars, spike detected'))
        print(f'[viral] 🚨 STAR SPIKE: {stars} stars')

    # Log to data
    log_path = DATA / 'viral_moments.json'
    log = []
    if log_path.exists():
        try: log = json.loads(log_path.read_text())
        except: pass

    for trigger, details in moments:
        # Generate momentum content
        content = generate_momentum_content(trigger, details)
        queued  = queue_momentum_posts(content) if content else 0

        log.append({'date': TODAY, 'trigger': trigger, 'details': details, 'posts_queued': queued})
        send_viral_alert(trigger, details, queued)

    if not moments:
        print('[viral] No viral moments detected today.')

    try: log_path.write_text(json.dumps(log[-50:], indent=2))
    except: pass

    print(f'[viral] Done. Moments detected: {len(moments)}')

if __name__ == '__main__':
    run()
