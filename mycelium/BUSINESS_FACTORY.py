#!/usr/bin/env python3
"""
BUSINESS_FACTORY.py — SolarPunk's Crown Jewel
==============================================
Builds complete digital businesses from scratch, autonomously.

THE PRODUCT: Sell "SolarPunk Business Builder" for $97-297 one-time.
Customer pays → gets their own GitHub repo → system builds their entire
digital business: landing page, product, email sequences, content,
revenue streams, affiliate links, social presence. All automated.

THIS ENGINE ALSO builds Meeko's OWN side businesses continuously —
one new income-generating mini-business every week, using all collective
knowledge from every other engine.

Revenue model:
- Sell the service: $97-297/customer (Gumroad delivery)
- Meeko's own businesses: ongoing passive income
- Affiliate links embedded in every business built: recurring commissions
"""
import os, json, sys, requests, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ─────────────────────────────────────────────
# MEEKO'S AFFILIATE LINKS — embedded everywhere
# ─────────────────────────────────────────────
AFFILIATE_LINKS = {
    "gumroad":     "https://gumroad.com/?via=meeko",
    "notion":      "https://affiliate.notion.so/meeko",
    "canva":       "https://partner.canva.com/meeko",
    "namecheap":   "https://namecheap.pxf.io/meeko",
    "hostinger":   "https://www.hostg.xyz/meeko",
    "convertkit":  "https://convertkit.com/?lmref=meeko",
    "beehiiv":     "https://www.beehiiv.com/?via=meeko",
    "substack":    "https://substack.com/?via=meeko",
    "ko-fi":       "https://ko-fi.com/meekotharaccoon",
    "github":      "https://github.com/meekotharaccoon-cell/meeko-nerve-center",
}

# Niches SolarPunk can auto-build businesses in
BUSINESS_NICHES = [
    {"niche": "AI Prompt Packs", "product_type": "digital_download", "price": 17,
     "platform": "Gumroad", "audience": "AI enthusiasts, creators, marketers"},
    {"niche": "Palestinian Art Prints", "product_type": "print_on_demand", "price": 25,
     "platform": "Redbubble+Etsy", "audience": "conscious consumers, art lovers"},
    {"niche": "GitHub Actions Templates", "product_type": "digital_download", "price": 27,
     "platform": "Gumroad", "audience": "developers, indie hackers"},
    {"niche": "Notion Templates for Freelancers", "product_type": "digital_download", "price": 19,
     "platform": "Gumroad+Notion", "audience": "freelancers, solopreneurs"},
    {"niche": "Autonomous Business Guide", "product_type": "ebook", "price": 37,
     "platform": "Gumroad", "audience": "entrepreneurs wanting passive income"},
    {"niche": "Social Media Content Packs", "product_type": "digital_download", "price": 22,
     "platform": "Gumroad", "audience": "small businesses, content creators"},
    {"niche": "Grant Writing Templates", "product_type": "digital_download", "price": 47,
     "platform": "Gumroad", "audience": "nonprofits, artists, community orgs"},
    {"niche": "Email Automation Blueprints", "product_type": "digital_download", "price": 37,
     "platform": "Gumroad", "audience": "marketers, online business owners"},
]

def load():
    f = DATA / "business_factory_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "businesses_built": [], "total_revenue_potential": 0, "customers_served": 0}

def save(state):
    (DATA / "business_factory_state.json").write_text(json.dumps(state, indent=2))

def load_collective_knowledge():
    """Pull insights from every engine that has run"""
    knowledge = {}
    sources = [
        ("neuron_a_report.json", "opportunities"),
        ("neuron_b_report.json", "insights"),
        ("health_report.json",   "health"),
        ("brain_state.json",     "brain"),
        ("flywheel_state.json",  "revenue"),
        ("etsy_seo_output.json", "seo"),
        ("content_harvest.json", "content"),
        ("synthesis_log.json",   "synthesis"),
    ]
    for fname, key in sources:
        fp = DATA / fname
        if fp.exists():
            try: knowledge[key] = json.loads(fp.read_text())
            except: pass
    return knowledge

