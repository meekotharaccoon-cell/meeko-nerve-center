#!/usr/bin/env python3
"""
SOCIAL_PROMOTER.py — Traffic Engine for Gaza Rose Gallery
Generates ready-to-post social content every cycle.
Auto-posts to Twitter/X if X_API_KEY + X_API_SECRET + X_ACCESS_TOKEN + X_ACCESS_SECRET are set.
Always saves drafts to data/social_queue.json for manual posting.

SolarPunk insight: The gap is distribution. Art exists. World doesn't know yet.
"""
import os, json, requests, hashlib
from pathlib import Path
from datetime import datetime, timezone

API_KEY          = os.environ.get("ANTHROPIC_API_KEY", "")
X_API_KEY        = os.environ.get("X_API_KEY", "")
X_API_SECRET     = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN   = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET  = os.environ.get("X_ACCESS_SECRET", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_SECRET    = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER      = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASS      = os.environ.get("REDDIT_PASSWORD", "")
SHOP_URL         = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
DATA             = Path("data")
DATA.mkdir(exist_ok=True)

ART_PIECES = [
    {"title": "Desert Rose at Dawn",               "emoji": "🌹", "theme": "hope"},
    {"title": "White Doves Over the Mediterranean","emoji": "🕊️", "theme": "peace"},
    {"title": "Olive Grove Eternal",               "emoji": "🌿", "theme": "roots"},
    {"title": "Tatreez Pattern Bloom",             "emoji": "🌸", "theme": "culture"},
    {"title": "Gaza Coastline at Golden Hour",     "emoji": "🌅", "theme": "home"},
    {"title": "Star of Hope Rising",               "emoji": "⭐", "theme": "resilience"},
    {"title": "Pomegranate Season",                "emoji": "🍎", "theme": "abundance"},
    {"title": "Night Garden in Ruins",             "emoji": "🌙", "theme": "memory"},
    {"title": "Child with Balloon",                "emoji": "🎈", "theme": "childhood"},
    {"title": "The Return — Sunflower Field",      "emoji": "🌻", "theme": "return"},
    {"title": "Grandmother's Embroidery",          "emoji": "🧵", "theme": "lineage"},
    {"title": "Sea Glass and Rubble",              "emoji": "💧", "theme": "survival"},
]

TWEET_TEMPLATES = [
    """{emoji} NEW: "{title}"

$1 AI art print.
70¢ → Gaza Rose Gallery (Palestinian artists)
30¢ → loop fund → buys the next piece automatically

The loop feeds itself 🔄

{url}

#GazaRose #PalestineArt #DigitalArt #SocialImpact""",

    """Every purchase loops.

{emoji} "{title}" — $1

→ 70% to Gaza Rose Gallery
→ 30% pools until it auto-buys another piece
→ That piece donates 70% too
→ Forever

One dollar. Infinite echoes.

{url}

#Palestine #ArtForGood #GazaRose""",

    """{emoji} Art that doesn't stop giving.

"{title}" — only $1

After 4 purchases, the system buys itself a new piece.
Gaza Rose Gallery gets 70¢ every single time.

This is SolarPunk economics.

{url}

#DigitalArt #Palestine #GazaRose #AIArt""",

    """This is different.

{emoji} "{title}" — $1
└ 70¢ → Palestinian artist support (instant)
└ 30¢ → auto-reinvestment pool
   └ When pool hits $1 → auto-buys another piece
      └ 70¢ to Gaza Rose Gallery
         └ and it loops again

Your $1 never stops.

{url}

#GazaRose #SolarPunk #Palestine""",

    """What if art bought itself?

{emoji} "{title}"
$1 — instant digital download

The SolarPunk Loop:
[Human pays $1] → [70¢ to Gaza] → [30¢ pools]
[Pool hits $1] → [auto-purchase] → [70¢ to Gaza]
[repeat forever]

{url}

#AIArt #GazaRose #DigitalArt #Palestine""",
]

REDDIT_POSTS = [
    {
        "subreddit": "DigitalArt",
        "title": "[OC] Gaza Rose Gallery — AI art prints where 70% of every sale goes to Palestinian artist relief",
        "text": """I built a small shop where every $1 purchase of AI-generated art automatically splits:

- **70¢ → Gaza Rose Gallery** (Palestinian artists & community relief)
- **30¢ → Loop Fund** (pools until $1, then auto-buys another piece)

The loop part is what makes it interesting: the system becomes its own customer. After ~4 human sales, the fund auto-purchases a new piece, which donates 70¢ to Gaza Rose, which adds 30¢ back to the pool... it compounds indefinitely.

Piece this week: **{title}** — {theme} themed, AI-generated, instant download.

Shop: {url}

All art is $1. All art is instant download. All art echoes.

*Built with SolarPunk autonomous systems — GitHub Actions + Claude API*"""
    },
    {
        "subreddit": "Palestine",
        "title": "$1 AI art that auto-donates 70% to Gaza Rose Gallery — the other 30% auto-buys the next piece",
        "text": """I wanted to find a way to support Palestinian artists that compounds instead of depleting.

**How it works:**
1. You buy a $1 digital art print (instant download)
2. 70¢ goes directly to Gaza Rose Gallery
3. 30¢ goes into a loop fund
4. When the loop fund hits $1.00, it auto-purchases another piece
5. That purchase donates another 70¢ to Gaza Rose Gallery
6. And adds 30¢ back to the fund...

It never stops. Your $1 echoes indefinitely.

Current piece: **{title}** — download immediately after purchase.

{url}

For Palestine. 🇵🇸"""
    },
]

def pick_piece(cycle_num):
    return ART_PIECES[cycle_num % len(ART_PIECES)]

def generate_with_claude(piece):
    if not API_KEY:
        return None
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 600,
                  "messages": [{"role": "user", "content": f"""Write 3 viral tweets promoting this $1 art piece.
Art: "{piece['title']}" — theme: {piece['theme']}
Shop URL: {SHOP_URL}
Rules: 280 chars max each. Mention 70% to Gaza Rose Gallery, $1 price, instant download.
One emotional, one analytical, one story. Use #GazaRose #Palestine #DigitalArt. Include {piece['emoji']}.
JSON only (no fences): {{"tweets": ["tweet1", "tweet2", "tweet3"]}}"""}]},
            timeout=25)
        if r.status_code == 200:
            t = r.json()["content"][0]["text"]
            s, e = t.find("{"), t.rfind("}") + 1
            return json.loads(t[s:e]) if s >= 0 else None
    except Exception as ex:
        print(f"Claude err: {ex}")
    return None

