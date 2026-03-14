# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
ART_CATALOG.py — Gaza Rose Gallery engine
Builds docs/art.html and data/art_catalog.json.
The Ko-fi art fix: art.html shows all 7 prints with buy buttons.
Ko-fi shop items still need to be created manually (no Ko-fi API exists).
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

ART_PIECES = [
    {"id": "white-doves", "title": "White Doves Over Gaza", "emoji": "🕊️",
     "desc": "Seven white doves ascending through golden morning light over ancient olive groves. Peace, hope, and the indomitable spirit of Palestine.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#f8f4e8", "#7a9b5c"], "tags": ["peace", "doves", "hope"]},
    {"id": "olive-grove", "title": "Ancient Olive Grove", "emoji": "🫒",
     "desc": "Thousand-year-old olive trees standing resilient against the Mediterranean sky.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#6b8f47", "#d4e8b8"], "tags": ["olive", "resilience", "nature"]},
    {"id": "tatreez", "title": "Tatreez — Living Embroidery", "emoji": "🧵",
     "desc": "The geometric language of Palestinian women, woven across generations.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#c41e3a", "#f4f1de"], "tags": ["tatreez", "culture", "art"]},
    {"id": "gaza-coastline", "title": "Gaza by the Sea", "emoji": "🌊",
     "desc": "The Mediterranean at dusk, its waters catching the last gold of day.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#0077b6", "#f4a261"], "tags": ["sea", "Gaza", "sunset"]},
    {"id": "star-of-hope", "title": "Star of Hope", "emoji": "⭐",
     "desc": "A single brilliant star above the ancient cityscape, surrounded by the warm glow of windows.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#1a1a2e", "#ffd700"], "tags": ["star", "hope", "night"]},
    {"id": "pomegranate", "title": "Pomegranate Season", "emoji": "🍎",
     "desc": "Deep crimson pomegranates split open on a mosaic table, seeds gleaming like rubies.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#9b2335", "#f4c2c2"], "tags": ["pomegranate", "culture", "home"]},
    {"id": "night-garden", "title": "Night Garden of Palestine", "emoji": "🌙",
     "desc": "Jasmine and bougainvillea under a moon so full it turns night to silver.",
     "kofi_url": "https://ko-fi.com/meekotharaccoon/shop", "gumroad_url": "https://meekotharacoon.gumroad.com",
     "colors": ["#0d0d2b", "#7b2d8b"], "tags": ["garden", "night", "jasmine"]},
]