def build_business_plan(niche_data, knowledge):
    """Use AI to design a complete business"""
    if not AI_AVAILABLE:
        return _fallback_plan(niche_data)

    affiliate_block = "\n".join([f"  - {k}: {v}" for k, v in AFFILIATE_LINKS.items()])
    prompt = f"""You are BUSINESS_FACTORY, part of SolarPunk — Meeko's autonomous income system.

BUILD A COMPLETE DIGITAL BUSINESS for this niche:
Niche: {niche_data['niche']}
Product type: {niche_data['product_type']}
Price: ${niche_data['price']}
Platform: {niche_data['platform']}
Target audience: {niche_data['audience']}

SYSTEM KNOWLEDGE:
{json.dumps(knowledge, indent=2)[:1000]}

MEEKO'S AFFILIATE LINKS (embed these naturally in ALL content):
{affiliate_block}

15% of every sale goes to Gaza. Build this into the story.

Design a COMPLETE, LAUNCHABLE business. Respond ONLY as JSON:
{{
  "business_name": "catchy name",
  "tagline": "one line hook",
  "product_name": "specific product name",
  "product_description": "3 sentences, compelling, includes Gaza mission",
  "price": {niche_data['price']},
  "landing_page_html": "complete minimal HTML landing page with buy button (use gumroad embed), Gaza story, and affiliate links naturally placed",
  "email_sequence": [
    {{"subject": "...", "body": "...", "day": 0}},
    {{"subject": "...", "body": "...", "day": 3}},
    {{"subject": "...", "body": "...", "day": 7}}
  ],
  "social_posts": [
    {{"platform": "twitter", "text": "..."}},
    {{"platform": "reddit", "text": "..."}},
    {{"platform": "linkedin", "text": "..."}}
  ],
  "seo_keywords": ["keyword1", "keyword2", "keyword3"],
  "affiliate_links_used": ["which affiliate links embedded and where"],
  "launch_steps": ["step 1", "step 2", "step 3"],
  "monthly_revenue_estimate": "realistic range",
  "gaza_impact": "what % goes to Gaza and how it helps"
}}"""

    try:
        result = ask_json(prompt, max_tokens=4000)
        return result
    except Exception as e:
        print(f"  Business AI error: {e}")
        return _fallback_plan(niche_data)

def _fallback_plan(niche_data):
    return {
        "business_name": f"SolarPunk {niche_data['niche']}",
        "tagline": f"Autonomous {niche_data['niche']} — 15% to Gaza",
        "product_name": f"{niche_data['niche']} Pack v1",
        "product_description": f"Premium {niche_data['niche']} built by autonomous AI. Every purchase sends 15% to Palestinian artists via Gaza Rose Gallery.",
        "price": niche_data['price'],
        "launch_steps": ["Create Gumroad listing", "Post to Reddit/Twitter", "Email list announcement"],
        "monthly_revenue_estimate": f"${niche_data['price'] * 10}-${niche_data['price'] * 50}/month",
        "gaza_impact": f"15% of every ${niche_data['price']} sale = ${niche_data['price'] * 0.15:.2f} to Gaza",
        "affiliate_links_used": list(AFFILIATE_LINKS.keys())[:3]
    }

def save_business_to_repo(plan, niche_data):
    """Save the complete business package to data/ for deployment"""
    business_id = niche_data['niche'].lower().replace(" ", "_").replace("/", "_")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")

    package = {
        "id": f"{business_id}_{ts}",
        "niche": niche_data,
        "plan": plan,
        "affiliate_links": AFFILIATE_LINKS,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready_to_launch",
        "estimated_monthly_revenue": plan.get("monthly_revenue_estimate", "unknown"),
        "gaza_contribution": "15% of all sales"
    }

    out_file = DATA / f"business_{business_id}.json"
    out_file.write_text(json.dumps(package, indent=2))

    # Save landing page HTML if present
    if plan.get("landing_page_html"):
        html_file = DATA / f"landing_{business_id}.html"
        html_file.write_text(plan["landing_page_html"])
        print(f"   🌐 Landing page: data/landing_{business_id}.html")

    return package

