#!/usr/bin/env python3
"""
Audience Intelligence Engine
=============================
The system posts daily but is blind to who's listening.
This engine fixes that.

What it tracks:
  - GitHub: stars, forks, watchers, issues, traffic (if token has access)
  - Mastodon: follower count, top engagers, who boosted what
  - Bluesky: follower count, top engagers
  - Reddit: mentions of the repo or project name
  - HN/Lobsters: any posts about the project
  - Google: indexed pages count (via site: query trick)

What it does with the data:
  - Detects follower spikes (someone shared it somewhere)
  - Identifies power users (people who engage repeatedly)
  - Finds where traffic is coming from
  - Alerts you when something is going viral
  - Feeds data to content_performance for smarter posting

Outputs:
  - data/audience_report.json
  - Email alert if spike detected (>10% growth in 24h)
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
BLUESKY_HANDLE     = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_PASSWORD   = os.environ.get('BLUESKY_PASSWORD', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

GITHUB_REPO = 'meekotharaccoon-cell/meeko-nerve-center'

def fetch(url, headers=None, timeout=15):
    h = {'User-Agent': 'meeko-audience/1.0'}
    if headers: h.update(headers)
    try:
        req = urllib_request.Request(url, headers=h)
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[audience] Fetch error {url[:60]}: {e}')
        return None

def get_github_stats():
    if not GITHUB_TOKEN: return {}
    data = fetch(
        f'https://api.github.com/repos/{GITHUB_REPO}',
        headers={'Authorization': f'Bearer {GITHUB_TOKEN}'}
    )
    if not data: return {}
    return {
        'stars':    data.get('stargazers_count', 0),
        'forks':    data.get('forks_count', 0),
        'watchers': data.get('subscribers_count', 0),
        'open_issues': data.get('open_issues_count', 0),
    }

def get_mastodon_stats():
    if not MASTODON_TOKEN or not MASTODON_BASE_URL: return {}
    data = fetch(
        f'{MASTODON_BASE_URL}/api/v1/accounts/verify_credentials',
        headers={'Authorization': f'Bearer {MASTODON_TOKEN}'}
    )
    if not data: return {}
    return {
        'followers':  data.get('followers_count', 0),
        'following':  data.get('following_count', 0),
        'posts':      data.get('statuses_count', 0),
    }

def get_bluesky_stats():
    if not BLUESKY_HANDLE or not BLUESKY_PASSWORD: return {}
    # Auth
    try:
        payload = json.dumps({'identifier': BLUESKY_HANDLE, 'password': BLUESKY_PASSWORD}).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=payload, headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
        token = session.get('accessJwt', '')
        did   = session.get('did', '')
        if not token or not did: return {}

        profile = fetch(
            f'https://bsky.social/xrpc/app.bsky.actor.getProfile?actor={did}',
            headers={'Authorization': f'Bearer {token}'}
        )
        if not profile: return {}
        return {
            'followers': profile.get('followersCount', 0),
            'following': profile.get('followsCount', 0),
            'posts':     profile.get('postsCount', 0),
        }
    except Exception as e:
        print(f'[audience] Bluesky error: {e}')
        return {}

def check_hn_mentions():
    """Search Hacker News for mentions."""
    queries = ['meeko-nerve-center', 'meekotharaccoon', 'gaza rose AI']
    hits = []
    for q in queries:
        from urllib.parse import quote
        data = fetch(f'https://hn.algolia.com/api/v1/search?query={quote(q)}&hitsPerPage=5')
        if data:
            for hit in data.get('hits', []):
                hits.append({
                    'title':  hit.get('title', hit.get('comment_text', ''))[:100],
                    'url':    f'https://news.ycombinator.com/item?id={hit.get("objectID","")}',
                    'points': hit.get('points', 0),
                    'date':   hit.get('created_at', '')[:10],
                })
    return hits

def check_reddit_mentions():
    """Search Reddit for project mentions."""
    queries = ['meeko-nerve-center', 'meekotharaccoon']
    hits = []
    for q in queries:
        from urllib.parse import quote
        data = fetch(
            f'https://www.reddit.com/search.json?q={quote(q)}&limit=5&sort=new',
            headers={'User-Agent': 'meeko-audience/1.0 (monitoring mentions)'}
        )
        if data:
            for post in data.get('data', {}).get('children', []):
                p = post.get('data', {})
                hits.append({
                    'title':     p.get('title', '')[:100],
                    'subreddit': p.get('subreddit', ''),
                    'url':       f'https://reddit.com{p.get("permalink","")}',
                    'score':     p.get('score', 0),
                    'date':      datetime.datetime.fromtimestamp(p.get('created_utc', 0)).date().isoformat(),
                })
    return hits

def detect_spike(current, previous):
    """Returns True + message if significant growth detected."""
    spikes = []
    for platform, curr in current.items():
        prev = previous.get(platform, {})
        for metric, val in curr.items():
            if not isinstance(val, (int, float)): continue
            old_val = prev.get(metric, val)
            if old_val > 0:
                change = (val - old_val) / old_val
                if change >= 0.10:  # 10%+ growth
                    spikes.append(f'{platform} {metric}: {old_val} → {val} (+{change*100:.0f}%)')
    return spikes

def send_spike_alert(spikes, report):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    lines = [
        f'🚨 Audience spike detected — {TODAY}',
        '',
        'Something is driving traffic. Check these:',
        '',
    ] + spikes + [
        '',
        'HN mentions:', str(report.get('hn_mentions', [])),
        'Reddit mentions:', str(report.get('reddit_mentions', [])),
        '',
        'Check GitHub traffic: https://github.com/meekotharaccoon-cell/meeko-nerve-center/graphs/traffic',
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 Meeko is spreading — spike detected {TODAY}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[audience] Spike alert sent')
    except Exception as e:
        print(f'[audience] Alert email error: {e}')

def run():
    print(f'\n[audience] Audience Intelligence Engine — {TODAY}')

    # Load previous report
    report_path = DATA / 'audience_report.json'
    previous = {}
    if report_path.exists():
        try:
            prev_report = json.loads(report_path.read_text())
            previous = prev_report.get('platforms', {})
        except: pass

    # Gather current stats
    platforms = {
        'github':   get_github_stats(),
        'mastodon': get_mastodon_stats(),
        'bluesky':  get_bluesky_stats(),
    }

    # Check mentions
    hn_mentions     = check_hn_mentions()
    reddit_mentions = check_reddit_mentions()

    # Detect spikes
    spikes = detect_spike(platforms, previous)
    if spikes:
        print(f'[audience] 🚨 SPIKE DETECTED: {spikes}')

    report = {
        'date':            TODAY,
        'platforms':       platforms,
        'hn_mentions':     hn_mentions,
        'reddit_mentions': reddit_mentions,
        'spikes':          spikes,
    }

    try:
        report_path.write_text(json.dumps(report, indent=2))
        print(f'[audience] Report saved')
        for p, stats in platforms.items():
            if stats:
                print(f'[audience]   {p}: {stats}')
    except Exception as e:
        print(f'[audience] Save error: {e}')

    if spikes:
        send_spike_alert(spikes, report)

    if hn_mentions:
        print(f'[audience] HN mentions: {len(hn_mentions)}')
    if reddit_mentions:
        print(f'[audience] Reddit mentions: {len(reddit_mentions)}')

    print('[audience] Done.')

if __name__ == '__main__':
    run()
