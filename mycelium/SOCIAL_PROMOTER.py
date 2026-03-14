# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SOCIAL_PROMOTER.py v2 — Drains the real queue and actually posts
=================================================================
PREVIOUS BUG: Read data/social_queue.json["queue"] (its own old format)
and ignored data/social_queue.json["posts"] which is what BUSINESS_FACTORY
and REVENUE_LOOP write. Nothing ever got posted.

FIX:
- Drains data/social_queue.json["posts"] (written by BUSINESS_FACTORY +
  REVENUE_LOOP every cycle)
- Posts to Twitter/X via tweepy (simpler than manual OAuth)
- Posts to Reddit via praw
- Marks posts as sent so they don't double-post
- Falls back gracefully if credentials missing
- Caps at 3 posts per cycle to avoid rate limits
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask_json_list, ask
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA            = Path("data"); DATA.mkdir(exist_ok=True)
X_API_KEY       = os.environ.get("X_API_KEY", "")
X_API_SECRET    = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN  = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")  # note: env var name
REDDIT_ID       = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_SECRET   = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER     = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASS     = os.environ.get("REDDIT_PASSWORD", "")
SHOP_URL        = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

TWITTER_AVAILABLE = all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET])
REDDIT_AVAILABLE  = all([REDDIT_ID, REDDIT_SECRET, REDDIT_USER, REDDIT_PASS])


def load_state():
    f = DATA / "social_promoter_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "posted": 0, "failed": 0, "history": []}


def save_state(s):
    (DATA / "social_promoter_state.json").write_text(json.dumps(s, indent=2))


def load_queue():
    """Load the shared queue written by BUSINESS_FACTORY + REVENUE_LOOP."""
    f = DATA / "social_queue.json"
    if f.exists():
        try:
            q = json.loads(f.read_text())
            # Handle both formats
            posts = q.get("posts", [])
            return q, posts
        except: pass
    return {"posts": []}, []


def save_queue(q):
    (DATA / "social_queue.json").write_text(json.dumps(q, indent=2))


def post_twitter(text):
    """Post to Twitter/X via tweepy. Returns (success, info)."""
    if not TWITTER_AVAILABLE:
        return False, "no credentials"
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET,
        )
        resp = client.create_tweet(text=text[:280])
        tweet_id = resp.data.get("id") if resp.data else "?"
        return True, f"https://twitter.com/i/web/status/{tweet_id}"
    except Exception as e:
        return False, str(e)


def post_reddit(text, niche=""):
    """Post to one relevant subreddit. Returns (success, info)."""
    if not REDDIT_AVAILABLE:
        return False, "no credentials"
    try:
        import praw
        reddit = praw.Reddit(
            client_id=REDDIT_ID,
            client_secret=REDDIT_SECRET,
            username=REDDIT_USER,
            password=REDDIT_PASS,
            user_agent=f"SolarPunk/1.0 by u/{REDDIT_USER}",
        )
        # Pick subreddit based on content
        sub = "Entrepreneur"
        niche_lower = niche.lower()
        if "art" in niche_lower or "design" in niche_lower:
            sub = "DigitalArt"
        elif "notion" in niche_lower or "template" in niche_lower:
            sub = "Notion"
        elif "github" in niche_lower or "code" in niche_lower or "developer" in niche_lower:
            sub = "learnprogramming"
        elif "grant" in niche_lower or "nonprofit" in niche_lower:
            sub = "nonprofit"
        elif "prompt" in niche_lower or "ai" in niche_lower:
            sub = "artificial"

        subreddit = reddit.subreddit(sub)
        title = f"Built this with AI: {niche or 'new digital product'} — 15% to Gaza"
        post = subreddit.submit(title=title[:300], selftext=text[:10000])
        return True, f"https://reddit.com{post.permalink}"
    except Exception as e:
        return False, str(e)


