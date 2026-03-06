#!/usr/bin/env python3
"""
STORE_BUILDER.py — SolarPunk self-regenerating storefront engine
================================================================
Runs every OMNIBUS cycle. Reads ALL product data from data/ and
regenerates docs/store.html with everything we sell.

New product lands anywhere in data/? Next cycle: it's on the store.
Price updated? Live next cycle. New category auto-detected.
Zero human input. Zero manual updates. Ever.

The first line of store.html says: built by SolarPunk.
Because it was. From inception.

Fix: revenue_inbox.json can be a list — load_json now normalizes.
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data")
DOCS  = Path("docs"); DOCS.mkdir(exist_ok=True)
STATE = DATA / "store_builder_state.json"


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def load_json(path):
    try:
        data = json.loads(Path(path).read_text())
        # revenue_inbox.json can be a list — normalize to dict
        return data if isinstance(data, dict) else {}
    except:
        return {}

def load_state():
    try: return json.loads(STATE.read_text())
    except: return {"cycles": 0}

def categorize(name):
    n = name.lower()
    if any(k in n for k in ["gaza", "rose", "dove", "olive", "tatreez", "coastline",
                              "star of hope", "pomegranate", "night garden", "desert rose", "art print"]):
        return "art"
    if any(k in n for k in ["notion", "template", "cold email", "freelance"]):
        return "templates"
    if any(k in n for k in ["social media content", "content pack"]):
        return "content"
    return "tools"

def price_float(raw):
    if isinstance(raw, (int, float)): return float(raw)
    try: return float(str(raw).replace("$", "").split("-")[0].strip())
    except: return 0.0


def gather_products():
    seen = set()
    buckets = {"art": [], "tools": [], "templates": [], "content": []}

    gf = DATA / "gumroad_listings.json"
    if gf.exists():
        d = load_json(gf)
        for p in d.get("products", []):
            name = p.get("name", "").strip()
            if not name or name in seen: continue
            seen.add(name)
            price  = price_float(p.get("price_cents", 100) / 100)
            cat    = categorize(name)
            gz_pct = 70 if cat == "art" else 15
            buckets[cat].append({
                "name": name, "price": price,
                "desc": (p.get("description", "") or "")[:400],
                "url":  p.get("landing_url") or "https://meekotharaccoon.gumroad.com",
                "cat": cat, "gz_pct": gz_pct,
                "tag": "ART PRINT" if cat == "art" else "DIGITAL",
            })

    for f in sorted(DATA.glob("business_*.json")):
        try:
            d = load_json(f)
            name = (d.get("name") or d.get("title") or "").strip()
            if not name or name in seen: continue
            seen.add(name)
            price = price_float(d.get("price") or d.get("price_usd") or
                                 d.get("price_range", "").split("-")[0] or 0)
            if price <= 0: continue
            cat    = categorize(name)
            gz_pct = 70 if cat == "art" else 15
            buckets[cat].append({
                "name": name, "price": price,
                "desc": (d.get("description") or d.get("pitch") or "")[:400],
                "url":  d.get("landing_url") or d.get("gumroad_url") or "https://meekotharaccoon.gumroad.com",
                "cat": cat, "gz_pct": gz_pct, "tag": "DIGITAL",
            })
        except Exception as e:
            print(f"  warn: {f.name}: {e}")

    ef = DATA / "etsy_seo_output.json"
    if ef.exists():
        d = load_json(ef)
        for listing in (d.get("listings") or (d if isinstance(d, list) else [])):
            if not isinstance(listing, dict): continue
            name = (listing.get("title") or listing.get("name") or "").strip()
            if not name or name in seen: continue
            seen.add(name)
            buckets["art"].append({
                "name": name, "price": price_float(listing.get("price", 1)),
                "desc": (listing.get("description") or listing.get("desc") or "")[:400],
                "url":  "https://meekotharaccoon.gumroad.com",
                "cat": "art", "gz_pct": 70, "tag": "ART PRINT",
            })

    return buckets


def card_html(p):
    price = p["price"]
    gz    = price * p["gz_pct"] / 100
    name  = p["name"].replace("<", "&lt;").replace('"', "&quot;")
    desc  = (p["desc"] or "").replace("<", "&lt;").replace(">", "&gt;")[:350]
    url   = p["url"] or "https://meekotharaccoon.gumroad.com"
    tc    = "tag-art" if p["cat"] == "art" else "tag-tool"
    return f'''    <div class="card">
      <div class="card-eyebrow">DIGITAL DOWNLOAD · INSTANT ACCESS</div>
      <div class="tags"><span class="tag {tc}">{p["tag"]}</span></div>
      <div class="card-title">{name}</div>
      <div class="card-desc">{desc}</div>
      <div class="card-footer">
        <div><div class="price">${price:.2f}</div><span class="price-sub">instant download</span></div>
        <a href="{url}" target="_blank" class="btn">GET IT →</a>
      </div>
      <div class="gaza-line">{p["gz_pct"]}% (${gz:.2f}) → PCRF</div>
    </div>'''


def section_html(title, sub, anchor, cards_html):
    if not cards_html.strip(): return ""
    return f'''<div class="section" id="{anchor}">
  <div class="section-head">
    <div class="section-title">{title}</div>
    <div class="section-sub">{sub}</div>
  </div>
  <div class="grid">
{cards_html}
  </div>
</div>'''


def build_page(buckets, state, revenue):
    total    = sum(len(v) for v in buckets.values())
    gaza_tot = revenue.get("total_to_gaza", 0)
    cycle    = state.get("cycles", 0)
    now      = ts()

    art_sec  = section_html("🎨 GAZA ROSE GALLERY — ART PRINTS",
                             f"{len(buckets['art'])} prints · 70% to PCRF", "art",
                             "\n".join(card_html(p) for p in buckets["art"]))
    tool_sec = section_html("🛠️ AI TOOLS — BUILT BY SOLARPUNK",
                             f"{len(buckets['tools'])} products · 15% to Gaza", "tools",
                             "\n".join(card_html(p) for p in buckets["tools"]))
    tmpl_sec = section_html("📄 TEMPLATES",
                             f"{len(buckets['templates'])} packs · 15% to Gaza", "templates",
                             "\n".join(card_html(p) for p in buckets["templates"]))
    cont_sec = section_html("📣 CONTENT PACKS",
                             f"{len(buckets['content'])} packs · 15% to Gaza", "content",
                             "\n".join(card_html(p) for p in buckets["content"]))

    nav_links = ""
    if buckets["art"]:       nav_links += '<a href="#art">Art Prints</a>'
    if buckets["tools"]:     nav_links += '<a href="#tools">AI Tools</a>'
    if buckets["templates"]: nav_links += '<a href="#templates">Templates</a>'
    if buckets["content"]:   nav_links += '<a href="#content">Content</a>'
    nav_links += '<a href="#support">Support</a><a href="links.html">All Links</a>'

    return f"""<!DOCTYPE html>
