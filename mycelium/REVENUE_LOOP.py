# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
REVENUE_LOOP.py v5 — Bulletproof end-to-end revenue pipeline
=============================================================
FIXES from v4:
- Import ask_json_list (not ask_json) for social posts — ask_json returns
  dict, but social posts prompt returns a JSON array [...]. Was silently
  returning None every cycle → always used fallback posts.
- ask_json_list added to AI_CLIENT in this session.
- FIXED IndentationError: step("brief") and step("brain") were at col 18
  instead of col 4 — caused SyntaxError preventing any execution.

FLOW (all self-contained, file-based handoff):
  1. Read latest business from data/business_*.json
  2. Inject affiliate links into description
  3. Deploy landing page to docs/{slug}/index.html
  4. Create/update Gumroad listing (if token exists)
  5. Queue social posts to data/social_queue.json
  6. Email Meeko the full report
  7. Update brain_state health score
"""
import os, json, sys, requests, smtplib, re
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

DATA     = Path("data");   DATA.mkdir(exist_ok=True)
DOCS     = Path("docs");   DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

sys.path.insert(0, str(MYCELIUM))
try:
    from AI_CLIENT import ask, ask_json, ask_json_list
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

GMAIL         = os.environ.get("GMAIL_ADDRESS", "")
GPWD          = os.environ.get("GMAIL_APP_PASSWORD", "")
GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
AMAZON_TAG    = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")
BASE_URL      = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

AMAZON_BOOKS = [
    {"title": "The $100 Startup",          "url": f"https://www.amazon.com/dp/0307951529?tag={AMAZON_TAG}"},
    {"title": "Palestine — Joe Sacco",     "url": f"https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}"},
    {"title": "Steal Like an Artist",      "url": f"https://www.amazon.com/dp/0761169253?tag={AMAZON_TAG}"},
    {"title": "Automate the Boring Stuff", "url": f"https://www.amazon.com/dp/1593279922?tag={AMAZON_TAG}"},
]


# ── STEP 1: GET BUSINESS ────────────────────────────────────────────
def step_get_business():
    print("\n━━━ STEP 1: GET BUSINESS ━━━")
    newest, newest_time = None, ""
    for f in DATA.glob("business_*.json"):
        if "factory_state" in f.name:
            continue
        try:
            pkg = json.loads(f.read_text())
            t = pkg.get("built_at", "")
            if t > newest_time:
                newest_time, newest = t, pkg
        except:
            pass

    if newest:
        name = newest.get("plan", {}).get("business_name", "?")
        print(f"  ✅ Found: {name} (built {newest_time[:10]})")
        return newest

    print("  ⚠️  No business found — BUSINESS_FACTORY hasn't run yet this cycle")
    return None


# ── STEP 2: AFFILIATE INJECTION ─────────────────────────────────────
def step_inject_affiliates(package):
    print("\n━━━ STEP 2: AFFILIATE INJECTION ━━━")
    if not package:
        return package

    plan = package.get("plan", {})
    desc = plan.get("product_description", "")

    if desc and AI_AVAILABLE and "amazon.com" not in desc:
        book = AMAZON_BOOKS[0]
        prompt = (f"Add ONE Amazon book recommendation naturally to this product description.\n"
                  f"Book: {book['title']} → {book['url']}\nDescription: {desc}\n"
                  f"Keep under 4 sentences. Return plain text only.")
        try:
            enriched = ask([{"role": "user", "content": prompt}], max_tokens=300)
            if enriched and len(enriched) > 20:
                plan["product_description"] = enriched
        except:
            pass

    for email in plan.get("email_sequence", []):
        if email.get("body") and "amazon.com" not in email.get("body", ""):
            book = AMAZON_BOOKS[1]
            email["body"] += f"\n\nP.S. Worth reading: {book['title']} → {book['url']}"

    plan["amazon_books"] = AMAZON_BOOKS
    plan["amazon_tag"]   = AMAZON_TAG
    package["plan"] = plan
    package["affiliate_injected"] = True
    print(f"  ✅ Amazon tag {AMAZON_TAG} injected")
    return package


# ── STEP 3: DEPLOY LANDING PAGE ─────────────────────────────────────
def step_deploy_landing(package):
    print("\n━━━ STEP 3: DEPLOY LANDING PAGE ━━━")
    if not package:
        return None

    existing_url = package.get("live_url")
    if existing_url:
        slug_path = existing_url.split("/meeko-nerve-center/")[-1].rstrip("/")
        if (DOCS / slug_path / "index.html").exists():
            print(f"  Already live: {existing_url}")
            return existing_url

    plan       = package.get("plan", {})
    niche      = package.get("niche", {})
    name       = plan.get("business_name", niche.get("niche", "Product"))
    desc       = plan.get("product_description", plan.get("tagline", ""))
    price      = plan.get("price", niche.get("price", 17))
    tagline    = plan.get("tagline", "Built by AI. 15% to Gaza.")
    gumroad_url= package.get("gumroad_url", "https://meekotharacoon.gumroad.com")
    keywords   = ", ".join(plan.get("seo_keywords", ["AI", "digital", "Gaza"]))
    steps      = plan.get("launch_steps", [])
    gaza       = plan.get("gaza_impact", f"15% of every ${price} sale → PCRF")
    product_nm = plan.get("product_name", name)

    raw  = niche.get("niche", name).lower()
    slug = re.sub(r'[^a-z0-9-]', '-', raw.replace(" ", "-"))
    slug = re.sub(r'-+', '-', slug).strip('-')[:40]

    book_html = "".join(
        f'<a class="book" href="{b["url"]}" target="_blank">'
        f'<span>📖</span><span class="bt">{b["title"]}</span>'
        f'<span class="bc">Amazon →</span></a>\n'
        for b in AMAZON_BOOKS
    )
    steps_html = ("<ul class='steps'>" +
                  "".join(f"<li>{s}</li>" for s in steps) +
                  "</ul>") if steps else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<meta name="description" content="{tagline}">
<meta name="keywords" content="{keywords}">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c10;color:#dde;font-family:-apple-system,BlinkMacSystemFont,sans-serif}}
.hero{{background:linear-gradient(135deg,#080c10,#0d1a0a);padding:80px 20px 60px;text-align:center}}
h1{{font-size:clamp(1.8rem,5vw,3rem);font-weight:800;color:#00ff88;margin-bottom:12px}}
.tag{{color:rgba(255,255,255,.5);font-size:1rem;display:block;margin:0 auto 24px;max-width:600px}}
.pb{{display:inline-flex;align-items:center;gap:16px;background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.2);border-radius:12px;padding:14px 24px;margin-bottom:22px}}
.pn{{font-size:2.5rem;font-weight:800;color:#00ff88}}
.ps{{font-size:.75rem;color:rgba(255,255,255,.4);line-height:1.6;text-align:left}}
.btn{{display:inline-block;background:#00ff88;color:#080c10;font-weight:800;font-size:1rem;padding:16px 40px;border-radius:10px;text-decoration:none;margin-bottom:10px}}
.pill{{display:inline-block;background:rgba(255,45,107,.12);border:1px solid rgba(255,45,107,.3);border-radius:20px;padding:6px 16px;color:#ff2d6b;font-size:.8rem}}
.sec{{max-width:860px;margin:0 auto;padding:48px 20px}}
.sec h2{{font-size:1.3rem;font-weight:700;margin-bottom:14px;color:#ffd700}}
.desc{{color:rgba(255,255,255,.65);line-height:1.8;margin-bottom:18px}}
.steps{{list-style:none;display:grid;gap:8px}}
.steps li{{background:rgba(255,255,255,.04);border-left:3px solid #00ff88;border-radius:6px;padding:11px 15px;color:rgba(255,255,255,.7)}}
.steps li::before{{content:"→ ";color:#00ff88;font-weight:bold}}
.mission{{background:rgba(255,45,107,.06);border:1px solid rgba(255,45,107,.2);border-radius:12px;padding:26px;text-align:center;margin:28px 0}}
.mission h3{{color:#ff2d6b;margin-bottom:10px}}
.mission p{{color:rgba(255,255,255,.6);line-height:1.8}}
.books{{background:rgba(255,215,0,.03);border-top:1px solid rgba(255,215,0,.1);padding:36px 20px}}
.books h3{{text-align:center;color:#ffd700;margin-bottom:4px}}
.bs{{text-align:center;color:rgba(255,255,255,.25);font-size:.7rem;margin-bottom:18px}}
.bg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;max-width:720px;margin:0 auto}}
.book{{background:rgba(255,255,255,.03);border:1px solid rgba(255,215,0,.1);border-radius:8px;padding:12px;text-decoration:none;display:flex;flex-direction:column;gap:6px}}
.bt{{color:#fff;font-size:.75rem;font-weight:600;line-height:1.4;flex:1}}
.bc{{color:#ffd700;font-size:.65rem}}
.am{{text-align:center;color:rgba(255,255,255,.15);font-size:.65rem;margin-top:10px}}
.ctab{{text-align:center;padding:48px 20px}}
footer{{text-align:center;padding:28px;color:rgba(255,255,255,.2);font-size:.75rem;border-top:1px solid rgba(255,255,255,.05)}}
footer a{{color:#ff2d6b;text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <h1>{name}</h1>
  <span class="tag">{tagline}</span>
  <div class="pb"><span class="pn">${price}</span><span class="ps">One-time<br>Instant access<br>No subscription</span></div><br>
  <a class="btn" href="{gumroad_url}" target="_blank">Get Instant Access →</a><br><br>
  <span class="pill">🌹 15% of every sale → Gaza aid</span>
</div>
<div class="sec">
  <h2>What You're Getting</h2>
  <p class="desc">{desc}</p>
  {f'<h2 style="margin-top:26px">Launch Steps</h2>{steps_html}' if steps_html else ""}
  <div class="mission">
    <h3>🌹 The Gaza Connection</h3>
    <p>{gaza}</p>
    <p style="margin-top:10px;font-size:.8rem;color:rgba(255,255,255,.3)">→ <a href="https://www.pcrf.net" style="color:#ff2d6b">PCRF</a> · 4-star Charity Navigator · EIN 93-1057665</p>
  </div>
</div>
<div class="books">
  <h3>📚 Recommended Reading</h3>
  <p class="bs">Amazon Associates · tag: {AMAZON_TAG}</p>
  <div class="bg">{book_html}</div>
  <p class="am">As an Amazon Associate I earn from qualifying purchases.</p>
</div>
<div class="ctab"><a class="btn" href="{gumroad_url}" target="_blank">Get {product_nm} — ${price} →</a></div>
<footer>Built by <a href="{BASE_URL}">SolarPunk</a> · 15% to Gaza ·
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Fork this system</a><br>
  Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</footer>
</body></html>"""

    out_dir = DOCS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    live_url = f"{BASE_URL}/{slug}/"
    print(f"  ✅ Staged docs/{slug}/ → {live_url}")

    package["live_url"]    = live_url
    package["slug"]        = slug
    package["deployed_at"] = datetime.now(timezone.utc).isoformat()

    for f in DATA.glob("business_*.json"):
        if "factory_state" in f.name:
            continue
        try:
            existing = json.loads(f.read_text())
            if existing.get("id") == package.get("id"):
                f.write_text(json.dumps(package, indent=2))
                break
        except:
            pass

    ld_f = DATA / "landing_deployer_state.json"
    ld   = json.loads(ld_f.read_text()) if ld_f.exists() else {"deployed": [], "live_urls": []}
    bid  = package.get("id", slug)
    if bid not in ld.get("deployed", []):
        ld.setdefault("deployed", []).append(bid)
        ld.setdefault("live_urls", []).append(live_url)
    ld_f.write_text(json.dumps(ld, indent=2))

    return live_url


