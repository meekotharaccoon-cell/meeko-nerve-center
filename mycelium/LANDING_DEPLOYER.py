#!/usr/bin/env python3
"""
LANDING_DEPLOYER.py — Auto-publishes every business as a live GitHub Pages site
================================================================================
Reads BUSINESS_FACTORY output from data/business_*.json
Generates polished landing pages with:
  - Buy button (Gumroad)
  - Amazon affiliate book recommendations (?tag=autonomoushum-20)
  - Gaza mission story
  - Email capture (free lead magnet)
  - SEO meta tags
Deploys to meekotharaccoon-cell.github.io/{business-slug}
Runs every OMNIBRAIN cycle. New business = new live URL within minutes.
"""
import os, json, sys, requests
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA   = Path("data");   DATA.mkdir(exist_ok=True)
DOCS   = Path("docs");   DOCS.mkdir(exist_ok=True)

GH_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
AMAZON_TAG = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")
GUMROAD    = "https://meekotharacoon.gumroad.com"

SITE_REPO  = "meekotharaccoon-cell/meekotharaccoon-cell.github.io"
SITE_OWNER = "meekotharaccoon-cell"
SITE_REPO_NAME = "meekotharaccoon-cell.github.io"

def load_affiliate_config():
    f = DATA / "affiliate_config.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"amazon_tag": AMAZON_TAG, "amazon_products": {}}

def load_deployed():
    f = DATA / "landing_deployer_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"deployed": [], "cycles": 0}

def save_deployed(state):
    (DATA / "landing_deployer_state.json").write_text(json.dumps(state, indent=2))

def find_undeployed_businesses():
    """Find businesses built but not yet deployed as landing pages"""
    state = load_deployed()
    deployed_ids = set(state.get("deployed", []))
    pending = []
    for f in DATA.glob("business_*.json"):
        if f.name == "business_factory_state.json":
            continue
        try:
            biz = json.loads(f.read_text())
            bid = biz.get("id", f.stem)
            if bid not in deployed_ids:
                pending.append(biz)
        except:
            pass
    return pending, state

def build_landing_html(biz, affiliate_config):
    """Build a complete, styled landing page for a business"""
    plan = biz.get("plan", {})
    niche = biz.get("niche", {})
    amazon_tag = affiliate_config.get("amazon_tag", AMAZON_TAG)
    amazon_products = affiliate_config.get("amazon_products", {})

    name        = plan.get("business_name", niche.get("niche", "SolarPunk Product"))
    tagline     = plan.get("tagline", "Built by autonomous AI. 15% to Gaza.")
    description = plan.get("product_description", "")
    price       = plan.get("price", niche.get("price", 17))
    product_nm  = plan.get("product_name", name)
    keywords    = ", ".join(plan.get("seo_keywords", ["AI tools", "digital products", "Gaza"]))
    launch_steps = plan.get("launch_steps", [])
    gaza_impact = plan.get("gaza_impact", f"15% of every ${price} goes to Gaza")
    revenue_est = plan.get("monthly_revenue_estimate", "")

    # Amazon book recs
    book_html = ""
    for key, prod in list(amazon_products.items())[:4]:
        url = prod.get("url", f"https://www.amazon.com?tag={amazon_tag}")
        title = prod.get("title", "Recommended Book")
        book_html += f'<a class="book" href="{url}" target="_blank" rel="noopener"><span class="book-icon">📖</span><span>{title}</span><span class="book-cta">Amazon →</span></a>\n'

    # Email sequence preview
    email_seq = plan.get("email_sequence", [])
    email_preview = ""
    if email_seq:
        first = email_seq[0]
        email_preview = f'<div class="email-preview"><strong>{first.get("subject","Welcome!")}</strong><p>{first.get("body","")[:200]}...</p></div>'

    slug = biz.get("id", "product").split("_")[0]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — Gaza Rose</title>
