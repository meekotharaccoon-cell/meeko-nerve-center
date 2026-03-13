#!/usr/bin/env python3
"""
NANOSHOP_ENGINE.py — SolarPunk's autonomous micro-storefront builder
====================================================================
What it does every cycle:
  1. Reads product_registry + system_directive — all live products
  2. Generates/updates nanoshop-index.json (the widget's product feed)
  3. Generates individual nanoshop pages: docs/ns/{id}.html
     — Each is a self-contained single-page mini-shop (shareable URL)
     — Contains the PayPal.me button, Gaza split, download link
  4. Generates embed snippets for each product
  5. Builds docs/embed.html — a page showing all embed codes
  6. Posts new products to Bluesky with embed snippet
  7. Writes nanoshop report to data/nanoshop_state.json

The nanoshop.js widget (already in docs/) reads nanoshop-index.json and
auto-rotates products — so anyone who embeds the script tag gets a fresh
product each day.

Embed: <script src="https://meekotharaccoon-cell.github.io/meeko-nerve-center/nanoshop.js"></script>
"""
import os, json, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)
NS   = DOCS / "ns";  NS.mkdir(exist_ok=True)

BASE         = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
WIDGET_URL   = f"{BASE}/nanoshop.js"
BLUESKY_ID   = os.environ.get("BLUESKY_IDENTIFIER", "")
BLUESKY_PWD  = os.environ.get("BLUESKY_APP_PASSWORD", "")
GH_TOKEN     = os.environ.get("GITHUB_TOKEN", "")
GH_REPO      = "meekotharaccoon-cell/meeko-nerve-center"


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb if fb is not None else {}


def load_state():
    return rj("nanoshop_state.json", {
        "pages_generated": 0,
        "products_indexed": 0,
        "last_bluesky_pid": None,
        "announced": [],
    })


def get_all_products():
    """Merge product_registry (has real URLs) with system_directive (has all 12 specs)."""
    registry = rj("product_registry.json", {}).get("products", {})
    directive = rj("system_directive.json", {}).get("product_line_canonical", [])

    merged = {}
    for spec in directive:
        pid = spec["id"]
        reg = registry.get(pid, {})
        merged[pid] = {
            "id":          pid,
            "title":       spec.get("title", reg.get("title", pid)),
            "price":       spec.get("price_usd", reg.get("price", 1.0)),
            "tagline":     spec.get("tagline", ""),
            "gaza":        spec.get("gaza_split_pct", 15),
            "paypal_url":  spec.get("paypal_url", f"https://www.paypal.me/meekotharaccoon/{spec.get('price_usd',1)}USD"),
            "gumroad_url": reg.get("gumroad_url", ""),
            "download_url":reg.get("download_url", ""),
            "format":      spec.get("format", "pdf_guide"),
            "content_ready": reg.get("content_ready", False),
        }
    # Also add any in registry not in directive
    for pid, reg in registry.items():
        if pid not in merged:
            merged[pid] = {
                "id": pid, "title": reg.get("title", pid),
                "price": reg.get("price", 1.0), "tagline": "",
                "gaza": 15, "paypal_url": f"https://www.paypal.me/meekotharaccoon/{reg.get('price',1)}USD",
                "gumroad_url": reg.get("gumroad_url",""),
                "download_url": reg.get("download_url",""),
                "format": "pdf_guide", "content_ready": reg.get("content_ready", False),
            }
    return merged


def write_index(products):
    """docs/nanoshop-index.json — read by nanoshop.js widget."""
    items = []
    for p in products.values():
        items.append({
            "id":       p["id"],
            "title":    p["title"],
            "price":    f"{p['price']:.2f}",
            "tagline":  p["tagline"][:80] if p["tagline"] else "",
            "gaza":     p["gaza"],
            "paypal":   p["paypal_url"],
            "gumroad":  p.get("gumroad_url", ""),
            "shop_url": f"{BASE}/ns/{p['id']}.html",
        })
    idx = {"products": items, "updated": datetime.now(timezone.utc).isoformat(), "total": len(items)}
    (DOCS / "nanoshop-index.json").write_text(json.dumps(idx, indent=2))
    print(f"  ✓ nanoshop-index.json — {len(items)} products")
    return items


