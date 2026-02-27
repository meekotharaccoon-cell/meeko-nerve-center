#!/usr/bin/env python3
"""
Content Performance Engine
============================
The system posts every day but has never learned what resonates.
This ends that.

Every run:
  1. Fetches engagement stats from Mastodon and Bluesky for recent posts
  2. Scores each post: boosts + replies + favourites = resonance
  3. Identifies top performers and what they had in common
  4. Writes a performance report to data/content_performance.json
  5. Feeds top-performing patterns back into a strategy file
     that other engines (social, cross, video) can read
  6. If a post went viral (score > threshold), generates a follow-up

Result: the system learns its own voice by watching what lands.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()

HF_TOKEN          = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS     = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
MAST_TOKEN        = os.environ.get('MASTODON_TOKEN', '')
MAST_BASE_URL     = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
BLUESKY_HANDLE    = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_PASSWORD  = os.environ.get('BLUESKY_PASSWORD', '')

VIRAL_THRESHOLD   = 10   # combined score to trigger a follow-up
LOOKBACK_POSTS    = 40   # how many recent posts to analyze

# ── Fetch ───────────────────────────────────────────────────────────────────────

def fetch_json(url, headers=None, timeout=20):
    h = {'User-Agent': 'meeko-performance/1.0'}
    if headers: h.update(headers)
    try:
        req = urllib_request.Request(url, headers=h)
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[perf] Fetch error {url[:60]}: {e}')
        return None

def fetch_mastodon_stats():
    """
    Fetch recent toots and their engagement stats.
    Returns list of {id, text, score, favourites, boosts, replies, date}
    """
    if not MAST_TOKEN:
        print('[perf] No Mastodon token')
        return []

    # Get account ID first
    account = fetch_json(
        f'{MAST_BASE_URL}/api/v1/accounts/verify_credentials',
        headers={'Authorization': f'Bearer {MAST_TOKEN}'}
    )
    if not account:
        return []

    acct_id = account.get('id')
    statuses = fetch_json(
        f'{MAST_BASE_URL}/api/v1/accounts/{acct_id}/statuses?limit={LOOKBACK_POSTS}',
        headers={'Authorization': f'Bearer {MAST_TOKEN}'}
    )
    if not statuses or not isinstance(statuses, list):
        return []

    posts = []
    for s in statuses:
        fav    = s.get('favourites_count', 0)
        boost  = s.get('reblogs_count', 0)
        reply  = s.get('replies_count', 0)
        score  = fav + (boost * 2) + reply  # boosts weighted higher
        # Strip HTML from content
        text = s.get('content', '')
        text = text.replace('<p>', '').replace('</p>', ' ').replace('<br>', ' ')
        import re
        text = re.sub(r'<[^>]+>', '', text).strip()[:280]
        posts.append({
            'platform':   'mastodon',
            'id':         s.get('id'),
            'text':       text,
            'score':      score,
            'favourites': fav,
            'boosts':     boost,
            'replies':    reply,
            'date':       s.get('created_at', '')[:10],
            'url':        s.get('url', ''),
        })

    print(f'[perf] Mastodon: {len(posts)} posts fetched')
    return posts

def bluesky_login():
    if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
        return None
    try:
        payload = json.dumps({'identifier': BLUESKY_HANDLE, 'password': BLUESKY_PASSWORD}).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[perf] Bluesky login failed: {e}')
        return None

def fetch_bluesky_stats(session):
    """
    Fetch recent Bluesky posts and engagement.
    Returns list of post dicts.
    """
    if not session: return []
    try:
        handle = session.get('handle', BLUESKY_HANDLE)
        token  = session.get('accessJwt', '')
        feed   = fetch_json(
            f'https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={handle}&limit={LOOKBACK_POSTS}',
            headers={'Authorization': f'Bearer {token}'}
        )
        if not feed or not feed.get('feed'):
            return []

        posts = []
        for item in feed['feed']:
            post   = item.get('post', {})
            record = post.get('record', {})
            counts = post.get('likeCount', 0), post.get('repostCount', 0), post.get('replyCount', 0)
            likes, reposts, replies = counts
            score = likes + (reposts * 2) + replies
            text  = record.get('text', '')[:280]
            posts.append({
                'platform': 'bluesky',
                'id':       post.get('cid', ''),
                'text':     text,
                'score':    score,
                'likes':    likes,
                'reposts':  reposts,
                'replies':  replies,
                'date':     record.get('createdAt', '')[:10],
                'url':      f'https://bsky.app/profile/{handle}',
            })
        print(f'[perf] Bluesky: {len(posts)} posts fetched')
        return posts
    except Exception as e:
        print(f'[perf] Bluesky stats error: {e}')
        return []

# ── Analysis ────────────────────────────────────────────────────────────────────

def ask_llm(prompt, max_tokens=800):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [
                {'role': 'system', 'content': 'You analyze social media content performance. Be specific and actionable.'},
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
    except Exception as e:
        print(f'[perf] LLM error: {e}')
        return None

def analyze_patterns(top_posts):
    """
    Ask LLM what the top posts have in common — what content patterns resonate.
    Returns a strategy dict.
    """
    post_summaries = '\n'.join(
        f'Score {p["score"]}: {p["text"][:200]}'
        for p in top_posts[:10]
    )
    prompt = f"""These are the highest-performing posts from a Palestinian solidarity + congressional accountability account:

{post_summaries}

Analyze what these posts have in common. Identify:
1. Tone patterns (urgent, hopeful, factual, emotional?)
2. Content patterns (data-heavy, personal, calls-to-action, questions?)
3. Length patterns (short punchy vs detailed?)
4. The one thing that makes people share this content

Respond as JSON only:
{{
  "tone": "dominant tone pattern",
  "content_type": "what kind of content performs best",
  "optimal_length": "short/medium/long and why",
  "resonance_factor": "the one thing that makes people engage",
  "avoid": "what to avoid based on low performers",
  "strategy_note": "one sentence instruction for the content engine"
}}
"""
    result = ask_llm(prompt)
    if not result: return {}
    try:
        start = result.find('{')
        end   = result.rfind('}') + 1
        return json.loads(result[start:end])
    except:
        return {}

# ── Follow-up generator ───────────────────────────────────────────────────────────

def generate_followup(viral_post):
    """If a post went viral, generate a follow-up post to keep the momentum."""
    prompt = f"""This post went viral on {viral_post['platform']} (score: {viral_post['score']}):

\"{viral_post['text']}\"

Write a follow-up post (max 280 chars) that:
- Thanks the community for the response
- Adds one new piece of information or action
- Keeps the same energy
- Includes a relevant hashtag

Just the post text. No quotes.
"""
    return ask_llm(prompt, max_tokens=200)

# ── Main ───────────────────────────────────────────────────────────────────

def run():
    print(f'\n[perf] Content Performance Engine — {TODAY}')

    all_posts = []

    # Mastodon
    mast_posts = fetch_mastodon_stats()
    all_posts.extend(mast_posts)

    # Bluesky
    bsky_session = bluesky_login()
    bsky_posts   = fetch_bluesky_stats(bsky_session)
    all_posts.extend(bsky_posts)

    if not all_posts:
        print('[perf] No posts fetched. Check API credentials.')
        return

    # Sort by score
    all_posts.sort(key=lambda p: p['score'], reverse=True)
    top_posts  = [p for p in all_posts if p['score'] > 0]
    viral_post = all_posts[0] if all_posts[0]['score'] >= VIRAL_THRESHOLD else None

    print(f'[perf] Total posts: {len(all_posts)} | With engagement: {len(top_posts)} | Viral: {bool(viral_post)}')

    # Analyze patterns
    strategy = {}
    if top_posts:
        print('[perf] Analyzing what resonates...')
        strategy = analyze_patterns(top_posts)
        if strategy:
            print(f'[perf] Strategy: {strategy.get("strategy_note","")}')

    # Build report
    report = {
        'date':          TODAY,
        'total_posts':   len(all_posts),
        'avg_score':     round(sum(p['score'] for p in all_posts) / max(len(all_posts),1), 2),
        'top_post':      all_posts[0] if all_posts else {},
        'top_10':        all_posts[:10],
        'strategy':      strategy,
        'viral_detected': bool(viral_post),
    }

    # Save report
    try:
        (DATA / 'content_performance.json').write_text(json.dumps(report, indent=2))
        print('[perf] Performance report saved')
    except Exception as e:
        print(f'[perf] Save error: {e}')

    # Save strategy for other engines to consume
    if strategy:
        try:
            (DATA / 'content_strategy.json').write_text(json.dumps({
                'updated':  TODAY,
                'strategy': strategy,
                'top_examples': [p['text'] for p in all_posts[:3]],
            }, indent=2))
            print('[perf] Strategy file updated for other engines')
        except Exception as e:
            print(f'[perf] Strategy save error: {e}')

    # Generate follow-up if something went viral
    if viral_post:
        followup = generate_followup(viral_post)
        if followup:
            queue_dir = ROOT / 'content' / 'queue'
            queue_dir.mkdir(parents=True, exist_ok=True)
            try:
                (queue_dir / f'viral_followup_{TODAY}.json').write_text(
                    json.dumps([{'platform': 'all', 'type': 'viral_followup', 'text': followup}], indent=2)
                )
                print(f'[perf] Viral follow-up queued: {followup[:80]}')
            except Exception as e:
                print(f'[perf] Queue write error: {e}')

    print(f'[perf] Done. Avg score: {report["avg_score"]} | Top: {all_posts[0]["score"] if all_posts else 0}')

if __name__ == '__main__':
    run()
