#!/usr/bin/env python3
"""
GUMROAD_AUTO_QUEUE.py — Auto-builds gumroad_listings.json from business data

Problem it solves:
  GUMROAD_ENGINE publishes from data/gumroad_listings.json
  But that file might be empty or missing real product content.
  This engine builds complete, ready-to-publish listings for all 4 products.
  Then GUMROAD_ENGINE picks them up and publishes them.

File flow:
  THIS ENGINE > data/gumroad_listings.json > GUMROAD_ENGINE > live on Gumroad
  After publish > real URLs update product landing pages

Secrets: GUMROAD_SECRET (optional — to check what's already live)
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

GUMROAD_SECRET = os.environ.get("GUMROAD_SECRET", "")
GUMROAD_BASE = "https://api.gumroad.com/v2"

PRODUCTS = [
    {
        "id": "ai-prompt-packs",
        "name": "SolarPunk AI Prompt Packs",
        "price_cents": 1700,
        "description": (
            "Premium AI prompt packs built by an autonomous AI revenue system.\n\n"
            "Part of SolarPunk™ — an AI agent that builds and sells digital products "
            "autonomously, with 15% of every sale going to Palestinian children via PCRF.\n\n"
            "🌹 $2.55 of your $17 → PCRF (EIN 93-1057665, 4★ Charity Navigator)\n\n"
            "What you get:\n"
            "• 200+ curated prompts across categories\n"
            "• Claude, GPT-4, Gemini compatible\n"
            "• Organized by use case: business, creative, coding, research\n"
            "• Instant download, no subscription\n\n"
            "Built by SolarPunk™ — an AI that funds Gaza."
        ),
        "landing_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/ai-prompt-packs/",
    },
    {
        "id": "github-actions-templates",
        "name": "SolarPunk GitHub Actions Templates",
        "price_cents": 2700,
        "description": (
            "Complete GitHub Actions workflow templates for autonomous AI revenue systems.\n\n"
            "Everything you need to build a self-running AI business on GitHub Actions — "
            "zero DevOps required.\n\n"
            "Includes:\n"
            "• Revenue automation workflows\n"
            "• Payment webhook handlers (Ko-fi, Gumroad, Stripe)\n"
            "• AI-powered build pipelines\n"
            "• Self-healing engine templates\n"
            "• Complete documentation\n\n"
            "🌹 15% ($4.05) → Gaza via PCRF\n\n"
            "Built by SolarPunk™ — AI infrastructure for autonomous income."
        ),
        "landing_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/github-actions-templates/",
    },
    {
        "id": "notion-templates-freelancers",
        "name": "Notion Templates for Freelancers — AI Edition",
        "price_cents": 1900,
        "description": (
            "AI-optimized Notion templates for freelancers building autonomous income.\n\n"
            "Stop managing projects manually. These templates integrate with AI workflows "
            "to automate client communication, invoicing, and project tracking.\n\n"
            "Includes:\n"
            "• Client relationship tracker\n"
            "• Invoice + payment automation template\n"
            "• AI task manager\n"
            "• Revenue dashboard\n"
            "• Content calendar with auto-scheduling\n\n"
            "🌹 15% ($2.85) → Gaza via PCRF\n\n"
            "Built by SolarPunk™ — Notion + AI = autonomous freelance business."
        ),
        "landing_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/notion-templates-for-freelancers/",
    },
    {
        "id": "gaza-rose-art-pack",
        "name": "Gaza Rose Gallery — 7 Palestinian Art Prints Pack",
        "price_cents": 700,
        "description": (
            "All 7 Gaza Rose Gallery AI-generated Palestinian art prints in one pack.\n\n"
            "Save $0 vs buying individually — or buy individually at $1 each.\n\n"
            "Prints included:\n"
            "🕊️ White Doves Over Gaza\n"
            "🫒 Ancient Olive Grove\n"
            "🧵 Tatreez — Living Embroidery\n"
            "🌊 Gaza by the Sea\n"
            "⭐ Star of Hope\n"
            "🍎 Pomegranate Season\n"
            "🌙 Night Garden of Palestine\n\n"
            "Revenue split: 70% → PCRF (Gaza children) · 30% → Loop Fund\n"
            "PCRF EIN: 93-1057665 · 4★ Charity Navigator · operating since 1991\n\n"
            "Built by SolarPunk™ — AI art that funds Gaza."
        ),
        "landing_url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/art.html",
    }
]


def check_existing_gumroad_products():
    if not GUMROAD_SECRET:
        return {}
    try:
        r = requests.get(
            f"{GUMROAD_BASE}/products",
            headers={"Authorization": f"Bearer {GUMROAD_SECRET}"},
            timeout=30
        )
        if r.status_code == 200 and r.json().get("success"):
            products = r.json().get("products", [])
            return {p.get("name", ""): p for p in products}
    except Exception as ex:
        print(f"  ⚠️  Gumroad check failed: {ex}")
    return {}


def run():
    print("GUMROAD_AUTO_QUEUE running...")
    now = datetime.now(timezone.utc).isoformat()

    lf = DATA / "gumroad_listings.json"
    listings = {"products": [], "last_updated": now}
    if lf.exists():
        try: listings = json.loads(lf.read_text())
        except: pass

    existing_gumroad = check_existing_gumroad_products()
    if existing_gumroad:
        print(f"  📦 Found {len(existing_gumroad)} existing Gumroad products")

    existing_ids = {p.get("id") for p in listings.get("products", [])}
    added, updated = 0, 0

    for product in PRODUCTS:
        pid = product["id"]
        if pid in existing_ids:
            for p in listings["products"]:
                if p.get("id") == pid:
                    for k, v in product.items():
                        if k != "gumroad_result":
                            p[k] = v
            updated += 1
            continue

        listing = dict(product)
        listing["queued_at"] = now
        listing["gumroad_result"] = {"status": "queued"}

        if product["name"] in existing_gumroad:
            gp = existing_gumroad[product["name"]]
            listing["gumroad_id"] = gp.get("id")
            listing["gumroad_result"] = {
                "status": "live",
                "gumroad_id": gp.get("id"),
                "gumroad_url": gp.get("short_url") or gp.get("url"),
                "published_at": now
            }
            print(f"  ✅ Already live: {product['name']}")
        else:
            print(f"  ➕ Queued: {product['name']} (${product['price_cents']/100:.2f})")

        listings["products"].append(listing)
        added += 1

    listings["last_updated"] = now
    listings["total_products"] = len(listings["products"])
    listings["gumroad_live"] = sum(
        1 for p in listings["products"]
        if p.get("gumroad_result", {}).get("status") == "live"
    )

    lf.write_text(json.dumps(listings, indent=2))
    print(f"  📊 Queue: {listings['total_products']} total | {listings['gumroad_live']} live | {added} added | {updated} updated")
    print("  ✅ GUMROAD_ENGINE will publish these next cycle — run RUN_NOW to trigger immediately")

    (DATA / "gumroad_queue_state.json").write_text(json.dumps({
        "last_run": now, "total": listings["total_products"],
        "live": listings["gumroad_live"], "added_this_cycle": added
    }, indent=2))


if __name__ == "__main__": run()