def build_tweets(piece, cycle_num):
    claude_result = generate_with_claude(piece)
    if claude_result and "tweets" in claude_result:
        return claude_result["tweets"]
    return [TWEET_TEMPLATES[(cycle_num + i) % len(TWEET_TEMPLATES)].format(
        emoji=piece["emoji"], title=piece["title"], theme=piece["theme"], url=SHOP_URL
    ) for i in range(3)]

def post_to_twitter(tweet_text):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        return {"status": "skipped", "reason": "no_credentials"}
    try:
        import hmac, base64, time, urllib.parse
        url = "https://api.twitter.com/2/tweets"
        ts = str(int(time.time()))
        nonce = hashlib.md5(ts.encode()).hexdigest()
        oauth_params = {
            "oauth_consumer_key": X_API_KEY, "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": ts,
            "oauth_token": X_ACCESS_TOKEN, "oauth_version": "1.0"
        }
        base = "POST&" + urllib.parse.quote(url, safe="") + "&" + \
               urllib.parse.quote("&".join(f"{k}={urllib.parse.quote(str(v), safe='')}"
               for k, v in sorted(oauth_params.items())), safe="")
        key = urllib.parse.quote(X_API_SECRET, safe="") + "&" + urllib.parse.quote(X_ACCESS_SECRET, safe="")
        sig = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
        oauth_params["oauth_signature"] = sig
        auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(str(v), safe="")}"'
                                           for k, v in sorted(oauth_params.items()))
        resp = requests.post(url,
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json={"text": tweet_text[:280]}, timeout=20)
        if resp.status_code in [200, 201]:
            return {"status": "posted", "tweet_id": resp.json().get("data", {}).get("id")}
        return {"status": "failed", "code": resp.status_code}
    except Exception as ex:
        return {"status": "error", "msg": str(ex)}

def run():
    queue_file = DATA / "social_queue.json"
    queue = json.loads(queue_file.read_text()) if queue_file.exists() else {"cycles": 0, "queue": []}
    cycle_num = queue.get("cycles", 0) + 1
    queue["cycles"] = cycle_num
    piece = pick_piece(cycle_num)
    print(f"SOCIAL_PROMOTER cycle {cycle_num} | Piece: {piece['title']}")
    tweets = build_tweets(piece, cycle_num)
    results = {"cycle": cycle_num, "piece": piece["title"],
               "ts": datetime.now(timezone.utc).isoformat(), "tweets": [], "reddit": []}
    for i, tweet in enumerate(tweets[:3]):
        if X_API_KEY:
            result = post_to_twitter(tweet)
            print(f"  Tweet {i+1}: {result['status']}")
        else:
            result = {"status": "queued"}
            print(f"  Tweet {i+1}: queued (set X_API_KEY to auto-post)")
        results["tweets"].append({"text": tweet, "result": result})
    for post in REDDIT_POSTS[:1]:
        rpost = {"subreddit": post["subreddit"], "title": post["title"],
                 "text": post["text"].format(title=piece["title"], theme=piece["theme"], url=SHOP_URL)}
        results["reddit"].append({"post": rpost, "result": {"status": "queued"}})
        print(f"  Reddit r/{post['subreddit']}: queued")
    queue.setdefault("queue", []).append(results)
    queue["queue"] = queue["queue"][-30:]
    queue_file.write_text(json.dumps(queue, indent=2))
    (DATA / "social_latest.json").write_text(json.dumps(results, indent=2))
    print(f"\n📋 COPY-PASTE READY TWEET:\n{'='*50}")
    print(tweets[0][:280])
    print(f"{'='*50}\nShop: {SHOP_URL}")
    return results

if __name__ == "__main__":
    run()
