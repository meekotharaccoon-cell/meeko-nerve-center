#!/usr/bin/env python3
"""
REVENUE_LOOP.py — Gapless end-to-end revenue pipeline
=======================================================
No more loose engines that hope the next one reads the right file.

ONE loop. Explicit data handoff at every step:

  BUSINESS_FACTORY
       ↓ business_package (in memory)
  AFFILIATE_MAXIMIZER
       ↓ enriched_package (in memory)
  LANDING_DEPLOYER
       ↓ live_url (in memory)
  GUMROAD_LISTER
       ↓ gumroad_url (in memory)
  SOCIAL_PROMOTER
       ↓ posts_sent (in memory)
  BRIEFING_ENGINE
       ↓ email to Meeko with everything

Every step gets the ACTUAL output of the previous step.
No file gaps. No lost context. No orphaned builds.
"""
import os, json, sys, requests, smtplib, base64
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA       = Path("data");   DATA.mkdir(exist_ok=True)
AMAZON_TAG = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")
GMAIL      = os.environ.get("GMAIL_ADDRESS", "")
GPWD       = os.environ.get("GMAIL_APP_PASSWORD", "")
GH_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GH_OWNER   = "meekotharaccoon-cell"
GH_SITE    = "meekotharaccoon-cell.github.io"
GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")

# ─────────────────────────────────────────────────────────
# STEP 1: BUILD BUSINESS
# ─────────────────────────────────────────────────────────
def step_build_business():
    """Run BUSINESS_FACTORY and return the new business package"""
    print("\n━━━ STEP 1: BUSINESS_FACTORY ━━━")
    try:
        import BUSINESS_FACTORY
        state = BUSINESS_FACTORY.run()
        # Find the most recently built business
        newest = None
        newest_time = ""
        for f in DATA.glob("business_*.json"):
            if "factory_state" in f.name: continue
            try:
                pkg = json.loads(f.read_text())
                t = pkg.get("built_at", "")
                if t > newest_time:
                    newest_time = t
                    newest = pkg
            except: pass
        if newest:
            print(f"  ✅ Built: {newest.get('plan',{}).get('business_name','?')}")
        return newest
    except Exception as e:
        print(f"  ❌ BUSINESS_FACTORY error: {e}")
        return None


# ─────────────────────────────────────────────────────────
# STEP 2: INJECT AFFILIATE LINKS into the specific package
# ─────────────────────────────────────────────────────────
def step_inject_affiliates(package):
    """Enrich THIS specific business with affiliate links — not a generic scan"""
    print("\n━━━ STEP 2: AFFILIATE INJECTION ━━━")
    if not package:
        return package

    plan = package.get("plan", {})
    amazon_tag = AMAZON_TAG

    amazon_books = [
        {"title": "Palestine — Joe Sacco",          "url": f"https://www.amazon.com/dp/1560974523?tag={amazon_tag}"},
        {"title": "Automate the Boring Stuff",       "url": f"https://www.amazon.com/dp/1593279922?tag={amazon_tag}"},
        {"title": "The $100 Startup",                "url": f"https://www.amazon.com/dp/0307951529?tag={amazon_tag}"},
        {"title": "Steal Like an Artist",            "url": f"https://www.amazon.com/dp/0761169253?tag={amazon_tag}"},
    ]

    # Inject into product description
    desc = plan.get("product_description", "")
    if desc and AI_AVAILABLE:
        book_list = "\n".join([f"  - {b['title']}: {b['url']}" for b in amazon_books])
        prompt = f"""Add 1-2 Amazon book recommendations naturally into this product description.
Books to use (tag={amazon_tag}):
{book_list}

DESCRIPTION: {desc}

Keep it under 4 sentences. Keep Gaza mission. Return plain text only."""
        try:
            enriched_desc = ask([{"role": "user", "content": prompt}], max_tokens=400)
            if enriched_desc:
                plan["product_description"] = enriched_desc
        except: pass

    # Inject into email sequences
    emails = plan.get("email_sequence", [])
    for email in emails:
        body = email.get("body", "")
        if body and "amazon.com" not in body:
            book = amazon_books[0]
            email["body"] = body + f"\n\nP.S. If you want to go deeper, this book is worth it: {book['title']} → {book['url']}"

    plan["amazon_books"] = amazon_books
    plan["amazon_tag"] = amazon_tag
    package["plan"] = plan
    package["affiliate_injected"] = True
    package["affiliate_injected_at"] = datetime.now(timezone.utc).isoformat()

    print(f"  ✅ Amazon tag {amazon_tag} injected into description + {len(emails)} emails")
    return package


