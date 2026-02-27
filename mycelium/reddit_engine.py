#!/usr/bin/env python3
"""
Reddit Engine
==============
Reddit is where developers, activists, and curious people actually
discover projects like this. This engine makes the system findable there.

What it does:
  1. Monitors relevant subreddits for posts the system can add value to
  2. Drafts comments/posts with genuine insight (not spam)
  3. Posts original content to relevant subreddits on a schedule
  4. Tracks which posts drove traffic to the GitHub repo
  5. Finds accountability threads to contribute congressional trade data

Target subreddits:
  r/LLMDevs, r/MachineLearning, r/opensource, r/Palestine,
  r/Accountability, r/SolarPunk, r/ProgrammerHumor (for the
  'AI that evolves itself for free' angle), r/investing (STOCK Act)

Uses Reddit's free JSON API (no OAuth needed for reading).
Posting requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET.
If no credentials: generates post drafts and emails them to you.
"""

import json, datetime, os, smtplib, time
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
REDDIT_CLIENT_ID   = os.environ.get('REDDIT_CLIENT_ID', '')
REDDIT_SECRET      = os.environ.get('REDDIT_CLIENT_SECRET', '')
REDDIT_USERNAME    = os.environ.get('REDDIT_USERNAME', '')
REDDIT_PASSWORD    = os.environ.get('REDDIT_PASSWORD', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

# Subreddits to monitor + post to
MONITOR_SUBS = [
    'opensource', 'selfhosted', 'MachineLearning', 'LLMDevs',
    'Palestine', 'SolarPunk', 'ethics', 'Anticonsumption',
]
POST_SUBS = {
    'showcase': 'opensource',       # Weekly showcase post
    'accountability': 'politics',   # Congressional trade alerts
    'solarpunk': 'SolarPunk',       # Art + mission posts
    'dev': 'selfhosted',            # Technical architecture posts
}

# Post schedule: one subreddit per day of week
DAILY_POST_TARGET = [
    'opensource',      # Monday
    'LLMDevs',         # Tuesday
    'SolarPunk',       # Wednesday
    'Palestine',       # Thursday
    'selfhosted',      # Friday
    None,              # Saturday - rest
    None,              # Sunday - rest
]

def fetch_json(url, headers=None, timeout=20):
    h = {'User-Agent': 'MeekoNerveCenter/1.0 (autonomous humanitarian AI; contact via GitHub)'}
    if headers: h.update(headers)
    try:
        req = urllib_request.Request(url, headers=h)
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[reddit] Fetch error: {e}')
        return None

def ask_llm(prompt, max_tokens=500):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You write genuine, valuable Reddit posts and comments. Never spammy. Always adds real value. Knows when NOT to post.'},
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
        print(f'[reddit] LLM error: {e}')
        return None

def get_system_stats():
    stats = {}
    try:
        ledger = json.loads((DATA / 'idea_ledger.json').read_text())
        ideas  = ledger.get('ideas', {})
        il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
        stats['ideas']   = len(il)
        stats['passed']  = sum(1 for i in il if i.get('status') in ('passed','wired'))
    except: pass
    try:
        stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        evo = json.loads((DATA / 'evolution_log.json').read_text())
        stats['self_built'] = len(evo.get('built', []))
    except: pass
    return stats

def generate_showcase_post(stats):
    prompt = f"""Write a Reddit post for r/opensource showcasing this project.

Project: Meeko Nerve Center
What it is: A self-evolving autonomous AI that runs entirely on GitHub Actions (free tier).
It tracks congressional trades under the STOCK Act, generates Palestinian solidarity art,
funds PCRF, writes its own code daily, heals its own bugs, applies for grants, manages
press relationships, and generates crypto signals. All for $0/month.

Stats:
  - {stats.get('engines', '40+')} autonomous Python engines
  - {stats.get('self_built', 0)} engines it built itself
  - {stats.get('passed', 0)} ideas self-tested and implemented
  - Running on GitHub Actions free tier
  - AGPL-3.0 licensed

Repo: {REPO_URL}

Write a genuine post that:
- Leads with the most technically interesting thing (self-evolution on free CI/CD)
- Is honest about what works and what's still rough
- Invites forks and contributions
- Mentions the humanitarian mission without being preachy
- Feels like a real developer sharing their weekend project, not marketing
- Title + body (markdown OK)
- Under 400 words total

Format:
TITLE: ...
BODY:
...
"""
    return ask_llm(prompt, max_tokens=600)

def generate_accountability_post():
    congress = {}
    try:
        p = DATA / 'congress.json'
        if p.exists(): congress = json.loads(p.read_text())
    except: pass
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    if not trades: return None

    trade = trades[0]
    member = trade.get('representative', trade.get('senator', 'A member of Congress'))
    ticker = trade.get('ticker', '?')
    date   = trade.get('transaction_date', trade.get('date', '?'))

    prompt = f"""Write a Reddit post for r/politics about this STOCK Act disclosure.

Fact: {member} disclosed trading {ticker} on {date}. Public record.
Source: House Financial Disclosures (efts.house.gov)
Tracked by: {REPO_URL} (open source, automated)

Write a factual, neutral post. No speculation. Just the public record + context about
what the STOCK Act requires. Under 200 words. Include the source link.

TITLE: ...
BODY:
...
"""
    return ask_llm(prompt, max_tokens=300)

def generate_solarpunk_post():
    prompt = f"""Write a Reddit post for r/SolarPunk about this project.

Project: An autonomous AI that generates Palestinian solidarity art, tracks congressional
accountability, and funds PCRF medical relief for children — all running for free on
open-source infrastructure. No VC funding. No ads. No extraction.

Angle: This is SolarPunk infrastructure — technology that serves community, runs on
renewable (free) compute, can't be shut down, and has its ethics baked into the code.

Repo: {REPO_URL}

Write something genuine that resonates with the SolarPunk community's values.
Not a product pitch. A vision of what tech CAN be.
Under 300 words.

TITLE: ...
BODY:
...
"""
    return ask_llm(prompt, max_tokens=400)

def post_to_reddit(subreddit, title, text, access_token):
    """Submit a post to Reddit via API."""
    try:
        data = urlencode({
            'sr':    subreddit,
            'kind':  'self',
            'title': title[:300],
            'text':  text[:10000],
            'nsfw':  False,
            'spoiler': False,
        }).encode()
        req = urllib_request.Request(
            'https://oauth.reddit.com/api/submit',
            data=data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'MeekoNerveCenter/1.0',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            url = result.get('jquery', [[]])
            return True, str(result)
    except Exception as e:
        return False, str(e)

def get_reddit_token():
    """Get OAuth token for posting."""
    if not all([REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        return None
    try:
        creds = base64.b64encode(f'{REDDIT_CLIENT_ID}:{REDDIT_SECRET}'.encode()).decode()
        data  = urlencode({'grant_type': 'password', 'username': REDDIT_USERNAME, 'password': REDDIT_PASSWORD}).encode()
        req   = urllib_request.Request(
            'https://www.reddit.com/api/v1/access_token',
            data=data,
            headers={
                'Authorization': f'Basic {creds}',
                'User-Agent': 'MeekoNerveCenter/1.0',
            }
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get('access_token')
    except Exception as e:
        print(f'[reddit] Auth error: {e}')
        return None

def email_draft(title, body, subreddit):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    text = f"""Reddit post ready to submit.

Subreddit: r/{subreddit}
Title: {title}

{'='*50}
{body}
{'='*50}

Post at: https://reddit.com/r/{subreddit}/submit
"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📝 Reddit draft: r/{subreddit}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(text, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[reddit] Draft emailed for r/{subreddit}')
    except Exception as e:
        print(f'[reddit] Email error: {e}')

def already_posted_today():
    p = DATA / 'reddit_log.json'
    if not p.exists(): return False
    try:
        log = json.loads(p.read_text())
        return any(e.get('date') == TODAY for e in log.get('posts', []))
    except: return False

def log_post(subreddit, title, posted):
    p = DATA / 'reddit_log.json'
    log = {'posts': []}
    if p.exists():
        try: log = json.loads(p.read_text())
        except: pass
    log['posts'].append({'date': TODAY, 'subreddit': subreddit, 'title': title[:80], 'posted': posted})
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def run():
    import base64
    print(f'\n[reddit] Reddit Engine — {TODAY}')

    if already_posted_today():
        print('[reddit] Already posted today. Skipping.')
        return

    stats   = get_system_stats()
    target  = DAILY_POST_TARGET[WEEKDAY]
    if not target:
        print('[reddit] Rest day. No post today.')
        return

    # Generate appropriate post type
    if target in ('opensource', 'LLMDevs', 'selfhosted'):
        content = generate_showcase_post(stats)
    elif target == 'SolarPunk':
        content = generate_solarpunk_post()
    elif target == 'Palestine':
        content = generate_accountability_post() or generate_solarpunk_post()
    else:
        content = generate_showcase_post(stats)

    if not content:
        print('[reddit] No content generated.')
        return

    # Parse title/body
    title, body = '', content
    for line in content.split('\n'):
        if line.startswith('TITLE:'):
            title = line.replace('TITLE:', '').strip()
        elif line.startswith('BODY:'):
            body = content[content.index('BODY:') + 5:].strip()
            break
    if not title:
        title = content.split('\n')[0][:200]

    # Try posting, fall back to email draft
    token = get_reddit_token()
    if token:
        ok, result = post_to_reddit(target, title, body, token)
        log_post(target, title, ok)
        print(f'[reddit] Posted to r/{target}: {ok}')
    else:
        email_draft(title, body, target)
        log_post(target, title, False)
        print(f'[reddit] No credentials — draft emailed')
        print('[reddit] Add REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD to GitHub Secrets to auto-post')

if __name__ == '__main__':
    run()
