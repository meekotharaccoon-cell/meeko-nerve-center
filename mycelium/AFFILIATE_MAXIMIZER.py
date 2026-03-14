# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AFFILIATE_MAXIMIZER.py — Every piece of content = affiliate revenue
====================================================================
Injects Meeko's affiliate links into ALL generated content.
Discovers NEW affiliate programs automatically every 3rd cycle.
Amazon Associates tag: autonomoushum-20 — appended to every Amazon URL.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask, ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DATA = Path("data"); DATA.mkdir(exist_ok=True)

AMAZON_TAG = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")

KNOWN_AFFILIATES = {
    # ★ CONFIRMED — real tags in use
    "amazon":        {"url": f"https://www.amazon.com?tag={AMAZON_TAG}",        "commission": "1-10%",            "type": "retail",       "tag": AMAZON_TAG},
    "ko-fi":         {"url": "https://ko-fi.com/meekotharaccoon",               "commission": "direct",           "type": "donations"},
    "gumroad":       {"url": "https://gumroad.com/?via=meeko",                  "commission": "10%",              "type": "saas"},
    # ★ HIGH VALUE — sign up ASAP
    "hostinger":     {"url": "https://www.hostg.xyz/meeko",                     "commission": "60%",              "type": "hosting"},
    "convertkit":    {"url": "https://convertkit.com/?lmref=meeko",             "commission": "30% recurring",    "type": "email"},
    "beehiiv":       {"url": "https://www.beehiiv.com/?via=meeko",              "commission": "50% first year",   "type": "newsletter"},
    "semrush":       {"url": "https://www.semrush.com/partner/",                "commission": "200% first pay",   "type": "seo"},
    "shopify":       {"url": "https://shopify.pxf.io/meeko",                    "commission": "$150/sale",        "type": "ecommerce"},
    "namecheap":     {"url": "https://namecheap.pxf.io/meeko",                  "commission": "35%",              "type": "domain"},
    # ★ CONTENT TOOLS
    "canva":         {"url": "https://partner.canva.com/meeko",                 "commission": "up to 80%",        "type": "design"},
    "notion":        {"url": "https://affiliate.notion.so/meeko",               "commission": "$10/ref",          "type": "productivity"},
    "fiverr":        {"url": "https://www.fiverr.com/s/meeko",                  "commission": "$100/ref",         "type": "marketplace"},
    "bluehost":      {"url": "https://www.bluehost.com/track/meeko",            "commission": "$65/sale",         "type": "hosting"},
    "coursera":      {"url": "https://coursera.pxf.io/meeko",                   "commission": "up to 45%",        "type": "education"},
    "envato":        {"url": "https://envato.com/refer/meeko",                  "commission": "30%",              "type": "templates"},
    "huggingface":   {"url": "https://huggingface.co",                          "commission": "check program",    "type": "ai"},
}

AMAZON_PRODUCTS = {
    "palestine_sacco":   {"asin": "1560974523", "title": "Palestine — Joe Sacco"},
    "automate_python":   {"asin": "1593279922", "title": "Automate the Boring Stuff"},
    "100_startup":       {"asin": "0307951529", "title": "The $100 Startup"},
    "steal_artist":      {"asin": "0761169253", "title": "Steal Like an Artist"},
    "ways_seeing":       {"asin": "014013515X", "title": "Ways of Seeing"},
    "passive_income":    {"asin": None,         "title": "Passive Income Books",    "search": "passive+income+online"},
    "python_automation": {"asin": None,         "title": "Python Automation",       "search": "python+automation"},
    "palestine_history": {"asin": None,         "title": "Palestine History Books", "search": "palestine+history"},
}

CONTENT_FILES_TO_ENRICH = [
    "substack_draft.txt",
    "social_latest.json",
    "social_queue.json",
    "neuron_a_report.json",
]

def amazon_link(product_key):
    """Generate affiliate Amazon link for a product"""
    p = AMAZON_PRODUCTS.get(product_key, {})
    if p.get("asin"):
        return f"https://www.amazon.com/dp/{p['asin']}?tag={AMAZON_TAG}"
    elif p.get("search"):
        return f"https://www.amazon.com/s?k={p['search']}&tag={AMAZON_TAG}"
    return f"https://www.amazon.com?tag={AMAZON_TAG}"