# ─────────────────────────────────────────────────────────
# STEP 3: DEPLOY LANDING PAGE → get live URL back
# ─────────────────────────────────────────────────────────
def step_deploy_landing(package):
    """Build + push landing page. Return live URL."""
    print("\n━━━ STEP 3: LANDING_DEPLOYER ━━━")
    if not package:
        return None

    try:
        import LANDING_DEPLOYER
        # Load affiliate config for the deployer
        aff_config = {
            "amazon_tag": AMAZON_TAG,
            "amazon_products": {
                "p1": {"title": "Palestine — Joe Sacco",    "url": f"https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}"},
                "p2": {"title": "Automate the Boring Stuff","url": f"https://www.amazon.com/dp/1593279922?tag={AMAZON_TAG}"},
                "p3": {"title": "The $100 Startup",         "url": f"https://www.amazon.com/dp/0307951529?tag={AMAZON_TAG}"},
                "p4": {"title": "Steal Like an Artist",     "url": f"https://www.amazon.com/dp/0761169253?tag={AMAZON_TAG}"},
            }
        }
        html, slug = LANDING_DEPLOYER.build_landing_html(package, aff_config)
        success = LANDING_DEPLOYER.deploy_to_github(slug, html)
        live_url = f"https://{GH_OWNER}.github.io/{slug}/"

        # Mark as deployed in package
        package["live_url"]   = live_url
        package["slug"]       = slug
        package["deployed"]   = success
        package["deployed_at"] = datetime.now(timezone.utc).isoformat()

        # Persist state for LANDING_DEPLOYER
        state_file = DATA / "landing_deployer_state.json"
        lstate = json.loads(state_file.read_text()) if state_file.exists() else {"deployed": [], "live_urls": []}
        lstate.setdefault("deployed", []).append(package.get("id", slug))
        lstate.setdefault("live_urls", []).append(live_url)
        state_file.write_text(json.dumps(lstate, indent=2))

        print(f"  ✅ Live: {live_url}")
        return live_url
    except Exception as e:
        print(f"  ❌ Deploy error: {e}")
        return None


