#!/usr/bin/env python3
"""
BUSINESS_FACTORY.py v3 — Infinite business generation machine
=============================================================
PREVIOUS BUG: Had a fixed list of 8 niches. After all 8 were built,
the engine silently did nothing every cycle. Dead weight.

FIX: After initial 8 niches, reads architect_plan.json for AI-generated
new niches. If that's empty, generates its own via AI. Never stops.
Always builds one new business per cycle, forever.

REVENUE STRATEGY:
- Digital products ($9-$97) on Gumroad → instant delivery
- Landing pages auto-deployed to docs/ → live in next commit
- Social posts queued → SOCIAL_PROMOTER sends them
- 15% to Gaza built into every product
"""
import os, json, sys, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")
AMAZON_TAG = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")

# Seed niches — first 8 cycles
SEED_NICHES = [
    {"niche": "AI Prompt Packs", "product_type": "digital_download", "price": 17,
     "platform": "Gumroad", "audience": "AI enthusiasts, creators, marketers"},
    {"niche": "Palestinian Art Prints", "product_type": "print_on_demand", "price": 25,
     "platform": "Redbubble+Etsy", "audience": "conscious consumers, art lovers"},
    {"niche": "GitHub Actions Templates", "product_type": "digital_download", "price": 27,
     "platform": "Gumroad", "audience": "developers, indie hackers"},
    {"niche": "Notion Templates for Freelancers", "product_type": "digital_download", "price": 19,
     "platform": "Gumroad", "audience": "freelancers, solopreneurs"},
    {"niche": "Autonomous Business Guide", "product_type": "ebook", "price": 37,
     "platform": "Gumroad", "audience": "entrepreneurs wanting passive income"},
    {"niche": "Social Media Content Packs", "product_type": "digital_download", "price": 22,
     "platform": "Gumroad", "audience": "small businesses, content creators"},
    {"niche": "Grant Writing Templates", "product_type": "digital_download", "price": 47,
     "platform": "Gumroad", "audience": "nonprofits, artists, community orgs"},
    {"niche": "Email Automation Blueprints", "product_type": "digital_download", "price": 37,
     "platform": "Gumroad", "audience": "marketers, online business owners"},
    {"niche": "AI Side Income Blueprint 2.0", "product_type": "ebook", "price": 27,
     "platform": "Gumroad", "audience": "anyone wanting to monetize AI skills"},
    {"niche": "Palestine Solidarity Zine Pack", "product_type": "digital_download", "price": 12,
     "platform": "Gumroad", "audience": "activists, artists, educators"},
    {"niche": "GitHub Pages Website Kit", "product_type": "digital_download", "price": 19,
     "platform": "Gumroad", "audience": "developers wanting free hosting"},
    {"niche": "Freelance Cold Email Templates", "product_type": "template_pack", "price": 17,
     "platform": "Gumroad", "audience": "freelancers, consultants, agencies"},
]

AFFILIATE_LINKS = {
    "gumroad":    "https://gumroad.com/?via=meeko",
    "ko-fi":      "https://ko-fi.com/meekotharaccoon",
    "github":     "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
    "amazon_p1":  f"https://www.amazon.com/dp/0307951529?tag={AMAZON_TAG}",
    "amazon_p2":  f"https://www.amazon.com/dp/1560974523?tag={AMAZON_TAG}",
}


def load():
    f = DATA / "business_factory_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "businesses_built": [], "total_revenue_potential": 0}


def save(state):
    (DATA / "business_factory_state.json").write_text(json.dumps(state, indent=2))


