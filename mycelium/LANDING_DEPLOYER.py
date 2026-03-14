# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
LANDING_DEPLOYER.py v3 — Deploys landing pages to docs/ in THIS repo.
======================================================================
PREVIOUS BUG: Was trying to push to meekotharaccoon-cell.github.io
(a separate repo). GITHUB_TOKEN only has write access to the CURRENT
repo. All deploys silently failed.

FIX: Write to docs/{slug}/index.html in THIS repo. The OMNIBRAIN.yml
commit step already does `git add docs/` so these get committed and
pushed automatically. GitHub Pages serves this repo at:
  meekotharaccoon-cell.github.io/meeko-nerve-center/{slug}/

Also exposes build_landing_html() so REVENUE_LOOP can call it directly.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA       = Path("data");   DATA.mkdir(exist_ok=True)
DOCS       = Path("docs");   DOCS.mkdir(exist_ok=True)
AMAZON_TAG = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")
GUMROAD    = "https://meekotharacoon.gumroad.com"
BASE_URL   = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"


def load_state():
    f = DATA / "landing_deployer_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"deployed": [], "live_urls": [], "cycles": 0}


def save_state(s):
    (DATA / "landing_deployer_state.json").write_text(json.dumps(s, indent=2))


def find_undeployed():
    state = load_state()
    deployed_ids = set(state.get("deployed", []))
    pending = []
    for f in sorted(DATA.glob("business_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if "factory_state" in f.name:
            continue
        try:
            biz = json.loads(f.read_text())
            bid = biz.get("id", f.stem)
            if bid not in deployed_ids:
                pending.append(biz)
        except:
            pass
    return pending


def build_landing_html(biz, affiliate_config=None):
    """Build complete HTML landing page. Returns (html_string, slug)."""
    plan  = biz.get("plan", {})
    niche = biz.get("niche", {})
    amazon_tag = (affiliate_config or {}).get("amazon_tag", AMAZON_TAG)
    amazon_products = (affiliate_config or {}).get("amazon_products", {
        "p1": {"title": "The $100 Startup", "url": f"https://www.amazon.com/dp/0307951529?tag={amazon_tag}"},
        "p2": {"title": "Palestine — Joe Sacco", "url": f"https://www.amazon.com/dp/1560974523?tag={amazon_tag}"},
        "p3": {"title": "Steal Like an Artist", "url": f"https://www.amazon.com/dp/0761169253?tag={amazon_tag}"},
        "p4": {"title": "Automate the Boring Stuff", "url": f"https://www.amazon.com/dp/1593279922?tag={amazon_tag}"},
    })

    name        = plan.get("business_name", niche.get("niche", "SolarPunk Product"))
    tagline     = plan.get("tagline", "Built by autonomous AI. 15% to Gaza.")
    description = plan.get("product_description", f"Premium digital product. {tagline}")
    price       = plan.get("price", niche.get("price", 17))
    product_nm  = plan.get("product_name", name)
    keywords    = ", ".join(plan.get("seo_keywords", ["AI", "digital products", "Gaza"]))
    launch_steps = plan.get("launch_steps", [])
    gaza_impact = plan.get("gaza_impact", f"15% of every ${price} sale goes to Gaza")
    email_seq   = plan.get("email_sequence", [])

    # Build slug from niche info — no spaces or slashes
    raw_niche = niche.get("niche", biz.get("id", "product")).lower()
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in raw_niche.replace(" ", "-"))
    slug = slug.strip("-")[:40]

    book_html = ""
    for key, prod in list(amazon_products.items())[:4]:
        url   = prod.get("url", f"https://www.amazon.com?tag={amazon_tag}")
        title = prod.get("title", "Recommended Book")
        book_html += f'<a class="book" href="{url}" target="_blank" rel="noopener"><span>📖</span><span class="bt">{title}</span><span class="bc">Amazon →</span></a>\n'

    steps_html = ""
    if launch_steps:
        steps_html = "<ul class='steps'>" + "".join(f"<li>{s}</li>" for s in launch_steps) + "</ul>"

    email_html = ""
    if email_seq:
        e0 = email_seq[0]
        email_html = f'<div class="email-preview"><strong>{e0.get("subject","Welcome!")}</strong><p>{str(e0.get("body",""))[:200]}...</p></div>'

    gumroad_url = biz.get("gumroad_url", GUMROAD)
    live_url = f"{BASE_URL}/{slug}/"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<meta name="description" content="{tagline}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{tagline}">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c10;color:#dde;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh}}
.hero{{background:linear-gradient(135deg,#080c10,#0d1a0a);padding:80px 20px 60px;text-align:center}}
h1{{font-size:clamp(1.8rem,5vw,3rem);font-weight:800;color:#00ff88;margin-bottom:12px;line-height:1.2}}
.tag{{color:rgba(255,255,255,0.5);font-size:1rem;margin-bottom:28px;max-width:600px;display:block;margin-inline:auto}}
.price-block{{display:inline-flex;align-items:center;gap:16px;background:rgba(0,255,136,0.08);border:1px solid rgba(0,255,136,0.2);border-radius:12px;padding:14px 24px;margin-bottom:24px}}
.pnum{{font-size:2.5rem;font-weight:800;color:#00ff88}}
.psub{{font-size:.75rem;color:rgba(255,255,255,0.4);line-height:1.6;text-align:left}}
.btn{{display:inline-block;background:#00ff88;color:#080c10;font-weight:800;font-size:1rem;padding:16px 40px;border-radius:10px;text-decoration:none;margin-bottom:10px}}
.btn:hover{{background:#00dd77}}
.pill{{display:inline-block;background:rgba(255,45,107,0.12);border:1px solid rgba(255,45,107,0.3);border-radius:20px;padding:6px 16px;color:#ff2d6b;font-size:.8rem;margin-top:6px}}
.sec{{max-width:860px;margin:0 auto;padding:50px 20px}}
.sec h2{{font-size:1.4rem;font-weight:700;margin-bottom:16px;color:#ffd700}}
.desc{{color:rgba(255,255,255,0.65);line-height:1.8;margin-bottom:20px}}
.steps{{list-style:none;display:grid;gap:10px}}
.steps li{{background:rgba(255,255,255,0.04);border-left:3px solid #00ff88;border-radius:6px;padding:12px 16px;color:rgba(255,255,255,0.7)}}
.steps li::before{{content:"→ ";color:#00ff88;font-weight:bold}}
.mission{{background:rgba(255,45,107,0.06);border:1px solid rgba(255,45,107,0.2);border-radius:12px;padding:28px;text-align:center;margin:32px 0}}
.mission h3{{color:#ff2d6b;font-size:1.2rem;margin-bottom:10px}}
.mission p{{color:rgba(255,255,255,0.6);line-height:1.8}}
.books{{background:rgba(255,215,0,0.03);border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);padding:40px 20px}}
.books h3{{text-align:center;color:#ffd700;margin-bottom:4px}}
.books-sub{{text-align:center;color:rgba(255,255,255,0.25);font-size:.75rem;margin-bottom:20px}}
.books-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;max-width:760px;margin:0 auto}}
.book{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,215,0,0.1);border-radius:8px;padding:14px;text-decoration:none;display:flex;flex-direction:column;gap:6px}}
.book:hover{{border-color:rgba(255,215,0,0.3)}}
.bt{{color:#fff;font-size:.75rem;font-weight:600;line-height:1.4;flex:1}}
.bc{{color:#ffd700;font-size:.65rem;letter-spacing:1px}}
.amz{{text-align:center;color:rgba(255,255,255,0.15);font-size:.65rem;margin-top:12px}}
.email-preview{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:18px;margin-top:14px}}
.email-preview strong{{color:#fff;display:block;margin-bottom:6px}}
.email-preview p{{color:rgba(255,255,255,0.45);font-size:.85rem;line-height:1.6}}
.cta-bottom{{text-align:center;padding:50px 20px}}
footer{{text-align:center;padding:30px;color:rgba(255,255,255,0.2);font-size:.75rem;border-top:1px solid rgba(255,255,255,0.05)}}
footer a{{color:#ff2d6b;text-decoration:none}}
</style>
</head>
<body>

<div class="hero">
  <h1>{name}</h1>
  <span class="tag">{tagline}</span>
  <div class="price-block">
    <span class="pnum">${price}</span>
    <span class="psub">One-time<br>Instant delivery<br>No subscription</span>
  </div><br>
  <a class="btn" href="{gumroad_url}" target="_blank">Get Instant Access →</a><br>
  <span class="pill">🌹 15% of every sale → Gaza aid</span>
</div>

<div class="sec">
  <h2>What You're Getting</h2>
  <p class="desc">{description}</p>
  {f'<h2 style="margin-top:28px">How To Launch</h2>{steps_html}' if steps_html else ""}
  {f'<h2 style="margin-top:36px">Your Welcome Email</h2>{email_html}' if email_html else ""}
  <div class="mission">
    <h3>🌹 The Gaza Connection</h3>
    <p>{gaza_impact}</p>
    <p style="margin-top:10px;font-size:.8rem;color:rgba(255,255,255,0.35)">
      → <a href="https://www.pcrf.net" target="_blank" style="color:#ff2d6b">PCRF — Palestine Children's Relief Fund</a>
      · 4-star Charity Navigator · EIN 93-1057665
    </p>
  </div>
</div>

{f'<div class="books"><h3>📚 Recommended Reading</h3><p class="books-sub">Amazon Associates · tag: {amazon_tag}</p><div class="books-grid">{book_html}</div><p class="amz">As an Amazon Associate I earn from qualifying purchases.</p></div>' if book_html else ""}

<div class="cta-bottom">
  <a class="btn" href="{gumroad_url}" target="_blank">Get {product_nm} — ${price} →</a>
</div>

<footer>
  Built by <a href="{BASE_URL}">SolarPunk / Gaza Rose</a> · Autonomous AI · 15% to Gaza ·
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Fork this system</a>
  <br>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
</footer>
</body>
</html>"""

    return html, slug


def deploy_local(slug, html_content):
    """Write to docs/{slug}/index.html — committed by OMNIBRAIN git step."""
    out_dir = DOCS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html_content)
    live_url = f"{BASE_URL}/{slug}/"
    print(f"  🌐 Staged: {live_url}")
    return live_url


def run():
    state = load_state()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"LANDING_DEPLOYER cycle {state['cycles']} | {len(state.get('deployed',[]))} pages live")

    pending = find_undeployed()
    if not pending:
        print("  All businesses already deployed")
        save_state(state)
        return state

    affiliate_config = {
        "amazon_tag": AMAZON_TAG,
        "amazon_products": {
            "p1": {"title": "The $100 Startup", "url": f"https://www.amazon.com/dp/0307951529?tag={AMAZON_TAG}"},
            "p2": {"title": "Palestine — Joe Sacco", "url": f"https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}"},
            "p3": {"title": "Steal Like an Artist", "url": f"https://www.amazon.com/dp/0761169253?tag={AMAZON_TAG}"},
            "p4": {"title": "Automate the Boring Stuff", "url": f"https://www.amazon.com/dp/1593279922?tag={AMAZON_TAG}"},
        }
    }

    for biz in pending[:3]:
        biz_id = biz.get("id", "unknown")
        print(f"  Deploying: {biz.get('plan', {}).get('business_name', biz_id)}")
        try:
            html, slug = build_landing_html(biz, affiliate_config)
            live_url   = deploy_local(slug, html)
            state.setdefault("deployed", []).append(biz_id)
            state.setdefault("live_urls", []).append(live_url)
            # Write back to biz file so REVENUE_LOOP can read live_url
            biz["live_url"] = live_url
            for f in DATA.glob(f"business_*{biz_id}*.json"):
                if "factory_state" not in f.name:
                    f.write_text(json.dumps(biz, indent=2))
        except Exception as e:
            print(f"  ❌ {e}")

    (DATA / "live_landing_pages.json").write_text(json.dumps(
        {"urls": state.get("live_urls", []), "updated": datetime.now(timezone.utc).isoformat()}, indent=2
    ))

    save_state(state)
    print(f"  Total live pages: {len(state.get('live_urls', []))}")
    return state


if __name__ == "__main__":
    run()
