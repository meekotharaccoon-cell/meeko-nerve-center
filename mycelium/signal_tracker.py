#!/usr/bin/env python3
"""
SIGNAL TRACKER
===============
The system's feedback loop. Tells us what's actually working.

Without this, the system is posting into a void. With it, the system
knows: which content types drive gallery visits, which email subjects
get replies, which posts get shared, what time of day converts best.

Sources pulled:
  - GitHub Pages traffic (via GitHub API — views/unique visitors per page)
  - Gumroad sales (linked to dates = linked to what was posted that day)
  - Email reply rates (from sent log vs. reply detection)
  - Cross-poster engagement (Mastodon favorites/boosts via API)
  - YouTube analytics (views/CTR per video via Data API)

Outputs:
  - data/signals.json — raw signal data
  - data/what_works.json — ranked content performance
  - Weekly digest committed to repo + emailed to system address

The system uses this to weight ROTATING_POSTS toward what converts.
High-performing content types get posted more. Low-performing get retired.
This is the loop that lets the system improve itself.

No third-party analytics. No tracking pixels. No data leaving the system.
All signals come from APIs the system already has access to.
"""
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
try:
    import urllib.request, urllib.error
except: pass

DATA_DIR    = Path('data')
SIGNAL_FILE = DATA_DIR / 'signals.json'
WORKS_FILE  = DATA_DIR / 'what_works.json'
POST_LOG    = DATA_DIR / 'posted.json'
SENT_LOG    = DATA_DIR / 'all_sent.json'

GH_TOKEN  = os.environ.get('GITHUB_TOKEN', '')
GH_USER   = os.environ.get('GITHUB_REPOSITORY_OWNER', 'meekotharaccoon-cell')
MASTO_TOKEN  = os.environ.get('MASTODON_TOKEN', '')
MASTO_SERVER = os.environ.get('MASTODON_SERVER', 'https://mastodon.social')
GUMROAD_TOKEN = os.environ.get('GUMROAD_TOKEN', '')

PAGES_REPOS = [
    'meeko-nerve-center',
    'gaza-rose-gallery',
    'solarpunk-learn',
    'solarpunk-market',
    'solarpunk-mutual-aid',
]

def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

def gh_get(endpoint):
    url = f'https://api.github.com{endpoint}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {GH_TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}

def fetch_pages_traffic():
    """GitHub Pages traffic: views + unique visitors per repo."""
    traffic = {}
    for repo in PAGES_REPOS:
        views = gh_get(f'/repos/{GH_USER}/{repo}/traffic/views')
        clones = gh_get(f'/repos/{GH_USER}/{repo}/traffic/clones')
        referrers = gh_get(f'/repos/{GH_USER}/{repo}/traffic/popular/referrers')
        paths = gh_get(f'/repos/{GH_USER}/{repo}/traffic/popular/paths')
        traffic[repo] = {
            'views_14d': views.get('count', 0),
            'unique_visitors_14d': views.get('uniques', 0),
            'clones_14d': clones.get('count', 0),
            'top_referrers': referrers[:5] if isinstance(referrers, list) else [],
            'top_paths': paths[:5] if isinstance(paths, list) else [],
            'daily_views': views.get('views', []),
        }
        print(f'  [{repo}] {traffic[repo]["views_14d"]} views, {traffic[repo]["unique_visitors_14d"]} unique')
    return traffic

def fetch_mastodon_engagement():
    """Pull our recent toots and get favorites/boosts per post."""
    if not MASTODON_TOKEN: return []
    try:
        req = urllib.request.Request(
            f"{MASTODON_SERVER.rstrip('/')}/api/v1/accounts/verify_credentials"
        )
        req.add_header('Authorization', f'Bearer {MASTODON_TOKEN}')
        with urllib.request.urlopen(req, timeout=15) as r:
            account = json.loads(r.read())
        account_id = account['id']

        req = urllib.request.Request(
            f"{MASTODON_SERVER.rstrip('/')}/api/v1/accounts/{account_id}/statuses?limit=20"
        )
        req.add_header('Authorization', f'Bearer {MASTODON_TOKEN}')
        with urllib.request.urlopen(req, timeout=15) as r:
            statuses = json.loads(r.read())

        return [{
            'id': s['id'],
            'created_at': s['created_at'],
            'text': s['content'][:80],
            'favourites': s.get('favourites_count', 0),
            'reblogs': s.get('reblogs_count', 0),
            'replies': s.get('replies_count', 0),
            'engagement': s.get('favourites_count', 0) + s.get('reblogs_count', 0) * 3,
        } for s in statuses]
    except Exception as e:
        print(f'  [mastodon] Error: {e}')
        return []

def fetch_gumroad_sales_by_date():
    """Sales per day for the last 30 days."""
    if not GUMROAD_TOKEN: return {}
    try:
        req = urllib.request.Request('https://api.gumroad.com/v2/sales')
        req.add_header('Authorization', f'Bearer {GUMROAD_TOKEN}')
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        sales = data.get('sales', [])
        by_date = {}
        for sale in sales:
            date = sale.get('created_at', '')[:10]
            if date:
                by_date[date] = by_date.get(date, 0) + 1
        return by_date
    except Exception as e:
        print(f'  [gumroad] Error: {e}')
        return {}