def get_next_niche(built_niches, state):
    """Pick next niche: seed list first, then ARCHITECT plan, then AI-generated."""
    # Try seed list first
    for nd in SEED_NICHES:
        if nd["niche"] not in built_niches:
            return nd

    # Try ARCHITECT plan
    plan_file = DATA / "architect_plan.json"
    if plan_file.exists():
        try:
            plan = json.loads(plan_file.read_text())
            for nd in plan.get("business_niches", []):
                if nd.get("niche") and nd["niche"] not in built_niches:
                    print(f"  Using ARCHITECT niche: {nd['niche']}")
                    return nd
        except:
            pass

    # AI generates fresh niches — never stops
    if not AI_AVAILABLE:
        # Fallback: generate a variant of an existing niche
        cycle = state.get("cycles", 1)
        variants = [
            {"niche": f"Digital Business Toolkit v{cycle}", "product_type": "digital_download",
             "price": 27 + (cycle % 20), "platform": "Gumroad", "audience": "entrepreneurs"},
            {"niche": f"AI Workflow Pack {cycle}", "product_type": "template_pack",
             "price": 17 + (cycle % 30), "platform": "Gumroad", "audience": "knowledge workers"},
            {"niche": f"Gaza Art Collection {cycle}", "product_type": "digital_download",
             "price": 15, "platform": "Gumroad", "audience": "art lovers"},
        ]
        for v in variants:
            if v["niche"] not in built_niches:
                return v
        return {"niche": f"SolarPunk Bundle {cycle}", "product_type": "digital_download",
                "price": 47, "platform": "Gumroad", "audience": "anyone"}

    # Use AI to generate a fresh, untapped niche
    built_list = list(built_niches)[-20:]  # last 20 to avoid repeats
    prompt = f"""You are BUSINESS_FACTORY for SolarPunk — autonomous AI income system.
Already built these niches: {json.dumps(built_list)}

Generate ONE new profitable digital product niche that:
- Has NOT been built yet (different from the list above)
- Is a digital product ($9-$97)
- Can be fully automated
- Fits SolarPunk mission: AI + autonomy + Gaza solidarity
- Has real demand right now (2025-2026 market)

Respond ONLY with JSON:
{{"niche": "Exact Niche Name", "product_type": "digital_download|ebook|template_pack|video_course_notes", "price": 27, "platform": "Gumroad", "audience": "who buys this in one sentence"}}"""

    result = ask_json(prompt, max_tokens=200)
    if result and result.get("niche") and result["niche"] not in built_niches:
        print(f"  AI generated new niche: {result['niche']}")
        return result

    # Last resort: timestamp variant
    ts = datetime.now(timezone.utc).strftime("%b %Y")
    return {"niche": f"AI Tools Mega Pack — {ts}", "product_type": "digital_download",
            "price": 37, "platform": "Gumroad", "audience": "AI power users"}


def build_plan(niche_data):
    if not AI_AVAILABLE:
        return _fallback_plan(niche_data)

    affiliate_block = "\n".join(f"  - {k}: {v}" for k, v in AFFILIATE_LINKS.items())
    prompt = f"""You are BUSINESS_FACTORY. Build a complete, launchable digital business.

NICHE: {niche_data['niche']}
PRODUCT TYPE: {niche_data['product_type']}
PRICE: ${niche_data['price']}
PLATFORM: {niche_data['platform']}
AUDIENCE: {niche_data['audience']}

AFFILIATE LINKS (embed naturally):
{affiliate_block}

15% of every sale goes to Gaza. Build this into the story.

Respond ONLY as JSON — NO extra text, NO markdown:
{{
  "business_name": "catchy name",
  "tagline": "punchy one-liner",
  "product_name": "specific product name",
  "product_description": "3 sentences, compelling, Gaza mission included",
  "price": {niche_data['price']},
  "email_sequence": [
    {{"subject": "...", "body": "100-word email", "day": 0}},
    {{"subject": "...", "body": "100-word email", "day": 3}},
    {{"subject": "...", "body": "100-word email", "day": 7}}
  ],
  "social_posts": [
    {{"platform": "twitter", "text": "280 chars max"}},
    {{"platform": "reddit", "text": "community-tone post"}},
    {{"platform": "linkedin", "text": "professional post"}}
  ],
  "seo_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "launch_steps": ["step 1", "step 2", "step 3", "step 4"],
  "monthly_revenue_estimate": "$X-$Y/month",
  "gaza_impact": "what goes to Gaza and how it helps"
}}"""

    try:
        result = ask_json(prompt, max_tokens=3000)
        if result and result.get("business_name"):
            return result
    except Exception as e:
        print(f"  AI error: {e}")

    return _fallback_plan(niche_data)


def _fallback_plan(nd):
    return {
        "business_name":   f"SolarPunk {nd['niche']}",
        "tagline":         f"{nd['niche']} — built by AI, 15% to Gaza",
        "product_name":    f"{nd['niche']} Pack",
        "product_description": f"Premium {nd['niche']} created by autonomous AI. Every purchase sends 15% to Palestinian children via PCRF. Instant download, no subscription.",
        "price":           nd["price"],
        "email_sequence":  [
            {"subject": f"Your {nd['niche']} is ready", "body": f"Thanks for your purchase. Your {nd['niche']} pack is attached. 15% went to Gaza. — Meeko", "day": 0},
            {"subject": "How's it going?", "body": "Just checking in. Let me know if you have questions. More resources at ko-fi.com/meekotharaccoon", "day": 3},
        ],
        "social_posts":    [
            {"platform": "twitter",  "text": f"Just launched: {nd['niche']} — ${nd['price']}, 15% to Gaza 🌹 gumroad.com"},
            {"platform": "reddit",   "text": f"Built this with autonomous AI: {nd['niche']}. ${nd['price']}, 15% goes to Palestinian kids."},
            {"platform": "linkedin", "text": f"New digital product: {nd['niche']}. ${nd['price']}. 15% to PCRF (Gaza children's relief)."},
        ],
        "seo_keywords":    [nd["niche"].lower(), "digital download", "ai tools", "gaza solidarity"],
        "launch_steps":    ["Create Gumroad listing", "Post to social", "Email list", "Repeat"],
        "monthly_revenue_estimate": f"${nd['price'] * 10}-${nd['price'] * 40}/month",
        "gaza_impact":     f"15% of every ${nd['price']} sale = ${nd['price'] * 0.15:.2f} to PCRF",
    }