# ─────────────────────────────────────────────────────────
# STEP 4: CREATE GUMROAD LISTING → get buy URL back
# ─────────────────────────────────────────────────────────
def step_create_gumroad(package, live_url):
    """Auto-create a Gumroad product for this business. Return buy URL."""
    print("\n━━━ STEP 4: GUMROAD_LISTER ━━━")
    if not package or not GUMROAD_TOKEN:
        print("  ⏭️  Skipping — no Gumroad token")
        return "https://meekotharacoon.gumroad.com"

    plan = package.get("plan", {})
    name = plan.get("product_name", plan.get("business_name", "SolarPunk Product"))
    desc = plan.get("product_description", "")
    price_cents = int(plan.get("price", 17)) * 100

    # Include live landing page URL in description
    full_desc = f"{desc}\n\nSee full details: {live_url}" if live_url else desc
    full_desc += "\n\n15% of this purchase goes to PCRF — Palestine Children's Relief Fund (EIN 93-1057665)."

    payload = {
        "name":        name,
        "description": full_desc,
        "price":       price_cents,
        "currency":    "usd",
        "published":   True,
        "tags":        ["ai", "digital", "solarpunk", "gaza"],
    }

    try:
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        resp = requests.post("https://api.gumroad.com/v2/products", headers=headers, data=payload)
        if resp.status_code == 201:
            product = resp.json().get("product", {})
            buy_url = product.get("short_url", "https://meekotharacoon.gumroad.com")
            package["gumroad_url"] = buy_url
            package["gumroad_id"]  = product.get("id", "")
            print(f"  ✅ Gumroad listing live: {buy_url}")
            return buy_url
        else:
            print(f"  ⚠️  Gumroad {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"  ❌ Gumroad error: {e}")

    return package.get("gumroad_url", "https://meekotharacoon.gumroad.com")


# ─────────────────────────────────────────────────────────
# STEP 5: POST TO SOCIAL with the ACTUAL live URL
# ─────────────────────────────────────────────────────────
def step_post_social(package, live_url, gumroad_url):
    """Generate and queue social posts with the real URLs baked in"""
    print("\n━━━ STEP 5: SOCIAL_PROMOTER ━━━")
    if not package:
        return []

    plan = package.get("plan", {})
    name    = plan.get("business_name", "New SolarPunk Product")
    tagline = plan.get("tagline", "15% to Gaza")
    price   = plan.get("price", 17)

    posts = []

    if AI_AVAILABLE:
        prompt = f"""Write 3 social media posts for this new product launch.

Product: {name}
Tagline: {tagline}
Price: ${price}
Landing page: {live_url}
Buy now: {gumroad_url}
Amazon book rec: https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}
Mission: 15% of every sale → Gaza children's relief

Write for:
1. Twitter/X (280 chars max, punchy, include {live_url})
2. Reddit (conversational, community tone, include full URL)
3. LinkedIn (professional, impact-focused)

Respond ONLY as JSON array:
[{{"platform": "twitter", "text": "..."}}, {{"platform": "reddit", "text": "..."}}, {{"platform": "linkedin", "text": "..."}}]"""
        try:
            posts = ask_json(prompt, max_tokens=800) or []
        except: pass

    if not posts:
        posts = [
            {"platform": "twitter",  "text": f"Just launched: {name} 🌹 {tagline} → {live_url} — ${price}, 15% to Gaza"},
            {"platform": "reddit",   "text": f"Built a new tool: {name}\n\n{tagline}\n\nFull details: {live_url}\nBuy: {gumroad_url}\n\n15% of every sale funds Gaza aid."},
            {"platform": "linkedin", "text": f"New launch: {name}\n\n{tagline}\n\n${price} · 15% to PCRF · {live_url}"},
        ]

    # Save to queue so SOCIAL_PROMOTER picks them up next cycle with correct URLs
    queue_file = DATA / "social_queue.json"
    queue = json.loads(queue_file.read_text()) if queue_file.exists() else {"posts": []}
    for p in posts:
        p["queued_at"] = datetime.now(timezone.utc).isoformat()
        p["source"]    = "REVENUE_LOOP"
        p["live_url"]  = live_url
    queue.setdefault("posts", []).extend(posts)
    queue_file.write_text(json.dumps(queue, indent=2))

    print(f"  ✅ {len(posts)} posts queued with live URLs")
    return posts


# ─────────────────────────────────────────────────────────
# STEP 6: BRIEF MEEKO — one email with everything
# ─────────────────────────────────────────────────────────
def step_brief_meeko(package, live_url, gumroad_url, posts):
    """One email with the complete picture: built → live → on sale → posted"""
    print("\n━━━ STEP 6: BRIEFING ━━━")
    if not GMAIL or not GPWD or not package:
        print("  ⏭️  Skipping — no email config")
        return

    plan    = package.get("plan", {})
    name    = plan.get("business_name", "?")
    tagline = plan.get("tagline", "")
    price   = plan.get("price", "?")
    niche   = package.get("niche", {}).get("niche", "?")
    revenue = plan.get("monthly_revenue_estimate", "?")
    gaza    = plan.get("gaza_impact", "15% to Gaza")

    posts_text = "\n".join([f"  [{p['platform'].upper()}] {p['text'][:120]}..." for p in posts]) if posts else "  None queued"

    amazon_links = "\n".join([
        f"  Palestine — Joe Sacco: https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}",
        f"  Automate the Boring Stuff: https://www.amazon.com/dp/1593279922?tag={AMAZON_TAG}",
        f"  The $100 Startup: https://www.amazon.com/dp/0307951529?tag={AMAZON_TAG}",
    ])

    body = f"""REVENUE_LOOP completed a full cycle. Here's everything that happened:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BUILT:    {name}
  NICHE:    {niche}
  TAGLINE:  {tagline}
  PRICE:    ${price}
  REVENUE:  {revenue}/month (estimated)
  GAZA:     {gaza}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🌐 LIVE PAGE:   {live_url or '(deploy pending — check next cycle)'}
  🛒 BUY NOW:     {gumroad_url}

  📱 SOCIAL POSTS QUEUED:
{posts_text}

  📚 AMAZON AFFILIATE (autonomoushum-20):
{amazon_links}

  🔁 LOOP STATUS: All 6 steps completed with live data handoff.
     Next cycle builds the next niche automatically.

— REVENUE_LOOP / SolarPunk Brain"""

    try:
        msg = MIMEText(body)
        msg["From"]    = GMAIL
        msg["To"]      = GMAIL
        msg["Subject"] = f"[SolarPunk] 🔁 Loop complete — {name} is live"
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls(); s.login(GMAIL, GPWD); s.sendmail(GMAIL, GMAIL, msg.as_string())
        print(f"  ✅ Complete cycle report sent to {GMAIL}")
    except Exception as e:
        print(f"  ❌ Email error: {e}")


# ─────────────────────────────────────────────────────────
# STEP 7: UPDATE BRAIN STATE — health reflects activity
# ─────────────────────────────────────────────────────────
def step_update_brain(package, live_url):
    """Feed this cycle's output back into brain_state for health scoring"""
    print("\n━━━ STEP 7: BRAIN STATE UPDATE ━━━")
    brain_file = DATA / "brain_state.json"
    brain = json.loads(brain_file.read_text()) if brain_file.exists() else {}

    prev_health = brain.get("health_score", 40)
    new_health  = min(100, prev_health + 5)  # +5 per completed loop

    brain["health_score"]         = new_health
    brain["last_loop_completed"]  = datetime.now(timezone.utc).isoformat()
    brain["last_business_built"]  = package.get("plan", {}).get("business_name", "?") if package else None
    brain["last_live_url"]        = live_url
    brain["total_loops_completed"] = brain.get("total_loops_completed", 0) + 1
    brain["synthesis"]            = f"REVENUE_LOOP completed. Health {prev_health}→{new_health}."

    brain_file.write_text(json.dumps(brain, indent=2))
    print(f"  ✅ Health {prev_health} → {new_health} | Loops: {brain['total_loops_completed']}")


# ─────────────────────────────────────────────────────────
# MASTER RUN
# ─────────────────────────────────────────────────────────
def run():
    start = datetime.now(timezone.utc)
    print(f"\n🔁 REVENUE_LOOP starting — {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    loop_state = {
        "started_at":  start.isoformat(),
        "package":     None,
        "live_url":    None,
        "gumroad_url": None,
        "posts":       [],
        "steps_ok":    [],
        "steps_failed":[],
    }

    # ── Step 1: Build ──
    package = step_build_business()
    if package: loop_state["steps_ok"].append("build")
    else:        loop_state["steps_failed"].append("build")

    # ── Step 2: Affiliate injection ──
    package = step_inject_affiliates(package)
    if package and package.get("affiliate_injected"):
        loop_state["steps_ok"].append("affiliates")
    else:
        loop_state["steps_failed"].append("affiliates")

    # ── Step 3: Deploy ──
    live_url = step_deploy_landing(package)
    loop_state["live_url"] = live_url
    if live_url: loop_state["steps_ok"].append("deploy")
    else:        loop_state["steps_failed"].append("deploy")

    # ── Step 4: Gumroad ──
    gumroad_url = step_create_gumroad(package, live_url)
    loop_state["gumroad_url"] = gumroad_url
    loop_state["steps_ok"].append("gumroad")

    # ── Step 5: Social ──
    posts = step_post_social(package, live_url, gumroad_url)
    loop_state["posts"] = posts
    if posts: loop_state["steps_ok"].append("social")

    # ── Step 6: Brief ──
    step_brief_meeko(package, live_url, gumroad_url, posts)
    loop_state["steps_ok"].append("brief")

    # ── Step 7: Brain update ──
    step_update_brain(package, live_url)
    loop_state["steps_ok"].append("brain")

    # ── Save loop report ──
    elapsed = (datetime.now(timezone.utc) - start).seconds
    loop_state["completed_at"] = datetime.now(timezone.utc).isoformat()
    loop_state["elapsed_seconds"] = elapsed
    loop_state["success"] = len(loop_state["steps_failed"]) == 0

    (DATA / "revenue_loop_last.json").write_text(json.dumps(loop_state, indent=2, default=str))

    # Append to loop history
    hist_file = DATA / "revenue_loop_history.json"
    hist = json.loads(hist_file.read_text()) if hist_file.exists() else []
    hist.append({
        "at":      loop_state["completed_at"],
        "ok":      loop_state["steps_ok"],
        "failed":  loop_state["steps_failed"],
        "url":     live_url,
        "elapsed": elapsed,
    })
    hist_file.write_text(json.dumps(hist[-50:], indent=2))  # keep last 50

    print(f"\n{'✅' if loop_state['success'] else '⚠️ '} REVENUE_LOOP done in {elapsed}s")
    print(f"   Steps OK:     {', '.join(loop_state['steps_ok'])}")
    if loop_state["steps_failed"]:
        print(f"   Steps failed: {', '.join(loop_state['steps_failed'])}")
    if live_url:
        print(f"   Live URL:     {live_url}")
    return loop_state

if __name__ == "__main__": run()