def make_gaza_bar_html(pct):
    color = "#e87c5a" if pct >= 70 else "#c8a86b"
    return f"""
    <div class="gaza-wrap">
      <div class="gaza-bar" style="--w:{pct}%;--c:{color}">
        <div class="gaza-fill"></div>
      </div>
      <p class="gaza-label">{pct}% of every purchase → Gaza children via PCRF · EIN 93-1057665</p>
    </div>"""


def write_ns_page(p):
    """docs/ns/{id}.html — standalone shareable nanoshop page."""
    pid    = p["id"]
    title  = p["title"]
    price  = p["price"]
    paypal = p["paypal_url"]
    gumroad= p.get("gumroad_url", "")
    dl_url = p.get("download_url", "")
    tagline= p.get("tagline", "")
    gaza   = p["gaza"]
    fmt    = p.get("format", "pdf_guide")

    # Format-specific details
    fmt_label = "🎨 Digital Art Print" if "image" in fmt else "📖 Digital Guide"
    dl_section = ""
    if dl_url:
        dl_section = f'<a href="{dl_url}" class="btn-dl" target="_blank" rel="noopener">📥 Preview / Download</a>'

    gumroad_btn = ""
    if gumroad:
        gumroad_btn = f'<a href="{gumroad}" class="btn-alt" target="_blank" rel="noopener">Buy on Gumroad instead</a>'

    embed_snippet = f'<script src="{WIDGET_URL}" data-product-id="{pid}" data-title="{title[:50]}" data-price="{price:.2f}" data-paypal="{paypal}" data-gaza="{gaza}"></script>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{tagline}">
<meta property="og:url" content="{BASE}/ns/{pid}.html">
<title>{title} — SolarPunk Nanoshop</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#05050f;color:rgba(255,255,255,.88);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#0c0c1e;border:1px solid rgba(200,168,107,.2);border-radius:16px;
  padding:32px 28px;max-width:380px;width:100%;text-align:center}}