def build_art_html():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cards = ""
    for p in ART_PIECES:
        c1, c2 = p["colors"]
        tags = " ".join(f'<span class="tag">{t}</span>' for t in p["tags"])
        cards += f"""<div class="card">
  <div class="preview" style="background:linear-gradient(135deg,{c1},{c2})">
    <div class="emoji">{p["emoji"]}</div>
  </div>
  <div class="info">
    <h3>{p["title"]}</h3>
    <p>{p["desc"]}</p>
    <div class="tags">{tags}</div>
    <div class="footer">
      <span class="price">$1.00</span>
      <span class="split">70¢ → Gaza · 30¢ → Loop</span>
    </div>
    <div class="btns">
      <a href="{p["gumroad_url"]}" class="btn-g" target="_blank">🛒 Buy on Gumroad</a>
      <a href="{p["kofi_url"]}" class="btn-k" target="_blank">☕ Ko-fi Shop</a>
    </div>
  </div>
</div>\n"""

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gaza Rose Gallery — SolarPunk™</title>
<meta name="description" content="$1 AI art prints. 70¢ to Gaza via PCRF. Palestinian-themed digital art.">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060e;color:#dde;font-family:-apple-system,sans-serif}}
nav{{background:#080812;border-bottom:1px solid rgba(255,255,255,.06);padding:12px 20px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap}}
nav a{{color:rgba(255,255,255,.35);text-decoration:none;font-size:.8rem}}
nav a:hover,nav a.active{{color:#ff4d6d}}
.hero{{padding:56px 20px 36px;text-align:center}}
.hero h1{{font-size:clamp(1.8rem,5vw,2.6rem);font-weight:900;color:#ff4d6d;margin-bottom:10px}}
.hero p{{color:rgba(255,255,255,.45);max-width:500px;margin:0 auto 20px;font-size:.95rem;line-height:1.7}}
.pills{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:16px}}
.pill{{background:rgba(255,45,107,.1);border:1px solid rgba(255,45,107,.2);border-radius:20px;padding:5px 14px;font-size:.75rem;color:#ff6b8a}}
.notice{{background:rgba(255,152,0,.05);border:1px solid rgba(255,152,0,.2);border-radius:8px;padding:12px 18px;max-width:640px;margin:0 auto 20px;font-size:.8rem;color:#ffb74d;text-align:left}}
.notice b{{color:#ff9800;display:block;margin-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:18px;max-width:980px;margin:30px auto;padding:0 20px}}
.card{{background:#0f0f1c;border:1px solid rgba(255,255,255,.07);border-radius:12px;overflow:hidden;transition:transform .2s}}
.card:hover{{transform:translateY(-4px)}}
.preview{{height:170px;display:flex;align-items:center;justify-content:center}}
.emoji{{font-size:4rem}}
.info{{padding:16px}}
.info h3{{font-size:.95rem;font-weight:700;margin-bottom:6px}}
.info p{{font-size:.75rem;color:rgba(255,255,255,.45);line-height:1.6;margin-bottom:8px}}
.tags{{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:10px}}
.tag{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:4px;padding:2px 7px;font-size:.65rem;color:rgba(255,255,255,.35)}}
.footer{{display:flex;align-items:baseline;gap:8px;margin-bottom:10px}}
.price{{font-size:1.3rem;font-weight:800;color:#00ff88}}
.split{{font-size:.7rem;color:rgba(255,45,107,.7)}}
.btns{{display:flex;gap:8px}}
.btn-g{{flex:1;background:#ff90e8;color:#000;text-align:center;padding:8px;border-radius:7px;text-decoration:none;font-size:.8rem;font-weight:700}}
.btn-k{{flex:1;background:#ff5e5b;color:#fff;text-align:center;padding:8px;border-radius:7px;text-decoration:none;font-size:.8rem;font-weight:700}}
.loop{{background:#080810;border-top:1px solid rgba(255,255,255,.05);padding:36px 20px;text-align:center}}
.loop h2{{color:#00ff88;margin-bottom:16px;font-size:1.1rem}}
.flow{{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;align-items:center;font-size:.82rem}}
.fs{{background:#0f0f1c;border:1px solid rgba(0,255,136,.15);border-radius:7px;padding:8px 14px;color:#ddd}}
.fa{{color:#444}}
.pcrf{{font-size:.72rem;color:rgba(255,255,255,.25);margin-top:14px;line-height:1.7}}
.pcrf a{{color:#ff4d6d;text-decoration:none}}
footer{{text-align:center;padding:20px;color:rgba(255,255,255,.18);font-size:.7rem;border-top:1px solid rgba(255,255,255,.04)}}
footer a{{color:#ff4d6d;text-decoration:none}}
</style></head><body>

<nav>
  <a href="index.html">Home</a>
  <a href="store.html">Store</a>
  <a href="art.html" class="active">🌹 Art Gallery</a>
  <a href="dashboard.html">Dashboard</a>
  <a href="setup.html">Setup</a>
  <a href="https://ko-fi.com/meekotharaccoon" target="_blank">Ko-fi ☕</a>
</nav>

<div class="hero">
  <h1>🌹 Gaza Rose Gallery</h1>
  <p>7 AI-generated Palestinian art prints. $1 each. 70¢ goes directly to Gaza children via PCRF on every purchase.</p>
  <div class="pills">
    <span class="pill"><b>70¢</b> of every $1 → PCRF (Gaza)</span>
    <span class="pill"><b>30¢</b> → Loop Fund</span>
    <span class="pill">7 prints available</span>
    <span class="pill">4★ Charity Navigator</span>
  </div>
  <div class="notice">
    <b>⚠️ Ko-fi Shop Setup Needed (Meeko action):</b>
    Gumroad buttons work now. Ko-fi buttons link to your shop page.
    To create individual Ko-fi shop items per print: ko-fi.com/account/shop → Add Item → $1 each → copy URL → update data/art_catalog.json → re-run ART_CATALOG engine.
  </div>
</div>

<div class="grid">
{cards}</div>

<div class="loop">
  <h2>The Self-Feeding Loop</h2>
  <div class="flow">
    <div class="fs">You pay $1</div><div class="fa">→</div>
    <div class="fs">70¢ → PCRF Gaza</div><div class="fa">→</div>
    <div class="fs">30¢ → Loop Fund</div><div class="fa">→</div>
    <div class="fs">Fund hits $1</div><div class="fa">→</div>
    <div class="fs">AI auto-buys</div><div class="fa">→</div>
    <div class="fs">Repeats ∞</div>
  </div>
  <p class="pcrf">All Gaza donations → <a href="https://www.pcrf.net" target="_blank">PCRF</a> (EIN 93-1057665, 4★ Charity Navigator, operating since 1991).<br>
  SolarPunk™ is a for-profit AI business. Gaza giving is voluntary, tracked in the <a href="payouts.html">public ledger</a>.</p>
</div>

<footer>SolarPunk™ · <a href="store.html">Store</a> · <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a> · Generated {now}</footer>
</body></html>"""


def run():
    print("ART_CATALOG running...")
    catalog = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_pieces": len(ART_PIECES),
        "price_usd": 1.00,
        "gaza_pct": 70,
        "loop_pct": 30,
        "pieces": ART_PIECES,
        "kofi_setup_instructions": [
            "Go to ko-fi.com/account/shop",
            "Click 'Add Item' for each print",
            "Set price to $1.00 USD each",
            "After creating item, copy its URL (e.g. ko-fi.com/s/xxxxx)",
            "Update kofi_url for each piece in data/art_catalog.json",
            "Re-run ART_CATALOG engine to rebuild art.html with correct URLs",
        ],
    }
    (DATA / "art_catalog.json").write_text(json.dumps(catalog, indent=2))
    html = build_art_html()
    (DOCS / "art.html").write_text(html)
    print(f"  ✅ docs/art.html — {len(ART_PIECES)} pieces ({len(html):,} bytes)")
    print(f"  URL: https://meekotharaccoon-cell.github.io/meeko-nerve-center/art.html")
    print(f"  ⚠️  Action: create 7 Ko-fi shop items at ko-fi.com/account/shop")


if __name__ == "__main__": run()