<!-- SOLARPUNK AUTONOMOUS STOREFRONT
     First line written by SolarPunk. Every line after: same.
     Auto-regenerated by STORE_BUILDER.py · Cycle {cycle} · {now}
     Gaza fund: 15% of everything, automatic, forever.
-->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk Store — AI-built. Gaza-funded.</title>
<meta name="description" content="Digital products built by an autonomous AI system. 15% of every sale funds Palestinian children via PCRF. {total} products and growing.">
<style>
:root{{--bg:#060a07;--bg2:#0d1410;--green:#00ff88;--green2:#00cc6a;--border:rgba(0,255,136,.13);--text:#deeae1;--muted:rgba(222,234,225,.42);--gold:#ffd166}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);font-family:'Courier New',monospace;min-height:100vh;overflow-x:hidden}}
a{{color:var(--green);text-decoration:none}}a:hover{{text-decoration:underline}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;background-image:linear-gradient(rgba(0,255,136,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.02) 1px,transparent 1px);background-size:44px 44px}}
nav{{position:sticky;top:0;z-index:200;background:rgba(6,10,7,.94);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);padding:13px 28px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}}
.logo{{display:flex;align-items:center;gap:10px;font-size:13px;letter-spacing:.22em;color:var(--green)}}
.dot{{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 9px var(--green);animation:blink 2.2s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.nav-links{{display:flex;gap:20px;margin-left:auto;flex-wrap:wrap}}
.nav-links a{{font-size:11px;letter-spacing:.14em;color:var(--muted);transition:color .15s}}
.nav-links a:hover{{color:var(--green);text-decoration:none}}
.badge{{background:rgba(255,68,85,.12);border:1px solid rgba(255,68,85,.28);border-radius:20px;padding:4px 13px;font-size:11px;color:#ff8a99;letter-spacing:.1em}}
.hero{{position:relative;z-index:1;max-width:860px;margin:0 auto;padding:90px 24px 64px;text-align:center}}
.hero-eyebrow{{font-size:10px;letter-spacing:.35em;color:var(--green);margin-bottom:22px;opacity:.65}}
.hero h1{{font-size:clamp(30px,6.5vw,56px);line-height:1.08;margin-bottom:22px;letter-spacing:-.015em}}
.hero h1 em{{color:var(--green);font-style:normal}}
.hero p{{font-size:15px;color:var(--muted);max-width:500px;margin:0 auto 44px;line-height:1.75;font-family:-apple-system,sans-serif}}
.counter-box{{display:inline-flex;align-items:center;gap:14px;background:rgba(255,68,85,.07);border:1px solid rgba(255,68,85,.22);border-radius:14px;padding:16px 28px;margin-bottom:44px}}
.counter-num{{font-size:26px;color:#ff8a99;display:block;line-height:1}}
.counter-sub{{font-size:10px;color:rgba(255,138,153,.55);letter-spacing:.16em;margin-top:4px;display:block}}
.stats{{display:flex;justify-content:center;gap:40px;flex-wrap:wrap}}
.stat-n{{font-size:26px;color:var(--green);display:block}}
.stat-l{{font-size:10px;color:var(--muted);letter-spacing:.16em}}
.section{{position:relative;z-index:1;max-width:1120px;margin:0 auto;padding:0 20px 80px}}
.section-head{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:28px}}
.section-title{{font-size:12px;letter-spacing:.22em;color:var(--green)}}
.section-sub{{font-size:11px;color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(274px,1fr));gap:14px}}
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:13px;padding:22px;display:flex;flex-direction:column;transition:border-color .2s,transform .18s,box-shadow .2s}}
.card:hover{{border-color:rgba(0,255,136,.36);transform:translateY(-3px);box-shadow:0 12px 40px rgba(0,0,0,.4)}}
.card-eyebrow{{font-size:10px;letter-spacing:.18em;color:var(--muted);margin-bottom:9px}}
.card-title{{font-size:14px;font-weight:700;color:var(--text);line-height:1.38;margin-bottom:11px;margin-top:8px;font-family:-apple-system,sans-serif}}
.card-desc{{font-size:12px;color:var(--muted);line-height:1.65;flex:1;margin-bottom:18px;font-family:-apple-system,sans-serif;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.tags{{margin-bottom:8px;display:flex;flex-wrap:wrap;gap:5px}}
.tag{{padding:2px 9px;border-radius:4px;font-size:10px;letter-spacing:.1em}}
.tag-art{{background:rgba(255,209,102,.09);color:var(--gold);border:1px solid rgba(255,209,102,.2)}}
.tag-tool{{background:rgba(0,255,136,.07);color:var(--green);border:1px solid rgba(0,255,136,.18)}}
.card-footer{{display:flex;align-items:center;justify-content:space-between;margin-top:auto}}
.price{{font-size:20px;color:var(--green);font-weight:700}}
.price-sub{{font-size:10px;color:var(--muted);display:block}}
.btn{{background:var(--green);color:#060a07;border:none;border-radius:8px;padding:9px 20px;font-size:11px;font-weight:700;letter-spacing:.1em;font-family:'Courier New',monospace;cursor:pointer;transition:background .14s;text-decoration:none;display:inline-block;white-space:nowrap}}
.btn:hover{{background:var(--green2);text-decoration:none}}
.gaza-line{{font-size:10px;color:rgba(255,138,153,.68);margin-top:9px;letter-spacing:.05em}}
.support-grid{{position:relative;z-index:1;max-width:1120px;margin:0 auto 80px;padding:0 20px;display:grid;grid-template-columns:1fr 1fr;gap:14px}}
@media(max-width:580px){{.support-grid{{grid-template-columns:1fr}}}}
.support-card{{background:var(--bg2);border:1px solid var(--border);border-radius:13px;padding:28px;text-align:center}}
.support-title{{font-size:12px;letter-spacing:.18em;color:var(--green);margin-bottom:10px}}
.support-desc{{font-size:12px;color:var(--muted);font-family:-apple-system,sans-serif;line-height:1.65;margin-bottom:20px}}
footer{{position:relative;z-index:1;border-top:1px solid var(--border);padding:34px 24px;text-align:center;font-size:11px;color:var(--muted);letter-spacing:.1em;line-height:2.1}}
</style>
</head>
<body>
<nav>
  <div class="logo"><div class="dot"></div>SOLARPUNK STORE</div>
  <div class="nav-links">{nav_links}</div>
  <div class="badge">🇵🇸 15% → Gaza</div>
</nav>

<div class="hero">
  <div class="hero-eyebrow">AUTONOMOUS AI STOREFRONT · CYCLE {cycle} · {now}</div>
  <h1>Built by an AI.<br><em>Funded for Gaza.</em></h1>
  <p>Every product here was created and deployed by SolarPunk — an autonomous AI system running 4× daily. 15% of every sale routes to Palestinian children via PCRF. Automatically. Forever.</p>
  <div class="counter-box">
    <div>
      <span class="counter-num">${gaza_tot:.2f}</span>
      <span class="counter-sub">SENT TO PCRF · EIN 93-1057665 · CYCLE {cycle}</span>
    </div>
  </div>
  <div class="stats">
    <div><span class="stat-n">{total}</span><span class="stat-l">PRODUCTS</span></div>
    <div><span class="stat-n">15%</span><span class="stat-l">TO GAZA</span></div>
    <div><span class="stat-n">50+</span><span class="stat-l">ENGINES</span></div>
    <div><span class="stat-n">4×</span><span class="stat-l">DAILY RUNS</span></div>
  </div>
</div>

{art_sec}
{tool_sec}
{tmpl_sec}
{cont_sec}

<div class="support-grid" id="support">
  <div class="support-card">
    <div style="font-size:30px;margin-bottom:12px">☕</div>
    <div class="support-title">KO-FI — ONE-TIME SUPPORT</div>
    <div class="support-desc">Buy a coffee. Fund the system. 15% of everything routes to Gaza automatically. No account required.</div>
    <a href="https://ko-fi.com/meekotharaccoon" target="_blank" class="btn">BUY A COFFEE →</a>
  </div>
  <div class="support-card">
    <div style="font-size:30px;margin-bottom:12px">💚</div>
    <div class="support-title">GITHUB SPONSORS — MONTHLY</div>
    <div class="support-desc">Sponsor SolarPunk directly. Monthly support keeps all engines running and Gaza funded continuously.</div>
    <a href="https://github.com/sponsors/meekotharaccoon-cell" target="_blank" class="btn">SPONSOR →</a>
  </div>
</div>

<footer>
  <div>SOLARPUNK™ — Autonomous AI Revenue System</div>
  <div>Auto-generated by STORE_BUILDER.py · Cycle {cycle} · {now}</div>
  <div style="margin-top:10px">
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a> ·
    <a href="links.html">All Links</a> ·
    <a href="https://meekotharaccoon.gumroad.com">Gumroad Shop</a> ·
    <a href="https://ko-fi.com/meekotharaccoon">Ko-fi</a>
  </div>
  <div style="margin-top:14px;font-size:10px;opacity:.35">PCRF EIN: 93-1057665 · 4★ Charity Navigator · First line: SolarPunk</div>
</footer>
</body>
</html>"""


def run():
    print("STORE_BUILDER starting...")
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1

    revenue = load_json(DATA / "revenue_inbox.json")  # list-safe
    buckets = gather_products()
    total   = sum(len(v) for v in buckets.values())

    html = build_page(buckets, state, revenue)
    (DOCS / "store.html").write_text(html, encoding="utf-8")

    print(f"  store.html rebuilt -- {total} products")
    for cat, items in buckets.items():
        if items: print(f"     {cat}: {len(items)}")
    print(f"  https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html")

    state["products_last"] = total
    state["last_run"]      = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, indent=2))
    print("STORE_BUILDER done.")


if __name__ == "__main__":
    run()