.brand{{font-size:10px;color:rgba(200,168,107,.5);letter-spacing:.1em;margin-bottom:16px}}
.fmt{{font-size:11px;color:rgba(255,255,255,.4);margin-bottom:12px}}
h1{{font-size:1.25rem;font-weight:800;line-height:1.3;margin-bottom:8px}}
.tagline{{font-size:.82rem;color:rgba(255,255,255,.5);line-height:1.5;margin-bottom:20px}}
.price{{font-size:3rem;font-weight:900;color:#c8a86b;line-height:1}}
.price-sub{{font-size:.72rem;color:rgba(255,255,255,.3);margin-top:4px;margin-bottom:20px}}
.gaza-wrap{{margin:16px 0}}
.gaza-bar{{background:rgba(255,255,255,.06);border-radius:4px;height:6px;overflow:hidden}}
.gaza-fill{{height:100%;width:var(--w);background:var(--c)}}
.gaza-label{{font-size:9px;color:rgba(255,255,255,.3);letter-spacing:.04em;margin-top:6px;text-transform:uppercase}}
.btn-buy{{display:block;background:#c8a86b;color:#080808;font-weight:900;font-size:1.1rem;
  border-radius:10px;padding:14px;text-decoration:none;margin:20px 0 10px;
  transition:background .2s}}
.btn-buy:hover{{background:#dfc07d}}
.btn-alt{{display:block;font-size:.78rem;color:rgba(255,255,255,.3);text-decoration:none;
  margin:4px 0;transition:color .2s}}
.btn-alt:hover{{color:rgba(255,255,255,.7)}}
.btn-dl{{display:inline-block;font-size:.78rem;color:rgba(200,168,107,.5);
  text-decoration:none;border:1px solid rgba(200,168,107,.2);border-radius:6px;
  padding:6px 14px;margin:8px 0;transition:all .2s}}
.btn-dl:hover{{color:#c8a86b;border-color:rgba(200,168,107,.5)}}
.embed-section{{margin-top:28px;border-top:1px solid rgba(255,255,255,.06);padding-top:20px;text-align:left}}
.embed-title{{font-size:10px;color:rgba(255,255,255,.3);letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px}}
.embed-code{{background:#000;border:1px solid rgba(255,255,255,.08);border-radius:6px;
  padding:10px;font-size:10px;color:rgba(0,232,122,.7);word-break:break-all;
  font-family:'Courier New',monospace;cursor:pointer}}
.embed-hint{{font-size:9px;color:rgba(255,255,255,.2);margin-top:6px}}
.footer{{margin-top:24px;font-size:9px;color:rgba(255,255,255,.2)}}
.footer a{{color:rgba(200,168,107,.4);text-decoration:none}}
.footer a:hover{{color:#c8a86b}}
</style>
</head>
<body>
<div class="card">
  <div class="brand">⚡ SOLARPUNK NANOSHOP</div>
  <div class="fmt">{fmt_label}</div>
  <h1>{title}</h1>
  <p class="tagline">{tagline}</p>
  <div class="price">${price:.2f}</div>
  <div class="price-sub">One-time · Instant delivery · No account needed</div>
  {make_gaza_bar_html(gaza)}
  <a href="{paypal}" class="btn-buy" target="_blank" rel="noopener">Buy Now — ${price:.2f} via PayPal</a>
  {gumroad_btn}
  {dl_section}

  <div class="embed-section">
    <div class="embed-title">🔌 Embed This Nanoshop</div>
    <div class="embed-code" onclick="navigator.clipboard.writeText(this.textContent).then(()=>this.style.color='#00e87a').catch(()=>{})"
         title="Click to copy">{embed_snippet}</div>
    <div class="embed-hint">Drop this tag into any webpage. Shows as a 1-click shop widget. × to dismiss. No tracking.</div>
  </div>

  <div class="footer">
    <a href="{BASE}/shop.html">Full shop</a> ·
    <a href="{BASE}/proof.html">Gaza proof</a> ·
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Source</a>
  </div>
</div>
</body>
</html>"""

    (NS / f"{pid}.html").write_text(html)
    return f"{BASE}/ns/{pid}.html"


def write_embed_index(products, items):
    """docs/embed.html — a page listing all embed snippets."""
    rows = ""
    for item in items:
        p = products[item["id"]]
        snippet = (f'<script src="{WIDGET_URL}" '
                   f'data-product-id="{item["id"]}" '
                   f'data-title="{item["title"][:40]}" '
                   f'data-price="{item["price"]}" '
                   f'data-paypal="{item["paypal"]}" '
                   f'data-gaza="{item["gaza"]}"></script>')
        rows += f"""
        <div class="row">
          <div class="title">{item['title']}</div>
          <div class="meta">${item['price']} · {item['gaza']}% Gaza · <a href="{item['shop_url']}" target="_blank">view page</a></div>
          <div class="code" onclick="navigator.clipboard.writeText(this.textContent).catch(()=>{{}})" title="Click to copy">{snippet}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Nanoshop — Embed Codes</title>
<style>
body{{background:#05050f;color:rgba(255,255,255,.88);font-family:-apple-system,sans-serif;padding:32px;max-width:800px;margin:auto}}
h1{{color:#c8a86b;margin-bottom:8px}}
.sub{{color:rgba(255,255,255,.4);font-size:.85rem;margin-bottom:32px;line-height:1.5}}
.main-embed{{background:#000;border:1px solid rgba(0,232,122,.2);border-radius:8px;padding:14px;
  font-family:monospace;font-size:.8rem;color:#00e87a;word-break:break-all;margin-bottom:32px;
  cursor:pointer}}
.row{{background:#0c0c1e;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:18px;margin-bottom:14px}}
.title{{font-size:.95rem;font-weight:700;margin-bottom:4px}}
.meta{{font-size:.75rem;color:rgba(255,255,255,.4);margin-bottom:10px}}
.meta a{{color:rgba(200,168,107,.6);text-decoration:none}}
.code{{background:#000;border:1px solid rgba(255,255,255,.07);border-radius:6px;
  padding:10px;font-family:monospace;font-size:.72rem;color:rgba(0,232,122,.6);
  word-break:break-all;cursor:pointer}}
.code:hover{{border-color:rgba(0,232,122,.3)}}
</style>
</head><body>
<h1>⚡ SolarPunk Nanoshop — Embed Anywhere</h1>
<p class="sub">
  Drop one &lt;script&gt; tag into any webpage and it becomes a 1-click purchase point.
  Replaces the ad slot. User sees a mini-shop, buys in 2 clicks via PayPal, or hits × to dismiss.
  <strong>Zero setup. No account. No platform fees for PayPal.me direct.</strong>
  <br><br>
  This one tag auto-rotates products daily:<br>
</p>
<div class="main-embed" onclick="navigator.clipboard.writeText(this.textContent).catch(()=>{{}})" title="Click to copy"><script src="{WIDGET_URL}"></script></div>

<h2 style="color:#ffd166;font-size:1rem;margin-bottom:16px">Or pin a specific product:</h2>
{rows}

<div style="text-align:center;color:rgba(255,255,255,.2);font-size:.75rem;margin-top:40px">
  <a href="shop.html" style="color:rgba(200,168,107,.4);text-decoration:none">Full shop</a> ·
  <a href="proof.html" style="color:rgba(200,168,107,.4);text-decoration:none">Gaza proof</a> ·
  SolarPunk™ · autonomous · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</div>
</body></html>"""

    (DOCS / "embed.html").write_text(html)
    print(f"  ✓ embed.html — {len(items)} embed snippets")


def bluesky_announce(product, page_url):
    """Post a new nanoshop to Bluesky."""
    if not BLUESKY_ID or not BLUESKY_PWD:
        return False
    try:
        # Auth
        login = urllib.request.Request(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            data=json.dumps({"identifier": BLUESKY_ID, "password": BLUESKY_PWD}).encode(),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(login, timeout=15) as r:
            sess = json.loads(r.read())

        p = product
        text = (
            f"⚡ New SolarPunk Nanoshop:\n\n"
            f"{p['title']}\n"
            f"${p['price']:.2f} · {p['gaza']}% → Gaza children (PCRF)\n\n"
            f"Drop 1 script tag on any webpage → instant shop widget\n"
            f"Replaces ads. User keeps scrolling.\n\n"
            f"Embed: {BASE}/embed.html\n"
            f"Buy: {page_url}"
        )[:300]

        post = urllib.request.Request(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            data=json.dumps({
                "repo": sess["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }
            }).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {sess['accessJwt']}"},
            method="POST"
        )
        with urllib.request.urlopen(post, timeout=15): pass
        print(f"  ✓ Bluesky: announced {p['id']}")
        return True
    except Exception as e:
        print(f"  Bluesky skip: {e}")
        return False


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nNANOSHOP_ENGINE — {ts}")

    state = load_state()
    products = get_all_products()

    if not products:
        print("  No products found — waiting for system_directive")
        return {"status": "no_products"}

    # Build index
    items = write_index(products)

    # Generate individual pages
    pages_built = 0
    announced = state.get("announced", [])
    new_announcements = []

    for pid, p in products.items():
        page_url = write_ns_page(p)
        pages_built += 1
        # Announce new products on Bluesky (ones not yet announced)
        if pid not in announced:
            announced_ok = bluesky_announce(p, page_url)
            if announced_ok:
                announced.append(pid)
                new_announcements.append(pid)

    # Build embed index page
    write_embed_index(products, items)

    print(f"  ✓ {pages_built} nanoshop pages in docs/ns/")

    state.update({
        "ts": ts,
        "pages_generated": pages_built,
        "products_indexed": len(items),
        "announced": announced,
        "new_announcements": new_announcements,
        "widget_url": WIDGET_URL,
        "index_url": f"{BASE}/nanoshop-index.json",
        "embed_page": f"{BASE}/embed.html",
    })
    (DATA / "nanoshop_state.json").write_text(json.dumps(state, indent=2))
    print(f"  Done: {pages_built} pages | {len(items)} indexed | {len(new_announcements)} announced")
    return state


if __name__ == "__main__":
    run()
