#!/usr/bin/env python3
"""
GUMROAD_ENGINE.py — Zero-Cost Digital Product Listings
Gumroad charges 10% per sale — zero upfront. Perfect for $1 art prints.
If GUMROAD_ACCESS_TOKEN set → auto-creates product listings via API.
Always generates data/gumroad_listings.json.

SolarPunk: Every new listing is a new door. Open 6 doors every cycle.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

API_KEY              = os.environ.get("ANTHROPIC_API_KEY", "")
GUMROAD_ACCESS_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
SHOP_URL             = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
DATA                 = Path("data")
DATA.mkdir(exist_ok=True)

PRODUCT_CATALOG = [
    {
        "name": "Desert Rose at Dawn — Gaza Rose Gallery",
        "price": 100,
        "description": """🌹 AI-generated digital art print — instant download.

YOUR PURCHASE SPLITS AUTOMATICALLY:
• 70¢ → Gaza Rose Gallery (Palestinian artist relief)
• 30¢ → SolarPunk Loop Fund (auto-buys the next piece)

The loop never stops. Your $1 echoes forever.

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI — print any size)
• Instant download after payment
• Personal & commercial use license

Impressionist style. Warm rose and ochre palette.
A desert bloom at first light — fragile, inevitable, alive.""",
        "theme": "Desert rose, golden hour, impressionist"
    },
    {
        "name": "White Doves Over the Mediterranean — Gaza Rose Gallery",
        "price": 100,
        "description": """🕊️ AI-generated digital art print — instant download.

70% of your $1 goes directly to Gaza Rose Gallery.

• 70¢ → Gaza Rose Gallery (Palestinian artist relief)
• 30¢ → SolarPunk Loop Fund

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI)
• Instant download • Full license

Dreamlike style. Deep Mediterranean blue. A symbol of return.""",
        "theme": "Doves, Mediterranean sea, dreamlike"
    },
    {
        "name": "Olive Grove Eternal — Gaza Rose Gallery",
        "price": 100,
        "description": """🌿 Ancient roots. AI-generated digital art — instant download.

70% of every sale to Gaza Rose Gallery.

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI)
• Instant download • Full license

Painterly style. Deep greens, silver leaves, afternoon light.""",
        "theme": "Olive trees, Palestinian landscape, painterly"
    },
    {
        "name": "Tatreez Pattern Bloom — Gaza Rose Gallery",
        "price": 100,
        "description": """🌸 Palestinian embroidery pattern, reimagined. AI art — instant download.

Tatreez is memory made visible. 70% to Gaza Rose Gallery.

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI)
• Instant download • Full license

Geometric style. Red, black, and gold. Living pattern.""",
        "theme": "Tatreez embroidery, geometric, cultural"
    },
    {
        "name": "Gaza Coastline at Golden Hour — Gaza Rose Gallery",
        "price": 100,
        "description": """🌅 The coast that remains. AI-generated digital art — instant download.

70% to Gaza Rose Gallery.

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI)
• Instant download • Full license

Landscape style. Warm golds, deep blues, horizon.""",
        "theme": "Coastline, golden hour, landscape"
    },
    {
        "name": "Star of Hope Rising — Gaza Rose Gallery",
        "price": 100,
        "description": """⭐ Light through dark. AI-generated digital art — instant download.

A single star. 70% to Gaza Rose Gallery.

WHAT YOU GET:
• 4000 x 4000px JPEG (300 DPI)
• Instant download • Full license

Symbolic style. Dark sky, single point of light, rising.""",
        "theme": "Star, hope, symbolic, minimal"
    },
]

def create_gumroad_product(product):
    if not GUMROAD_ACCESS_TOKEN:
        return {"status": "no_token"}
    try:
        r = requests.post("https://api.gumroad.com/v2/products",
            data={"access_token": GUMROAD_ACCESS_TOKEN, "name": product["name"],
                  "price": product["price"], "description": product["description"],
                  "url": SHOP_URL, "published": True, "require_shipping": False}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return {"status": "created", "id": data.get("product", {}).get("id"),
                    "short_url": data.get("product", {}).get("short_url")}
        return {"status": "failed", "code": r.status_code}
    except Exception as ex:
        return {"status": "error", "msg": str(ex)}

def run():
    listings_file = DATA / "gumroad_listings.json"
    existing = json.loads(listings_file.read_text()) if listings_file.exists() else {"cycles": 0, "products": []}
    existing["cycles"] = existing.get("cycles", 0) + 1
    existing["last_run"] = datetime.now(timezone.utc).isoformat()
    products_out = []
    existing_ids = {p["name"]: p for p in existing.get("products", [])}
    print(f"GUMROAD_ENGINE cycle {existing['cycles']} | {len(PRODUCT_CATALOG)} products")
    for product in PRODUCT_CATALOG:
        if product["name"] in existing_ids and existing_ids[product["name"]].get("gumroad_id"):
            products_out.append(existing_ids[product["name"]])
            print(f"  ✓ Existing: {product['name'][:45]}...")
            continue
        result = create_gumroad_product(product)
        entry = {"name": product["name"], "price_cents": product["price"],
                 "description": product["description"],
                 "created_at": datetime.now(timezone.utc).isoformat(), "gumroad_result": result}
        if result.get("status") == "created":
            entry["gumroad_id"] = result["id"]
            entry["gumroad_url"] = result["short_url"]
            print(f"  🟢 Created: {product['name'][:45]} → {result.get('short_url','?')}")
        else:
            print(f"  📋 Queued: {product['name'][:45]} ({result.get('status','?')})")
        products_out.append(entry)
    existing["products"] = products_out
    existing["gumroad_live"] = sum(1 for p in products_out if p.get("gumroad_id"))
    existing["setup_instructions"] = {
        "step1": "Go to https://gumroad.com/signup — free account",
        "step2": "Settings → Advanced → Copy your Access Token",
        "step3": "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets",
        "note": "10% Gumroad fee. $1 sale = 90¢ then 70/30 split."
    }
    listings_file.write_text(json.dumps(existing, indent=2))
    print(f"\nGUMROAD: {existing['gumroad_live']} live | {len(products_out) - existing['gumroad_live']} queued")
    if not GUMROAD_ACCESS_TOKEN:
        print("  → Add GUMROAD_ACCESS_TOKEN secret to auto-create listings")
    return existing

if __name__ == "__main__":
    run()