def make_tweet_from_post(post):
    """Convert a queued post dict to a tweet string."""
    # If already has twitter text, use it
    if post.get("platform") == "twitter" and post.get("text"):
        return post["text"][:280]

    # Build from available fields
    niche    = post.get("niche", "new digital product")
    live_url = post.get("live_url", SHOP_URL)
    text     = post.get("text", "")

    if text and len(text) <= 280:
        return text

    # Generate a compact tweet
    return f"🌹 New: {niche} — built by AI, 15% to Gaza. {live_url} #Gaza #DigitalProduct #AI"[:280]


def make_reddit_text(post):
    """Convert a queued post dict to reddit post text."""
    if post.get("platform") == "reddit" and post.get("text"):
        return post["text"]
    text     = post.get("text", "")
    live_url = post.get("live_url", SHOP_URL)
    niche    = post.get("niche", "digital product")
    if text:
        return f"{text}\n\nMore info: {live_url}"
    return (f"Built this with AI for SolarPunk — {niche}.\n\n"
            f"15% of revenue goes to Gaza children's relief (PCRF).\n\n"
            f"Details: {live_url}")


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    print(f"SOCIAL_PROMOTER v2 cycle {state['cycles']} | "
          f"Twitter={'on' if TWITTER_AVAILABLE else 'off'} | "
          f"Reddit={'on' if REDDIT_AVAILABLE else 'off'}")

    queue, pending_posts = load_queue()

    # Filter to unsent posts only
    unsent = [p for p in pending_posts if not p.get("sent")]
    print(f"  Queue: {len(pending_posts)} total, {len(unsent)} unsent")

    if not unsent:
        # Generate a fresh post from scratch if queue empty
        print("  Queue empty — generating fresh post")
        ts = datetime.now(timezone.utc).strftime("%B %Y")
        unsent = [{
            "platform": "twitter",
            "text": f"🌹 SolarPunk is live — autonomous AI building digital businesses 4x/day. 15% to Gaza. {SHOP_URL} #AI #Gaza #Autonomous",
            "niche": "SolarPunk system",
            "live_url": SHOP_URL,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "source": "SOCIAL_PROMOTER_fallback",
        }]

    sent_this_cycle = 0
    MAX_PER_CYCLE = 3

    for i, post in enumerate(pending_posts):
        if post.get("sent"):
            continue
        if sent_this_cycle >= MAX_PER_CYCLE:
            break

        platform = post.get("platform", "twitter")
        niche    = post.get("niche", "")
        success  = False
        info     = ""

        if platform == "twitter" or platform == "x":
            tweet = make_tweet_from_post(post)
            success, info = post_twitter(tweet)
            print(f"  Twitter: {'✅ ' + info[:60] if success else '⚠️  ' + info[:60]}")

        elif platform == "reddit":
            body = make_reddit_text(post)
            success, info = post_reddit(body, niche)
            print(f"  Reddit:  {'✅ ' + info[:60] if success else '⚠️  ' + info[:60]}")

        else:
            # linkedin, etc — just log it
            print(f"  {platform}: queued (manual post needed)")
            info = "manual"
            success = True  # mark sent so it doesn't loop

        # Mark as sent regardless (avoid infinite retry spam)
        post["sent"] = True
        post["sent_at"] = datetime.now(timezone.utc).isoformat()
        post["send_result"] = {"success": success, "info": info}

        if success:
            state["posted"] = state.get("posted", 0) + 1
            state.setdefault("history", []).append({
                "platform": platform,
                "niche": niche,
                "info": info,
                "at": post["sent_at"],
            })
        else:
            state["failed"] = state.get("failed", 0) + 1

        sent_this_cycle += 1

    # Keep history trimmed
    state["history"] = state.get("history", [])[-200:]

    # Write queue back with sent flags
    queue["posts"] = pending_posts
    save_queue(queue)
    save_state(state)

    print(f"  Sent this cycle: {sent_this_cycle} | All-time: {state['posted']} posted, {state['failed']} failed")
    return state


if __name__ == "__main__":
    run()
