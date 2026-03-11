#!/usr/bin/env python3
"""
AGENT_GUMROAD_BUILDER.py — Nano-agent that generates + updates Gumroad listings
================================================================================
Runs every cycle. Generates fresh Gumroad copy, updates data/gumroad_listings.txt,
and writes a docs/store.html update. Uses Claude if available, templates otherwise.
"""
import sys, os, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from NANO_AGENT import NanoAgent, DATA, DOCS
from datetime import datetime, timezone

PRODUCTS = [
    {
        "id": "solarpunk-system",
        "name": "SolarPunk — Fork Your Own Autonomous AI Revenue System",
        "price": 17,
        "url": "https://meekotharacoon.gumroad.com/l/solarpunk",
        "tagline": "76 engines. 4x/day. Self-building. 15% hardcoded to Gaza.",
        "category": "software",
    },
    {
        "id": "ai-prompt-packs",
        "name": "500+ Battle-Tested AI Prompts for Builders & Earners",
        "price": 9,
        "url": "https://meekotharacoon.gumroad.com/l/ai-prompts",
        "tagline": "The prompts that built an autonomous AI business.",
        "category": "prompts",
    },
    {
        "id": "github-actions-guide",
        "name": "GitHub Actions for Beginners — Free Automation That Actually Works",
        "price": 7,
        "url": "https://meekotharacoon.gumroad.com/l/github-actions",
        "tagline": "Run Python, deploy sites, send emails — all free.",
        "category": "guide",
    },
    {
        "id": "palestine-art-pack",
        "name": "Palestine Solidarity Art Pack — 12 AI Prints",
        "price": 5,
        "url": "https://meekotharacoon.gumroad.com/l/palestine-art",
        "tagline": "70% to Palestinian artists. Print-ready. Instant download.",
        "category": "art",
    },
    {
        "id": "autonomous-business-guide",
        "name": "Build an Autonomous Business in 30 Days",
        "price": 12,
        "url": "https://meekotharacoon.gumroad.com/l/autonomous-biz",
        "tagline": "No code. No team. No investors. Real blueprint.",
        "category": "guide",
    },
]

STORE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Store — AI Products for Palestine</title>
<meta name="description" content="Digital products built by autonomous AI. 15% of every sale to Palestinian children.">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c10;color:#dde;font-family:-apple-system,BlinkMacSystemFont,sans-serif}}
.hero{{padding:60px 20px 40px;text-align:center;background:linear-gradient(135deg,#080c10,#0d1a0a)}}
h1{{font-size:clamp(1.8rem,5vw,3rem);font-weight:900;color:#00ff88;margin-bottom:12px}}
.sub{{color:rgba(255,255,255,.45);margin-bottom:20px}}
.pill{{display:inline-block;background:rgba(255,45,107,.1);border:1px solid rgba(255,45,107,.3);border-radius:20px;padding:6px 16px;color:#ff2d6b;font-size:.8rem}}
.grid{{max-width:960px;margin:0 auto;padding:40px 20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}}
.card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:24px;display:flex;flex-direction:column;gap:12px}}
.card-name{{font-size:1rem;font-weight:700;color:#fff;line-height:1.4}}
.card-tag{{font-size:.8rem;color:rgba(255,255,255,.4);line-height:1.5}}
.card-price{{font-size:1.8rem;font-weight:900;color:#00ff88}}
.card-btn{{display:block;background:#00ff88;color:#080c10;font-weight:800;text-align:center;padding:12px;border-radius:8px;text-decoration:none;font-size:.9rem;margin-top:auto}}
.card-btn:hover{{background:#00e67a}}
.gaza{{text-align:center;padding:40px 20px;color:rgba(255,255,255,.35);font-size:.8rem;border-top:1px solid rgba(255,255,255,.05)}}
.gaza a{{color:#ff2d6b;text-decoration:none}}
footer{{text-align:center;padding:24px;color:rgba(255,255,255,.2);font-size:.75rem}}
footer a{{color:#00ff88;text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <h1>SolarPunk Store</h1>
  <p class="sub">Digital products built by autonomous AI — 4x/day, every day</p>
  <span class="pill">🌹 15% of every sale → Palestinian children via PCRF</span>
</div>
<div class="grid">
{CARDS}
</div>
<div class="gaza">
  <strong style="color:#ff2d6b">15% of every purchase</strong> goes to <a href="https://www.pcrf.net" target="_blank">PCRF</a> — Palestinian Children's Relief Fund<br>
  EIN: 93-1057665 · 4-star Charity Navigator · <a href="https://www.charitynavigator.org/ein/931057665" target="_blank">Verify →</a>
</div>
<footer>
  Built by <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center">SolarPunk</a> ·
  Updated {TS} ·
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Fork on GitHub</a>
</footer>
</body>
</html>"""

CARD_TEMPLATE = """  <div class="card">
    <div class="card-name">{name}</div>
    <div class="card-tag">{tagline}</div>
    <div class="card-price">${price}</div>
    <a class="card-btn" href="{url}" target="_blank">Get Instant Access →</a>
  </div>"""


class AGENT_GUMROAD_BUILDER(NanoAgent):
    def run(self):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        cards = "\n".join(
            CARD_TEMPLATE.format(**p) for p in PRODUCTS
        )
        html = STORE_HTML_TEMPLATE.replace("{CARDS}", cards).replace("{TS}", ts)
        self.write_html("store.html", html)

        # Also write a machine-readable product catalog
        catalog = {
            "generated": ts,
            "products": PRODUCTS,
            "total_products": len(PRODUCTS),
            "note": "Full copy-paste listings in data/gumroad_listings.txt",
        }
        self.save_data("gumroad_catalog.json", catalog)

        return {
            "status": "ok",
            "summary": f"Rebuilt store.html with {len(PRODUCTS)} products",
            "products_count": len(PRODUCTS),
        }

if __name__ == "__main__":
    AGENT_GUMROAD_BUILDER("AGENT_GUMROAD_BUILDER").execute()