# ── STEP 4: GUMROAD LISTING ─────────────────────────────────────────
def step_gumroad(package, live_url):
    print("\n━━━ STEP 4: GUMROAD ━━━")
    if package and package.get("gumroad_url") and "gumroad.com/l/" in package.get("gumroad_url", ""):
        print(f"  Already listed: {package['gumroad_url']}")
        return package["gumroad_url"]

    if not GUMROAD_TOKEN or not package:
        print(f"  {'No token' if not GUMROAD_TOKEN else 'No package'} — skipping")
        return "https://meekotharacoon.gumroad.com"

    plan  = package.get("plan", {})
    name  = plan.get("product_name", plan.get("business_name", "SolarPunk Product"))
    desc  = plan.get("product_description", plan.get("tagline", ""))
    price = int(plan.get("price", package.get("niche", {}).get("price", 17))) * 100

    if live_url:
        desc += f"\n\nFull details: {live_url}"
    desc += "\n\n15% of this purchase goes to PCRF — Palestine Children's Relief Fund (EIN 93-1057665)."

    try:
        resp = requests.post(
            "https://api.gumroad.com/v2/products",
            headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
            data={"name": name, "description": desc, "price": price, "currency": "usd", "published": True},
            timeout=20
        )
        if resp.status_code == 201:
            buy_url = resp.json().get("product", {}).get("short_url", "https://meekotharacoon.gumroad.com")
            package["gumroad_url"] = buy_url
            print(f"  ✅ Listed: {buy_url}")
            return buy_url
        else:
            print(f"  Gumroad {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  Gumroad error: {e}")

    return package.get("gumroad_url", "https://meekotharacoon.gumroad.com")


