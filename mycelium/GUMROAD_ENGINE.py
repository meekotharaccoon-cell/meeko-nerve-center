#!/usr/bin/env python3
"""
GUMROAD_ENGINE.py — publishes products to Gumroad automatically
Uses YOUR actual secret names: GUMROAD_SECRET (access token), GUMROAD_ID (seller ID)
Gumroad API: https://app.gumroad.com/api

Secret mapping:
  GUMROAD_SECRET  → access_token (the Bearer token for all API calls)
  GUMROAD_ID      → seller/user ID (optional, used for verification)
  GUMROAD_NAME    → your Gumroad display name
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# YOUR actual secret names
ACCESS_TOKEN = os.environ.get("GUMROAD_SECRET", "")   # ← fixed from GUMROAD_ACCESS_TOKEN
SELLER_ID    = os.environ.get("GUMROAD_ID", "")
SELLER_NAME  = os.environ.get("GUMROAD_NAME", "")

BASE = "https://api.gumroad.com/v2"


def gum(method, path, **kwargs):
    """Make authenticated Gumroad API call."""
    r = requests.request(
        method, f"{BASE}{path}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        timeout=30, **kwargs
    )
    return r


def load_state():
    f = DATA / "gumroad_engine_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"published": [], "failed": [], "cycles": 0, "total_live": 0}


def save_state(s):
    (DATA / "gumroad_engine_state.json").write_text(json.dumps(s, indent=2))


def load_listings():
    """Load queued listings from gumroad_listings.json (created by ART_GENERATOR/BUSINESS_FACTORY)."""
    f = DATA / "gumroad_listings.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"products": []}


def publish_product(product):
    """Create or update a Gumroad product listing."""
    name = product.get("name", "")
    price_cents = int(product.get("price_cents", 100))
    description = product.get("description", "")
    file_url = product.get("file_url", "")      # URL to downloadable file
    preview_url = product.get("preview_url", "") # cover image

    payload = {
        "name": name,
        "price": price_cents,
        "description": description,
        "published": "true",
        "require_shipping": "false",
    }
    if file_url:
        payload["url"] = file_url
    if preview_url:
        payload["preview_url"] = preview_url

    # Check if already published (has existing_id)
    existing_id = product.get("gumroad_id")
    if existing_id:
        r = gum("PUT", f"/products/{existing_id}", data=payload)
        action = "updated"
    else:
        r = gum("POST", "/products", data=payload)
        action = "created"

    if r.status_code in (200, 201):
        data = r.json()
        if data.get("success"):
            prod_data = data.get("product", {})
            return {
                "success": True,
                "action": action,
                "gumroad_id": prod_data.get("id"),
                "gumroad_url": prod_data.get("short_url") or prod_data.get("url"),
                "name": name,
            }
    return {"success": False, "status": r.status_code, "body": r.text[:200], "name": name}


def run():
    print("GUMROAD_ENGINE running...")
    now = datetime.now(timezone.utc).isoformat()

    if not ACCESS_TOKEN:
        print("  ⚠️  GUMROAD_SECRET not set — skipping")
        print("  How to fix: Settings → Advanced → Access Token → copy → GitHub Secrets → GUMROAD_SECRET")
        state = load_state()
        state["last_run"] = now
        state["status"] = "no_token"
        save_state(state)
        return

    # Verify token works
    r = gum("GET", "/user")
    if r.status_code != 200:
        print(f"  ❌ Gumroad auth failed: {r.status_code} — check GUMROAD_SECRET")
        return
    user = r.json().get("user", {})
    print(f"  ✅ Authenticated as: {user.get('name', SELLER_NAME)} ({user.get('email', '')})")

    state = load_state()
    listings = load_listings()
    products = listings.get("products", [])

    published_count = 0
    updated_listings = []

    for product in products:
        # Skip if already live
        if product.get("gumroad_result", {}).get("status") == "live":
            updated_listings.append(product)
            continue

        result = publish_product(product)
        product = dict(product)  # copy

        if result["success"]:
            product["gumroad_result"] = {
                "status": "live",
                "action": result["action"],
                "gumroad_id": result["gumroad_id"],
                "gumroad_url": result["gumroad_url"],
                "published_at": now,
            }
            state["published"].append({
                "name": product["name"],
                "gumroad_id": result["gumroad_id"],
                "url": result["gumroad_url"],
                "ts": now,
            })
            print(f"  ✅ {result['action']}: {product['name']} → {result['gumroad_url']}")
            published_count += 1
        else:
            product["gumroad_result"] = {"status": "error", "detail": result.get("body", ""), "ts": now}
            print(f"  ❌ Failed: {product['name']} — {result.get('body', '')[:80]}")

        updated_listings.append(product)

    # Save updated listings
    listings["products"] = updated_listings
    listings["gumroad_live"] = sum(1 for p in updated_listings if p.get("gumroad_result", {}).get("status") == "live")
    listings["last_run"] = now
    (DATA / "gumroad_listings.json").write_text(json.dumps(listings, indent=2))

    state["cycles"] = state.get("cycles", 0) + 1
    state["total_live"] = listings["gumroad_live"]
    state["last_run"] = now
    save_state(state)

    print(f"  📊 Published this cycle: {published_count} | Total live: {listings['gumroad_live']}/{len(products)}")


if __name__ == "__main__": run()
