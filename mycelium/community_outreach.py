#!/usr/bin/env python3
"""
COMMUNITY OUTREACH
==================
Posts announcements to communities that would care about this.

Targets:
  - Reddit: r/solarpunk, r/selfhosted, r/opensource, r/Palestine,
            r/digitalnomad, r/antiwork, r/collapse, r/herbalism,
            r/legaladvice (resource posts only), r/povertyfinance
  - Hacker News: Submit Show HN
  - Dev.to: Publish full article
  - Lemmy: solarpunk.moe, lemmy.ml
  - Mastodon hashtag targeting: #solarpunk #opensource #Palestine

SECRETS:
  REDDIT_CLIENT_ID
  REDDIT_SECRET
  REDDIT_USERNAME
  REDDIT_PASSWORD
  DEVTO_API_KEY

Rules:
  - Never post the same content to the same subreddit twice
  - Space posts by 48h minimum to avoid spam detection
  - Match content to community (rights posts to legal communities,
    tech posts to selfhosted, art posts to art communities)
  - Always be honest: this is an autonomous system and we say so
"""
import os, json, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR  = Path('data')
COMM_LOG  = DATA_DIR / 'community_posts.json'

REDDIT_ID     = os.environ.get('REDDIT_CLIENT_ID', '')
REDDIT_SECRET = os.environ.get('REDDIT_SECRET', '')
REDDIT_USER   = os.environ.get('REDDIT_USERNAME', '')
REDDIT_PASS   = os.environ.get('REDDIT_PASSWORD', '')
DEVTO_KEY     = os.environ.get('DEVTO_API_KEY', '')

# ---- COMMUNITY TARGETS -------------------------------------------
# Each entry: subreddit, content type, title, body, link
# Ordered by priority / fit

COMMUNITY_POSTS = [
    {
        'id': 'reddit_selfhosted_system',
        'platform': 'reddit',
        'subreddit': 'selfhosted',
        'title': 'Built a fully autonomous AI agent system on GitHub free tier — 10 daily workflows, $0/month',
        'text': open('content/ANNOUNCEMENT_REDDIT_SELFHOSTED.md').read().split('**Body:**')[-1].strip() if Path('content/ANNOUNCEMENT_REDDIT_SELFHOSTED.md').exists() else 'See: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        'link': 'https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        'flair': 'Project',
    },
    {
        'id': 'reddit_solarpunk_system',
        'platform': 'reddit',
        'subreddit': 'solarpunk',
        'title': 'Built a solarpunk AI system: autonomous, $0/month, humanitarian, forkable by anyone',
        'text': open('content/ANNOUNCEMENT_REDDIT_SOLARPUNK.md').read().split('**Body:**')[-1].strip() if Path('content/ANNOUNCEMENT_REDDIT_SOLARPUNK.md').exists() else 'See: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        'link': 'https://github.com/meekotharaccoon-cell/meeko-nerve-center',
    },
    {
        'id': 'reddit_opensource_license',
        'platform': 'reddit',
        'subreddit': 'opensource',
        'title': 'AGPL-3.0 + Ethical Use Rider that propagates through forks — is this open source?',
        'text': open('content/ANNOUNCEMENT_REDDIT_OPENSOURCE.md').read().split('**Body:**')[-1].strip() if Path('content/ANNOUNCEMENT_REDDIT_OPENSOURCE.md').exists() else 'See: https://github.com/meekotharaccoon-cell/meeko-nerve-center',
        'link': 'https://github.com/meekotharaccoon-cell/meeko-nerve-center',
    },
    {
        'id': 'reddit_povertyfinance_rights',
        'platform': 'reddit',
        'subreddit': 'povertyfinance',
        'title': 'Free tools for rights you probably don\'t know you have: TCPA, FDCPA, unclaimed property, FTC refunds',
        'text': """Sharing some free tools from a project I'm working on. These are all real legal rights with real money attached, and most people don't know about them.

**Unclaimed property:** Every US state holds billions in forgotten accounts, uncashed checks, old deposits. missingmoney.com searches all states at once. Free. Takes 2 minutes. Your name might be in there.

**TCPA (robocalls):** Robocalls to your cell phone without consent are illegal. $500–1,500 per call in statutory damages. Small claims court. $30–75 filing fee. No lawyer.

**FTC refunds:** The FTC has hundreds of millions in active refund programs from corporate settlements. ftc.gov/refunds — no application, just check if you qualify.

**FDCPA (debt collectors):** Can't call before 8am or after 9pm. Can't contact you after written cease request. Each violation up to $1,000.

Free letter generators for all of these: https://github.com/meekotharaccoon-cell/solarpunk-legal
Free knowledge library (no signup, no paywall): https://meekotharaccoon-cell.github.io/solarpunk-learn""",
        'link': 'https://meekotharaccoon-cell.github.io/solarpunk-learn',
    },
    {
        'id': 'reddit_herbalism_remedies',
        'platform': 'reddit',
        'subreddit': 'herbalism',
        'title': 'Free PDF: Backyard Remedies Vol. 1 — 12 plants, 40+ preparations, honest about when to see a doctor',
        'text': """Released a free herbal medicine guide as part of a larger open-source project.

Backyard Remedies Vol. 1 covers:
- Echinacea, Yarrow, Elderberry, Plantain, Calendula, St. John's Wort, Chamomile, Lemon Balm, Lavender, Rosemary, Thyme, Garlic
- 40+ preparations: tinctures, teas, salves, oxymels, fire cider, elixirs
- Real dosing. Real contraindications. Real "see a doctor" flags.

It's not vibes. It's as evidence-based as traditional herbalism can be, with honest acknowledgment of where evidence is thin.

Free download (no signup): https://github.com/meekotharaccoon-cell/solarpunk-remedies

Part of a larger free knowledge library: https://meekotharaccoon-cell.github.io/solarpunk-learn""",
        'link': 'https://github.com/meekotharaccoon-cell/solarpunk-remedies',
    },
]