# ── STEP 5: SOCIAL POSTS ────────────────────────────────────────────
def step_social(package, live_url, gumroad_url):
    print("\n━━━ STEP 5: SOCIAL QUEUE ━━━")
    if not package:
        return []

    plan    = package.get("plan", {})
    name    = plan.get("business_name", "SolarPunk Product")
    tagline = plan.get("tagline", "15% to Gaza")
    price   = plan.get("price", 17)

    posts = []
    if AI_AVAILABLE:
        prompt = (
            f"Write 3 social posts for this product launch.\n\n"
            f"Product: {name}\nTagline: {tagline}\nPrice: ${price}\n"
            f"Landing page: {live_url}\nBuy: {gumroad_url}\n"
            f"Mission: 15% → Gaza children's relief\n\n"
            f"Write:\n1. Twitter/X (280 chars max, include URL)\n"
            f"2. Reddit (conversational, include URL, no spam)\n"
            f"3. LinkedIn (professional, mission-focused)\n\n"
            f"Return ONLY a JSON array: "
            f'[{{"platform":"twitter","text":"..."}},{{"platform":"reddit","text":"..."}},{{"platform":"linkedin","text":"..."}}]'
        )
        try:
            posts = ask_json_list(prompt, max_tokens=600)
        except Exception as e:
            print(f"  AI social gen error: {e}")

    if not posts:
        posts = [
            {"platform": "twitter",  "text": f"🌹 New: {name} — {tagline} {live_url} ${price}, 15% to Gaza"},
            {"platform": "reddit",   "text": f"Built with AI: {name}\n\n{tagline}\n\n{live_url}\n15% → Gaza."},
            {"platform": "linkedin", "text": f"New launch: {name}\n{tagline}\n${price} · 15% to PCRF · {live_url}"},
        ]

    qf = DATA / "social_queue.json"
    q  = json.loads(qf.read_text()) if qf.exists() else {"posts": []}
    ts = datetime.now(timezone.utc).isoformat()
    for p in posts:
        p.update({"queued_at": ts, "source": "REVENUE_LOOP", "live_url": live_url,
                  "niche": package.get("niche", {}).get("niche", "")})
    q.setdefault("posts", []).extend(posts)
    q["posts"] = q["posts"][-300:]
    qf.write_text(json.dumps(q, indent=2))
    print(f"  ✅ {len(posts)} posts queued")
    return posts