def correlate_posts_to_sales(post_log, sales_by_date):
    """
    Cross-reference: when a post went out vs. when sales happened.
    If sales spike the day after a post type, that post type works.
    This is correlation not causation, but it's the best signal we have.
    """
    correlations = {}
    for post_id, post_data in post_log.items():
        posted_dates = []
        for platform_post in post_data.get('platforms', []):
            # Get date from last_posted field
            date = post_data.get('first_posted', '')[:10]
            if date:
                posted_dates.append(date)

        if not posted_dates:
            continue

        # Sales on post day + next 2 days
        post_date = posted_dates[0] if posted_dates else ''
        if not post_date:
            continue

        try:
            pd = datetime.fromisoformat(post_date)
            window_sales = sum(
                sales_by_date.get((pd + timedelta(days=d)).strftime('%Y-%m-%d'), 0)
                for d in range(3)
            )
            correlations[post_id] = {
                'post_date': post_date,
                'window_sales': window_sales,
                'text_preview': post_data.get('text', '')[:60],
            }
        except:
            pass

    return correlations

def analyze_email_performance():
    """From sent log: which email types get replies vs. silence."""
    sent = load(SENT_LOG)
    if not sent:
        return {}

    by_type = {}
    for entry in sent.get('sent', []) if isinstance(sent, dict) else []:
        mode = entry.get('mode', 'unknown')
        replied = entry.get('replied', False)
        if mode not in by_type:
            by_type[mode] = {'sent': 0, 'replied': 0}
        by_type[mode]['sent'] += 1
        if replied:
            by_type[mode]['replied'] += 1

    # Calculate reply rates
    for mode, data in by_type.items():
        data['reply_rate'] = round(
            data['replied'] / data['sent'] * 100, 1
        ) if data['sent'] > 0 else 0

    return by_type

def generate_what_works_report(traffic, mastodon_posts, correlations, email_perf):
    """The actual insight: what's driving results."""
    report = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'summary': {},
        'traffic': {},
        'top_posts': [],
        'email': email_perf,
        'recommendations': [],
    }

    # Traffic winners
    if traffic:
        sorted_repos = sorted(
            traffic.items(),
            key=lambda x: x[1].get('unique_visitors_14d', 0),
            reverse=True
        )
        report['traffic'] = {
            'winner': sorted_repos[0][0] if sorted_repos else None,
            'total_views_14d': sum(v.get('views_14d', 0) for _, v in traffic.items()),
            'total_unique_14d': sum(v.get('unique_visitors_14d', 0) for _, v in traffic.items()),
            'by_repo': {k: {
                'views': v.get('views_14d', 0),
                'unique': v.get('unique_visitors_14d', 0)
            } for k, v in traffic.items()}
        }

    # Top Mastodon posts by engagement
    if mastodon_posts:
        top = sorted(mastodon_posts, key=lambda x: x.get('engagement', 0), reverse=True)[:3]
        report['top_posts'] = top

    # Recommendations
    recs = []
    if report['traffic'].get('winner'):
        recs.append(f"Drive more traffic to {report['traffic']['winner']} — it\'s your top performer")
    if mastodon_posts:
        top_post = sorted(mastodon_posts, key=lambda x: x['engagement'], reverse=True)
        if top_post:
            recs.append(f"Top Mastodon content type: '{top_post[0]['text'][:50]}...' — post more like this")
    if email_perf:
        best_mode = max(email_perf.items(), key=lambda x: x[1].get('reply_rate', 0), default=(None, {}))
        if best_mode[0]:
            recs.append(f"Best email mode: '{best_mode[0]}' ({best_mode[1].get('reply_rate', 0)}% reply rate) — increase frequency")

    report['recommendations'] = recs
    report['summary'] = {
        'total_14d_views': report['traffic'].get('total_views_14d', 0),
        'total_14d_unique': report['traffic'].get('total_unique_14d', 0),
        'top_mastodon_engagement': mastodon_posts[0]['engagement'] if mastodon_posts else 0,
        'recommendation_count': len(recs),
    }

    return report

def run():
    print('\n' + '='*52)
    print('  SIGNAL TRACKER — What\'s Actually Working')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    signals = load(SIGNAL_FILE)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Pull all signals
    print('\n  [traffic] Pulling GitHub Pages traffic...')
    traffic = fetch_pages_traffic() if GH_TOKEN else {}

    print('\n  [mastodon] Pulling post engagement...')
    mastodon_posts = fetch_mastodon_engagement()
    if mastodon_posts:
        top = sorted(mastodon_posts, key=lambda x: x['engagement'], reverse=True)[0]
        print(f'  [mastodon] Top post: {top["engagement"]} engagement — {top["text"][:50]}')

    print('\n  [gumroad] Pulling sales by date...')
    sales_by_date = fetch_gumroad_sales_by_date()
    print(f'  [gumroad] Sales data: {len(sales_by_date)} days with sales')

    print('\n  [email] Analyzing reply rates...')
    email_perf = analyze_email_performance()

    print('\n  [correlate] Linking posts to sales...')
    post_log = load(POST_LOG)
    correlations = correlate_posts_to_sales(post_log, sales_by_date)

    # Build the what-works report
    what_works = generate_what_works_report(traffic, mastodon_posts, correlations, email_perf)

    # Save
    signals[today] = {
        'traffic': traffic,
        'mastodon_top3': mastodon_posts[:3] if mastodon_posts else [],
        'sales_by_date': sales_by_date,
        'email_performance': email_perf,
    }
    save(SIGNAL_FILE, signals)
    save(WORKS_FILE, what_works)

    # Print summary
    print('\n' + '='*52)
    print('  WHAT\'S WORKING:')
    s = what_works['summary']
    print(f'  Pages: {s["total_14d_views"]} views, {s["total_14d_unique"]} unique (14d)')
    print(f'  Top Mastodon engagement: {s["top_mastodon_engagement"]}')
    print('\n  RECOMMENDATIONS:')
    for r in what_works['recommendations']:
        print(f'  • {r}')
    print('='*52)

if __name__ == '__main__':
    run()
