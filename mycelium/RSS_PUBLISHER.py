#!/usr/bin/env python3
"""
RSS_PUBLISHER — publish RSS feed from newsletter archive + cycle history
FIX: newsletter_archive.json can be a dict or a list. Handle both.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
DOCS  = Path("docs"); DOCS.mkdir(exist_ok=True)
FEED  = DOCS / "feed.xml"
STATE = DATA / "rss_publisher_state.json"
BASE  = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"


def rj(path, fb=None):
    try: return json.loads(Path(path).read_text())
    except: return fb


def rfc822(iso_ts):
    try:
        from email.utils import format_datetime
        return format_datetime(datetime.fromisoformat(iso_ts.replace("Z", "+00:00")))
    except:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def build_items():
    items = []

    # FIX: archive.json can be a dict {"newsletters": [...]} or a raw list or empty dict
    raw = rj(DATA / "newsletter_archive.json", [])
    if isinstance(raw, dict):
        archive = raw.get("newsletters", [])
    elif isinstance(raw, list):
        archive = raw
    else:
        archive = []

    for entry in reversed(archive[-10:]):
        if not isinstance(entry, dict):
            continue
        items.append({
            "title": escape(entry.get("subject", "SolarPunk Update")),
            "link":  f"{BASE}/index.html",
            "desc":  escape(entry.get("body", "")[:500]),
            "pub":   rfc822(entry.get("ts", datetime.now(timezone.utc).isoformat())),
            "guid":  f"newsletter-{entry.get('ts', '')[:10]}",
        })

    hist = rj(DATA / "omnibus_history.json", [])
    if isinstance(hist, list):
        for cycle in reversed(hist[-5:]):
            if not isinstance(cycle, dict):
                continue
            health = cycle.get("health_after", 0)
            built  = cycle.get("engines_auto_built", [])
            ts     = cycle.get("completed", "")
            rev    = cycle.get("total_revenue", 0)
            title  = f"Cycle #{cycle.get('cycle_number','?')}: Health {health}/100"
            if built: title += f" — built {', '.join(built[:2])}"
            desc = (f"SolarPunk cycle. Health: {health}/100. Revenue: ${rev:.2f}. "
                    f"Engines built: {', '.join(built) if built else 'none'}. "
                    f"15% to PCRF (Palestinian relief).")
            items.append({
                "title": escape(title),
                "link":  f"{BASE}/status.html",
                "desc":  escape(desc),
                "pub":   rfc822(ts) if ts else rfc822(datetime.now(timezone.utc).isoformat()),
                "guid":  f"cycle-{cycle.get('cycle_number','0')}",
            })

    return items[:20]


def render_feed(items):
    now = rfc822(datetime.now(timezone.utc).isoformat())
    item_xml = ""
    for it in items:
        item_xml += f"""    <item>
      <title>{it['title']}</title>
      <link>{it['link']}</link>
      <description>{it['desc']}</description>
      <pubDate>{it['pub']}</pubDate>
      <guid isPermaLink="false">{it['guid']}</guid>
    </item>\n"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>SolarPunk — Autonomous AI Revenue System</title>
    <link>{BASE}</link>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml" />
    <description>Live updates from SolarPunk: autonomous AI building revenue for Palestinian relief.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <managingEditor>meekotharaccoon@gmail.com (Meeko)</managingEditor>
{item_xml}  </channel>
</rss>"""


def run():
    print("RSS_PUBLISHER starting...")
    items = build_items()
    FEED.write_text(render_feed(items), encoding="utf-8")
    print(f"  ✅ Published {len(items)} items → docs/feed.xml")
    print(f"  URL: {BASE}/feed.xml")

    idx = DOCS / "index.html"
    if idx.exists():
        html = idx.read_text()
        tag = f'<link rel="alternate" type="application/rss+xml" title="SolarPunk Feed" href="{BASE}/feed.xml" />'
        if tag not in html and "<head>" in html:
            html = html.replace("<head>", f"<head>\n  {tag}")
            idx.write_text(html)
            print("  ✅ RSS autodiscovery injected into index.html")

    STATE.write_text(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "items": len(items),
        "feed_url": f"{BASE}/feed.xml"
    }, indent=2))


if __name__ == "__main__":
    run()