# ── STEP 6: EMAIL BRIEFING ──────────────────────────────────────────
def step_brief(package, live_url, gumroad_url, posts):
    print("\n━━━ STEP 6: EMAIL BRIEFING ━━━")
    if not GMAIL or not GPWD or not package:
        print("  Skipping — no email config or no package")
        return

    plan    = package.get("plan", {})
    name    = plan.get("business_name", "?")
    price   = plan.get("price", "?")
    revenue = plan.get("monthly_revenue_estimate", "?")
    gaza    = plan.get("gaza_impact", "15% to Gaza")

    posts_txt  = "\n".join(f"  [{p['platform'].upper()}] {p['text'][:100]}..." for p in posts) or "  none"
    amazon_txt = "\n".join(f"  {b['title']}: {b['url']}" for b in AMAZON_BOOKS[:3])

    body = f"""REVENUE_LOOP cycle complete.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BUILT:   {name}
  PRICE:   ${price}
  REVENUE: {revenue}
  GAZA:    {gaza}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  LIVE:  {live_url or '(staged — live after git push)'}
  BUY:   {gumroad_url}

  SOCIAL QUEUED:
{posts_txt}

  AMAZON ({AMAZON_TAG}):
{amazon_txt}

— REVENUE_LOOP v5 / SolarPunk"""

    try:
        msg = MIMEText(body)
        msg["From"] = GMAIL; msg["To"] = GMAIL
        msg["Subject"] = f"[SolarPunk] Loop complete — {name}"
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls(); s.login(GMAIL, GPWD); s.sendmail(GMAIL, GMAIL, msg.as_string())
        print(f"  ✅ Email sent")
    except Exception as e:
        print(f"  Email error: {e}")