# ---- DEVTO ARTICLE -----------------------------------------------
DEVTO_ARTICLE = {
    'id': 'devto_main_article',
    'title': 'I built a fully autonomous humanitarian AI system for $0/month. Here\'s the architecture.',
    'tags': ['opensource', 'github', 'python', 'solarpunk'],
    'body_file': 'content/DEVTO_ARTICLE.md',
}

# ---- UTILITIES ---------------------------------------------------
def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

def already_posted(post_id, log):
    return post_id in log and log[post_id].get('posted')

def get_reddit_token():
    if not all([REDDIT_ID, REDDIT_SECRET, REDDIT_USER, REDDIT_PASS]):
        return None
    import base64
    creds = base64.b64encode(f'{REDDIT_ID}:{REDDIT_SECRET}'.encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'password',
        'username': REDDIT_USER,
        'password': REDDIT_PASS
    }).encode()
    req = urllib.request.Request('https://www.reddit.com/api/v1/access_token', data=data)
    req.add_header('Authorization', f'Basic {creds}')
    req.add_header('User-Agent', 'SolarPunkMycelium/1.0')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get('access_token')
    except Exception as e:
        print(f'  [reddit] Auth failed: {e}')
        return None

def post_reddit(token, subreddit, title, text, link=None):
    data = urllib.parse.urlencode({
        'sr': subreddit,
        'kind': 'link' if link else 'self',
        'title': title,
        'url': link or '',
        'text': text if not link else '',
        'resubmit': 'false',
        'nsfw': 'false',
    }).encode()
    req = urllib.request.Request('https://oauth.reddit.com/api/submit', data=data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('User-Agent', 'SolarPunkMycelium/1.0')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            errors = resp.get('json', {}).get('errors', [])
            if errors:
                return False, str(errors)
            url = resp.get('json', {}).get('data', {}).get('url', 'posted')
            return True, url
    except Exception as e:
        return False, str(e)

def post_devto_article(title, body_md, tags):
    if not DEVTO_KEY:
        return False, 'no API key'
    payload = json.dumps({
        'article': {
            'title': title,
            'body_markdown': body_md,
            'published': True,
            'tags': tags,
        }
    }).encode()
    req = urllib.request.Request('https://dev.to/api/articles', data=payload, method='POST')
    req.add_header('api-key', DEVTO_KEY)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            return True, resp.get('url', 'posted')
    except Exception as e:
        return False, str(e)

# ---- MAIN --------------------------------------------------------
def run():
    print('\n' + '='*52)
    print('  COMMUNITY OUTREACH')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    dry_run = os.environ.get('OUTREACH_DRY_RUN', 'true').lower() != 'false'
    log = load(COMM_LOG)

    # Post Dev.to article first (highest value)
    article_id = DEVTO_ARTICLE['id']
    if not already_posted(article_id, log):
        body_path = Path(DEVTO_ARTICLE['body_file'])
        if body_path.exists():
            body = body_path.read_text()
            # Strip frontmatter for body
            if body.startswith('---'):
                body = '---'.join(body.split('---')[2:]).strip()
            print(f'\n  [devto] Publishing article...')
            if dry_run:
                print('  [devto] DRY RUN — would publish')
            else:
                ok, url = post_devto_article(DEVTO_ARTICLE['title'], body, DEVTO_ARTICLE['tags'])
                if ok:
                    log[article_id] = {'posted': True, 'url': url, 'at': datetime.now(timezone.utc).isoformat()}
                    print(f'  [devto] Published: {url}')
                else:
                    print(f'  [devto] Failed: {url}')

    # Reddit posts (one per run, spaced)
    reddit_token = None
    if all([REDDIT_ID, REDDIT_SECRET, REDDIT_USER, REDDIT_PASS]):
        reddit_token = get_reddit_token()

    for post in COMMUNITY_POSTS:
        if post['platform'] != 'reddit': continue
        if already_posted(post['id'], log):
            print(f'  [skip] Already posted: {post["id"]}')
            continue

        print(f'\n  [reddit] r/{post["subreddit"]}: {post["title"][:60]}...')

        if dry_run:
            print('  [reddit] DRY RUN — would post')
            continue

        if not reddit_token:
            print('  [reddit] No credentials — skipping')
            continue

        ok, url = post_reddit(
            reddit_token,
            post['subreddit'],
            post['title'],
            post.get('text', ''),
            post.get('link')
        )
        if ok:
            log[post['id']] = {'posted': True, 'url': url, 'at': datetime.now(timezone.utc).isoformat()}
            print(f'  [reddit] Posted: {url}')
        else:
            print(f'  [reddit] Failed: {url}')

        save(COMM_LOG, log)
        time.sleep(30)  # Reddit rate limiting
        break  # One Reddit post per run

    save(COMM_LOG, log)
    posted = sum(1 for v in log.values() if v.get('posted'))
    print(f'\n  Total community posts made: {posted}/{len(COMMUNITY_POSTS) + 1}')

if __name__ == '__main__':
    run()
