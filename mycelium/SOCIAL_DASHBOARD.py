# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""SOCIAL_DASHBOARD.py — builds docs/social.html copy-paste board from social_queue.json
Zero external APIs. Runs every cycle. Gives Meeko one URL to copy-paste all queued posts.
No Twitter/Reddit credentials needed — just grab the text and post manually.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

def load_queue():
    f = DATA / "social_queue.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"queue": [], "posts": []}

def card(platform, text, url=None, sent=False):
    icon = {"twitter": "🐦", "reddit": "🟠", "linkedin": "💼"}.get(platform, "📋")
    status_badge = '<span style="color:#888;font-size:11px">✓ sent</span>' if sent else '<span style="color:#4caf50;font-size:11px;font-weight:bold">● ready</span>'
    link_html = f'<div style="font-size:11px;color:#888;margin-top:4px">🔗 {url}</div>' if url else ""
    # Escape for HTML
    safe_text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
    return f"""
<div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:8px 0;position:relative">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="font-weight:bold;font-size:13px">{icon} {platform.upper()}</span>
    {status_badge}
  </div>
  <pre style="white-space:pre-wrap;font-family:monospace;font-size:12px;color:#e0e0e0;margin:0;background:#111;padding:10px;border-radius:4px;cursor:pointer" onclick="navigator.clipboard.writeText(this.innerText).then(()=>this.style.border='1px solid #4caf50')" title="Click to copy">{safe_text}</pre>
  {link_html}
</div>"""

def build_html(queue_data):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Collect all posts
    art_posts = []   # from queue[].tweets/reddit
    biz_posts = []   # from posts[]

    for item in queue_data.get("queue", []):
        piece = item.get("piece", "?")
        for tw in item.get("tweets", []):
            sent = tw.get("result", {}).get("status") in ("sent", "ok")
            art_posts.append(("twitter", tw["text"], None, sent, piece))
        for rd in item.get("reddit", []):
            sent = rd.get("result", {}).get("status") in ("sent", "ok")
            post = rd.get("post", {})
            art_posts.append(("reddit", f"r/{post.get('subreddit','?')}\n\nTITLE: {post.get('title','')}\n\n{post.get('text','')}", None, sent, piece))

    for p in queue_data.get("posts", []):
        sent = p.get("sent", False) and p.get("send_result", {}).get("success", False)
        biz_posts.append((p["platform"], p["text"], p.get("live_url"), sent, p.get("niche","?")))

    total_ready = sum(1 for *_, sent, _ in art_posts + biz_posts if not sent)
    total_sent = sum(1 for *_, sent, _ in art_posts + biz_posts if sent)

    # Group biz posts by niche
    niches = {}
    for platform, text, url, sent, niche in biz_posts:
        niches.setdefault(niche, []).append((platform, text, url, sent))

    # Group art posts by piece
    pieces = {}
    for platform, text, url, sent, piece in art_posts:
        pieces.setdefault(piece, []).append((platform, text, url, sent))

    niche_sections = ""
    for niche, posts in niches.items():
        cards = "".join(card(p, t, u, s) for p, t, u, s in posts)
        niche_sections += f'<h3 style="color:#81c784;margin:24px 0 8px">💼 {niche}</h3>{cards}'

    art_sections = ""
    for piece, posts in pieces.items():
        cards = "".join(card(p, t, u, s) for p, t, u, s in posts)
        art_sections += f'<h3 style="color:#ce93d8;margin:24px 0 8px">🎨 {piece}</h3>{cards}'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Social Queue</title>
<style>
  body{{background:#0d0d1a;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:860px;margin:0 auto;padding:20px}}
  h1{{color:#81c784;margin-bottom:4px}}
  h2{{color:#90caf9;border-bottom:1px solid #333;padding-bottom:8px}}
  .stat{{display:inline-block;background:#1a1a2e;border:1px solid #333;border-radius:6px;padding:8px 16px;margin:4px;text-align:center}}
  .stat .num{{font-size:24px;font-weight:bold;color:#81c784}}
  .stat .lbl{{font-size:11px;color:#888}}
  .tip{{background:#1a2a1a;border:1px solid #4caf5066;border-radius:6px;padding:12px;margin:16px 0;font-size:13px;color:#a5d6a7}}
</style>
</head>
<body>
<h1>⚡ SolarPunk Social Queue</h1>
<p style="color:#888;font-size:13px">Updated: {now} — Click any post to copy it to clipboard</p>

<div style="margin:16px 0">
  <div class="stat"><div class="num">{total_ready}</div><div class="lbl">ready to post</div></div>
  <div class="stat"><div class="num">{total_sent}</div><div class="lbl">sent</div></div>
  <div class="stat"><div class="num">{len(niches)}</div><div class="lbl">products</div></div>
  <div class="stat"><div class="num">{len(pieces)}</div><div class="lbl">art pieces</div></div>
</div>

<div class="tip">
  💡 <strong>Click any post to copy.</strong> Then paste directly into Twitter, Reddit, or LinkedIn.
  Once you add API credentials, SOCIAL_PROMOTER posts these automatically.
</div>

<h2>🛍️ Product Launches</h2>
{niche_sections or '<p style="color:#666">No product posts yet</p>'}

<h2>🎨 Gaza Rose Art Posts</h2>
{art_sections or '<p style="color:#666">No art posts yet</p>'}

<p style="color:#444;font-size:11px;margin-top:40px">
  Generated by SOCIAL_DASHBOARD engine · SolarPunk autonomous system<br>
  GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center
</p>
</body>
</html>"""

def run():
    print("SOCIAL_DASHBOARD building copy-paste board...")
    data = load_queue()

    html = build_html(data)
    (DOCS / "social.html").write_text(html)

    total = len(data.get("queue",[])) * 4 + len(data.get("posts",[]))
    print(f"  ✅ docs/social.html built — {total} posts ready to copy")
    print(f"  🌐 https://meekotharaccoon-cell.github.io/meeko-nerve-center/social.html")
    return {"status": "ok", "posts": total}

if __name__ == "__main__": run()