# ── STEP 7: BRAIN UPDATE ────────────────────────────────────────────
def step_brain(package, live_url):
    print("\n━━━ STEP 7: BRAIN UPDATE ━━━")
    bf    = DATA / "brain_state.json"
    brain = json.loads(bf.read_text()) if bf.exists() else {}
    prev  = brain.get("health_score", 40)
    new   = min(100, prev + 5)
    brain.update({
        "health_score":          new,
        "last_loop_completed":   datetime.now(timezone.utc).isoformat(),
        "last_business_built":   package.get("plan", {}).get("business_name") if package else None,
        "last_live_url":         live_url,
        "total_loops_completed": brain.get("total_loops_completed", 0) + 1,
    })
    bf.write_text(json.dumps(brain, indent=2))
    print(f"  ✅ Health {prev}→{new} | Total loops: {brain['total_loops_completed']}")


# ── MASTER LOOP ─────────────────────────────────────────────────────
def run():
    start = datetime.now(timezone.utc)
    print(f"\n🔁 REVENUE_LOOP v5 — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    loop = {"started_at": start.isoformat(), "steps_ok": [], "steps_failed": [],
            "live_url": None, "gumroad_url": None, "posts": []}

    def step(name, fn, *args):
        try:
            result = fn(*args)
            loop["steps_ok"].append(name)
            return result
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            loop["steps_failed"].append(name)
            return None

    package     = step("get_business", step_get_business)
    package     = step("affiliates",   step_inject_affiliates, package) or package
    live_url    = step("deploy",       step_deploy_landing,    package)
    gumroad_url = step("gumroad",      step_gumroad,           package, live_url) or "https://meekotharacoon.gumroad.com"
    posts       = step("social",       step_social,            package, live_url, gumroad_url) or []
    step("brief", step_brief, package, live_url, gumroad_url, posts)
    step("brain", step_brain, package, live_url)

    loop.update({
        "live_url": live_url, "gumroad_url": gumroad_url, "posts": posts,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": (datetime.now(timezone.utc) - start).seconds,
        "success": not loop["steps_failed"],
    })

    (DATA / "revenue_loop_last.json").write_text(json.dumps(loop, indent=2, default=str))
    hf   = DATA / "revenue_loop_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({"at": loop["completed_at"], "ok": loop["steps_ok"],
                 "failed": loop["steps_failed"], "url": live_url})
    hf.write_text(json.dumps(hist[-100:], indent=2))

    print(f"\n{'✅' if loop['success'] else '⚠️ '} REVENUE_LOOP done {loop['elapsed_seconds']}s")
    print(f"   OK: {', '.join(loop['steps_ok'])}")
    if loop["steps_failed"]: print(f"   FAILED: {', '.join(loop['steps_failed'])}")
    if live_url: print(f"   Live: {live_url}")
    return loop


if __name__ == "__main__":
    run()