<meta name="description" content="{tagline}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{tagline}">
<meta property="og:url" content="https://meekotharaccoon-cell.github.io/{slug}">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--rose:#ff2d6b;--gold:#ffd700;--dark:#080c10;--green:#00ff88}}
body{{background:var(--dark);color:#dde;font-family:'Outfit',sans-serif;min-height:100vh}}
.hero{{background:linear-gradient(135deg,#080c10,#0d1a0a);padding:80px 20px 60px;text-align:center}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:var(--green);margin-bottom:12px;line-height:1.2}}
.hero .tag{{color:rgba(255,255,255,0.5);font-size:1.1rem;margin-bottom:32px;max-width:600px;margin-inline:auto}}
.price-block{{display:inline-flex;align-items:center;gap:16px;background:rgba(0,255,136,0.08);border:1px solid rgba(0,255,136,0.25);border-radius:16px;padding:16px 28px;margin-bottom:28px}}
.price{{font-size:3rem;font-weight:800;color:var(--green)}}
.price-sub{{text-align:left;font-size:.8rem;color:rgba(255,255,255,0.4);line-height:1.6}}
.buy-btn{{display:inline-block;background:var(--green);color:#080c10;font-weight:800;font-size:1.1rem;padding:18px 48px;border-radius:12px;text-decoration:none;transition:.2s;margin-bottom:12px}}
.buy-btn:hover{{background:#00dd77;transform:translateY(-2px)}}
.gaza-pill{{display:inline-block;background:rgba(255,45,107,0.12);border:1px solid rgba(255,45,107,0.3);border-radius:20px;padding:8px 20px;color:var(--rose);font-size:.85rem;margin-top:8px}}
.section{{max-width:900px;margin:0 auto;padding:60px 20px}}
.section h2{{font-size:1.6rem;font-weight:700;margin-bottom:20px}}
.gold{{color:var(--gold)}}
.rose{{color:var(--rose)}}
.desc{{color:rgba(255,255,255,0.65);line-height:1.8;font-size:1rem;margin-bottom:24px}}
.steps{{list-style:none;display:grid;gap:12px}}
.steps li{{background:rgba(255,255,255,0.04);border-left:3px solid var(--green);border-radius:8px;padding:14px 18px;color:rgba(255,255,255,0.7)}}
.steps li::before{{content:'→ ';color:var(--green);font-weight:bold}}
.mission-box{{background:rgba(255,45,107,0.06);border:1px solid rgba(255,45,107,0.2);border-radius:16px;padding:32px;text-align:center;margin:40px 0}}
.mission-box h3{{color:var(--rose);font-size:1.3rem;margin-bottom:12px}}
.mission-box p{{color:rgba(255,255,255,0.6);line-height:1.8}}
.books-section{{background:rgba(255,215,0,0.04);border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);padding:48px 20px}}
.books-section h3{{text-align:center;color:var(--gold);margin-bottom:8px}}
.books-sub{{text-align:center;color:rgba(255,255,255,0.3);font-size:.8rem;margin-bottom:24px}}
.books-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;max-width:800px;margin:0 auto}}
.book{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,215,0,0.1);border-radius:10px;padding:16px;text-decoration:none;display:flex;flex-direction:column;gap:8px;transition:.2s}}
.book:hover{{border-color:rgba(255,215,0,0.3);background:rgba(255,215,0,0.05)}}
.book-icon{{font-size:1.8rem}}
.book span:nth-child(2){{color:#fff;font-size:.8rem;font-weight:600;line-height:1.4;flex:1}}
.book-cta{{color:var(--gold);font-size:.7rem;letter-spacing:1px}}
.amz-disc{{text-align:center;color:rgba(255,255,255,0.18);font-size:.7rem;margin-top:16px}}
.email-preview{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:20px;margin-top:16px}}
.email-preview strong{{color:#fff;display:block;margin-bottom:8px}}
.email-preview p{{color:rgba(255,255,255,0.5);font-size:.9rem;line-height:1.6}}
.footer{{text-align:center;padding:40px;color:rgba(255,255,255,0.25);font-size:.8rem;border-top:1px solid rgba(255,255,255,0.06)}}
.footer a{{color:var(--rose);text-decoration:none}}
</style>
</head>
<body>

<div class="hero">
  <h1>{name}</h1>
  <p class="tag">{tagline}</p>
  <div class="price-block">
    <span class="price">${price}</span>
    <span class="price-sub">One-time payment<br>Instant delivery<br>No subscription</span>
  </div>
  <br>
  <a class="buy-btn" href="{GUMROAD}" target="_blank">Get Instant Access →</a>
  <br>
  <span class="gaza-pill">🌹 15% of every sale → Gaza aid</span>
</div>

<div class="section">
  <h2 class="gold">What You're Getting</h2>
  <p class="desc">{description}</p>

  {f'<h2 class="gold" style="margin-top:32px">How To Launch</h2><ul class="steps">' + "".join(f"<li>{s}</li>" for s in launch_steps) + "</ul>" if launch_steps else ""}

  {f'<h2 class="gold" style="margin-top:40px">What Comes In Your Inbox</h2>{email_preview}' if email_preview else ""}

  <div class="mission-box">
    <h3>🌹 The Gaza Connection</h3>
    <p>{gaza_impact}</p>
    <p style="margin-top:12px;font-size:.85rem;color:rgba(255,255,255,0.4)">
      Funds go to <a href="https://www.pcrf.net" target="_blank" style="color:var(--rose)">PCRF — Palestine Children's Relief Fund</a>
      · 4-star Charity Navigator · EIN 93-1057665
    </p>
  </div>
</div>

{f'<div class="books-section"><h3>📚 Books That Go With This</h3><p class="books-sub">Recommended reads · Amazon Associates: {amazon_tag}</p><div class="books-grid">{book_html}</div><p class="amz-disc">As an Amazon Associate I earn from qualifying purchases.</p></div>' if book_html else ""}

<div style="text-align:center;padding:60px 20px">
  <a class="buy-btn" href="{GUMROAD}" target="_blank">Get {product_nm} — ${price} →</a>
  <p style="color:rgba(255,255,255,0.3);margin-top:12px;font-size:.8rem">{revenue_est}</p>
</div>

<div class="footer">
  <p>Built by <a href="https://meekotharaccoon-cell.github.io">Gaza Rose / Meeko</a> · Autonomous AI system · 15% to Gaza</p>
  <p style="margin-top:8px"><a href="https://meekotharaccoon-cell.github.io">← Back to all products</a></p>
  <p style="margin-top:8px;font-size:.7rem">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} · <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Fork this system</a></p>
</div>
</body>
</html>"""
    return html, slug

def deploy_to_github(slug, html_content):
    """Push landing page directly to meekotharaccoon-cell.github.io repo"""
    if not GH_TOKEN:
        print("  ⚠️  No GITHUB_TOKEN — saving locally only")
        (DOCS / f"{slug}.html").write_text(html_content)
        return False

    path = f"{slug}/index.html"
    url  = f"https://api.github.com/repos/{SITE_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json"}

    # Check if file exists (need sha to update)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    import base64
    payload = {
        "message": f"🏗️ Deploy landing page: {slug}",
        "content": base64.b64encode(html_content.encode()).decode(),
        "committer": {"name": "SolarPunk Brain", "email": "meekotharaccoon@gmail.com"}
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code in (200, 201):
        print(f"  🌐 Live: https://meekotharaccoon-cell.github.io/{slug}/")
        return True
    else:
        print(f"  ⚠️  Deploy failed {resp.status_code}: {resp.text[:200]}")
        (DOCS / f"{slug}.html").write_text(html_content)
        return False

def run():
    state = load_deployed()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"🚀 LANDING_DEPLOYER cycle {state['cycles']} | {len(state.get('deployed',[]))} pages live")

    affiliate_config = load_affiliate_config()
    pending, _ = find_undeployed_businesses()

    if not pending:
        print("  ✅ All businesses already deployed")
        save_deployed(state)
        return state

    for biz in pending[:2]:  # Deploy up to 2 per cycle
        biz_id = biz.get("id", "unknown")
        print(f"  📄 Deploying: {biz_id}")
        try:
            html, slug = build_landing_html(biz, affiliate_config)
            success = deploy_to_github(slug, html)
            state.setdefault("deployed", []).append(biz_id)
            state.setdefault("live_urls", []).append(
                f"https://meekotharaccoon-cell.github.io/{slug}/"
            )
            print(f"  ✅ {biz.get('plan',{}).get('business_name','?')} deployed")
        except Exception as e:
            print(f"  ❌ Deploy error for {biz_id}: {e}")

    # Save index of all live landing pages
    (DATA / "live_landing_pages.json").write_text(
        json.dumps({"urls": state.get("live_urls", []), "updated": datetime.now(timezone.utc).isoformat()}, indent=2)
    )

    save_deployed(state)
    print(f"  🌐 Total live pages: {len(state.get('live_urls',[]))}")
    return state

if __name__ == "__main__": run()