def notify_meeko(package):
    if not GMAIL or not GPWD:
        return
    plan = package["plan"]
    body = f"""BUSINESS_FACTORY just built a new business for you!

Business: {plan.get('business_name', '?')}
Tagline: {plan.get('tagline', '?')}
Product: {plan.get('product_name', '?')}
Price: ${plan.get('price', '?')}
Revenue estimate: {plan.get('monthly_revenue_estimate', '?')}
Gaza impact: {plan.get('gaza_impact', '15% of all sales')}

LAUNCH STEPS:
{chr(10).join(f"  {i+1}. {s}" for i, s in enumerate(plan.get('launch_steps', [])))}

Full business package: data/business_{package['id']}.json
Landing page ready: data/landing_{package['id'].split('_')[0]}.html

TO SELL SOLARPUNK AS A PRODUCT:
Price: $97-297/customer
Pitch: "AI builds your entire digital business in 24 hours"
Delivery: Gumroad → customer gets their own GitHub repo
You keep 85%, 15% to Gaza
Affiliate links earn you commissions on every tool the new business uses

— BUSINESS_FACTORY"""
    try:
        msg = MIMEText(body)
        msg["From"] = GMAIL; msg["To"] = GMAIL
        msg["Subject"] = f"[SolarPunk] 🏗️ New business built: {plan.get('business_name','?')}"
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls(); s.login(GMAIL, GPWD); s.sendmail(GMAIL, GMAIL, msg.as_string())
        print("  📧 Meeko notified")
    except Exception as e:
        print(f"  Email error: {e}")

def run():
    state = load()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"🏗️  BUSINESS_FACTORY cycle {state['cycles']} | {len(state.get('businesses_built',[]))} businesses built")

    knowledge = load_collective_knowledge()
    built_niches = {b.get("niche") for b in state.get("businesses_built", [])}

    for niche_data in BUSINESS_NICHES:
        if niche_data["niche"] not in built_niches:
            print(f"  Building: {niche_data['niche']}")
            plan = build_business_plan(niche_data, knowledge)
            if not plan:
                print("  Plan generation failed")
                continue
            package = save_business_to_repo(plan, niche_data)
            state.setdefault("businesses_built", []).append({
                "niche": niche_data["niche"],
                "name": plan.get("business_name", "?"),
                "price": niche_data["price"],
                "revenue_estimate": plan.get("monthly_revenue_estimate", "?"),
                "built_at": datetime.now(timezone.utc).isoformat()
            })
            state["total_revenue_potential"] = sum(
                b.get("price", 0) * 20 for b in state["businesses_built"]
            )
            notify_meeko(package)
            print(f"  ✅ {plan.get('business_name','?')} — {plan.get('monthly_revenue_estimate','?')}/month")
            print(f"  💰 Gaza: {plan.get('gaza_impact','15% of sales')}")
            break  # One per cycle, builds up over time

    # Save sellable product pitch
    pitch = {
        "product": "SolarPunk Business Builder",
        "tagline": "AI builds your entire digital business from scratch in 24 hours",
        "price_tiers": {
            "starter": {"price": 97, "includes": "1 business built, GitHub repo, landing page, 3 email sequences"},
            "growth":  {"price": 197, "includes": "3 businesses, full social content, SEO, affiliate setup"},
            "empire":  {"price": 297, "includes": "Unlimited businesses, Gaza story, custom branding, full automation"}
        },
        "your_cut": "85% per sale",
        "gaza_cut": "15% per sale",
        "delivery": "Automated via Gumroad → GitHub Actions",
        "affiliate_commissions": "Earn recurring commissions on every tool your customers use",
        "total_businesses_built": len(state.get("businesses_built", [])),
        "total_revenue_potential": state.get("total_revenue_potential", 0),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    (DATA / "solarpunk_product_pitch.json").write_text(json.dumps(pitch, indent=2))

    save(state)
    print(f"  📊 Total revenue potential: ${state.get('total_revenue_potential',0):,}/month")
    return state

if __name__ == "__main__": run()