def save_package(plan, niche_data):
    niche_slug = niche_data["niche"].lower().replace(" ", "_").replace("/", "_").replace(".", "")[:40]
    ts         = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    biz_id     = f"{niche_slug}_{ts}"

    package = {
        "id":       biz_id,
        "niche":    niche_data,
        "plan":     plan,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "status":   "ready_to_launch",
        "affiliate_links": AFFILIATE_LINKS,
        "estimated_monthly_revenue": plan.get("monthly_revenue_estimate", "unknown"),
        "gaza_contribution": "15% of all sales",
    }

    (DATA / f"business_{niche_slug}.json").write_text(json.dumps(package, indent=2))
    print(f"  Saved: data/business_{niche_slug}.json")
    return package


def notify(package):
    if not GMAIL or not GPWD:
        return
    plan = package["plan"]
    body = f"""New business built by BUSINESS_FACTORY:

Business:  {plan.get('business_name','?')}
Tagline:   {plan.get('tagline','?')}
Price:     ${plan.get('price','?')}
Revenue:   {plan.get('monthly_revenue_estimate','?')}
Gaza:      {plan.get('gaza_impact','15%')}

Launch steps:
{chr(10).join(f"  {i+1}. {s}" for i, s in enumerate(plan.get('launch_steps', [])))}

Next: LANDING_DEPLOYER will create live page on next cycle.
Social posts queued for SOCIAL_PROMOTER.

— BUSINESS_FACTORY / SolarPunk"""
    try:
        msg = MIMEText(body)
        msg["From"] = GMAIL; msg["To"] = GMAIL
        msg["Subject"] = f"[SolarPunk] 🏗️ Built: {plan.get('business_name','?')}"
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls(); s.login(GMAIL, GPWD); s.sendmail(GMAIL, GMAIL, msg.as_string())
    except Exception as e:
        print(f"  Email error: {e}")


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    built_niches = {b.get("niche") for b in state.get("businesses_built", [])}
    print(f"BUSINESS_FACTORY cycle {state['cycles']} | {len(built_niches)} niches built | AI={'on' if AI_AVAILABLE else 'off'}")

    niche_data = get_next_niche(built_niches, state)
    print(f"  Building: {niche_data['niche']} @ ${niche_data['price']}")

    plan = build_plan(niche_data)
    if not plan:
        print("  Plan failed — skipping cycle")
        save(state)
        return state

    package = save_package(plan, niche_data)

    # Queue social posts for SOCIAL_PROMOTER
    social_posts = plan.get("social_posts", [])
    if social_posts:
        qf = DATA / "social_queue.json"
        q  = json.loads(qf.read_text()) if qf.exists() else {"posts": []}
        ts = datetime.now(timezone.utc).isoformat()
        for p in social_posts:
            p.update({"queued_at": ts, "source": "BUSINESS_FACTORY", "niche": niche_data["niche"]})
        q.setdefault("posts", []).extend(social_posts)
        q["posts"] = q["posts"][-200:]
        qf.write_text(json.dumps(q, indent=2))
        print(f"  {len(social_posts)} social posts queued")

    state.setdefault("businesses_built", []).append({
        "niche":    niche_data["niche"],
        "name":     plan.get("business_name", "?"),
        "price":    niche_data["price"],
        "revenue":  plan.get("monthly_revenue_estimate", "?"),
        "built_at": datetime.now(timezone.utc).isoformat(),
    })
    state["total_revenue_potential"] = sum(b.get("price", 0) * 20 for b in state["businesses_built"])

    notify(package)
    print(f"  ✅ {plan.get('business_name','?')} | {plan.get('monthly_revenue_estimate','?')}")
    print(f"  💰 Gaza: {plan.get('gaza_impact','15%')}")
    print(f"  📊 Total potential: ${state['total_revenue_potential']:,}/month")

    save(state)
    return state


if __name__ == "__main__":
    run()