def load():
    f = DATA / "affiliate_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "links_injected": 0, "new_programs_found": []}

def save(state):
    (DATA / "affiliate_state.json").write_text(json.dumps(state, indent=2))

def discover_new_programs():
    if not AI_AVAILABLE:
        return []
    prompt = """Find the 10 BEST affiliate programs an indie hacker building AI tools should join RIGHT NOW.
Focus on: high %, recurring, easy approval, relevant to tech/AI/productivity audience.
Respond ONLY as JSON array:
[{"tool": "name", "signup_url": "url", "commission": "rate", "why": "one sentence reason"}]"""
    try:
        result = ask_json(prompt, max_tokens=1200)
        return result if isinstance(result, list) else []
    except:
        return []

def inject_links(content_text, context="general"):
    if not AI_AVAILABLE or not content_text or len(content_text) < 100:
        return content_text
    top_links = "\n".join([
        f"  {k}: {v['url']} ({v['commission']})"
        for k, v in list(KNOWN_AFFILIATES.items())[:6]
    ])
    amazon_links = "\n".join([
        f"  {p['title']}: {amazon_link(k)}"
        for k, p in list(AMAZON_PRODUCTS.items())[:4]
    ])
    prompt = f"""Naturally weave 2-3 affiliate links into this content. Organic, helpful, not spammy.
Context: {context}

CONTENT:
{content_text[:1500]}

AFFILIATE LINKS:
{top_links}

AMAZON BOOKS (tag=autonomoushum-20):
{amazon_links}

Rules: links feel helpful, keep Gaza/mission intact, add one-line disclosure.
Return plain text only."""
    try:
        return ask([{"role": "user", "content": prompt}], max_tokens=2000)
    except:
        return content_text

def write_master_config():
    """Write unified affiliate config for all engines to read"""
    config = {
        "amazon_tag": AMAZON_TAG,
        "amazon_base": f"https://www.amazon.com?tag={AMAZON_TAG}",
        "programs": KNOWN_AFFILIATES,
        "amazon_products": {
            k: {**v, "url": amazon_link(k)}
            for k, v in AMAZON_PRODUCTS.items()
        },
        "inject_into_all_content": True,
        "disclosure": "As an Amazon Associate and affiliate partner I earn from qualifying purchases. Commissions fund Gaza aid.",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    (DATA / "affiliate_config.json").write_text(json.dumps(config, indent=2))
    (DATA / "affiliate_links_master.json").write_text(
        json.dumps({k: v["url"] for k, v in KNOWN_AFFILIATES.items()}, indent=2)
    )
    print(f"  💾 Affiliate config written: {len(KNOWN_AFFILIATES)} programs, Amazon tag={AMAZON_TAG}")

def run():
    state = load()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"💸 AFFILIATE_MAXIMIZER cycle {state['cycles']} | Amazon tag: {AMAZON_TAG}")

    # Discover new programs every 3rd cycle
    if state["cycles"] % 3 == 1:
        print("  🔍 Discovering new programs...")
        new = discover_new_programs()
        if new:
            state.setdefault("new_programs_found", []).extend(new)
            state["new_programs_found"] = state["new_programs_found"][-50:]
            (DATA / "new_affiliates_found.json").write_text(json.dumps(new, indent=2))
            print(f"  Found {len(new)} new opportunities")

    # Enrich content files
    enriched = 0
    for fname in CONTENT_FILES_TO_ENRICH:
        fpath = DATA / fname
        if not fpath.exists(): continue
        try:
            if fname.endswith(".txt"):
                content = fpath.read_text()
                if "affiliate" not in content.lower():
                    result = inject_links(content, fname)
                    if result and result != content:
                        (DATA / f"enriched_{fname}").write_text(result)
                        enriched += 1
                        print(f"  ✅ Enriched: {fname}")
        except Exception as e:
            print(f"  Skip {fname}: {e}")

    write_master_config()

    state["links_injected"] = state.get("links_injected", 0) + enriched
    state["programs_active"] = len(KNOWN_AFFILIATES)
    monthly = len(KNOWN_AFFILIATES) * 100 * 0.02 * 20
    state["estimated_monthly_commissions"] = monthly

    save(state)
    print(f"  📈 Commission potential: ${monthly:,.0f}/month")
    return state

if __name__ == "__main__": run()
