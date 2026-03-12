#!/usr/bin/env python3
"""
GUMROAD_ENGINE.py v2 — creates AND updates Gumroad products, fixes 404 bug
===========================================================================
BUG v1: PUT /products/{stale_id} for products that don't exist on Gumroad
→ got 404 every cycle → nothing ever published.

FIX v2:
  1. On startup, GET /products from live Gumroad API → build name→id map
  2. Match each queued product by name to find its real ID
  3. If match → PUT update
  4. If no match → POST create
  5. If PUT returns 404 → fallback to POST create
  6. Never skip a product just because it was marked "live" in stale local data
"""
import os, json, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA         = Path("data"); DATA.mkdir(exist_ok=True)
ACCESS_TOKEN = os.environ.get("GUMROAD_SECRET", "").strip()
BASE         = "https://api.gumroad.com/v2"


def gum(method, path, params=None):
    p = dict(params or {})
    p["access_token"] = ACCESS_TOKEN
    if method == "GET":
        url = f"{BASE}{path}?{urllib.parse.urlencode(p)}"
        req = urllib.request.Request(url)
    else:
        data = urllib.parse.urlencode(p).encode()
        req  = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "SolarPunk/2.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get_live_products():
    """Fetch all products from Gumroad. Returns name→id dict."""
    try:
        data = gum("GET", "/products")
        if data.get("success"):
            return {p["name"]: p["id"] for p in data.get("products", [])}
    except Exception as e:
        print(f"  ⚠️  Could not fetch live products: {e}")
    return {}


def publish_product(product, live_map):
    name        = product.get("name", "")
    price_cents = int(product.get("price_cents", 100))
    description = product.get("description", "")

    params = {
        "name":             name,
        "price":            str(price_cents),
        "description":      description,
        "published":        "true",
        "require_shipping": "false",
    }
    if product.get("file_url"):    params["url"]         = product["file_url"]
    if product.get("preview_url"): params["preview_url"] = product["preview_url"]

    # Use live ID from Gumroad API (not stale local data)
    gid = live_map.get(name) or product.get("gumroad_id") or product.get("gumroad_result", {}).get("gumroad_id")

    try:
        if gid:
            try:
                data   = gum("PUT", f"/products/{gid}", params)
                action = "updated"
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Stale ID — product was deleted on Gumroad, recreate
                    data   = gum("POST", "/products", params)
                    action = "recreated"
                else:
                    raise
        else:
            data   = gum("POST", "/products", params)
            action = "created"
    except Exception as e:
        return {"success": False, "name": name, "error": str(e)}

    if data.get("success"):
        prod = data.get("product", {})
        return {
            "success":    True,
            "name":       name,
            "action":     action,
            "gumroad_id": prod.get("id"),
            "url":        prod.get("short_url") or prod.get("url"),
        }
    return {"success": False, "name": name, "error": str(data)[:200]}


def run():
    print("GUMROAD_ENGINE v2 running...")
    now = datetime.now(timezone.utc).isoformat()

    if not ACCESS_TOKEN:
        print("  ⚠️  GUMROAD_SECRET not set")
        print("  Fix: gumroad.com → Settings → Advanced → Applications → Generate Token")
        return {"status": "no_token"}

    # Verify auth
    try:
        user_data = gum("GET", "/user")
        if not user_data.get("success"):
            print(f"  ❌ GUMROAD_SECRET invalid: {user_data}")
            return {"status": "auth_failed"}
        print(f"  ✅ Gumroad auth OK — {user_data.get('user', {}).get('email', '?')}")
    except Exception as e:
        print(f"  ❌ API error: {e}")
        return {"status": f"error: {e}"}

    # Fetch live products — this is the fix
    live_map = get_live_products()
    print(f"  Live on Gumroad: {len(live_map)} products")

    f = DATA / "gumroad_listings.json"
    listings = {"products": []}
    if f.exists():
        try: listings = json.loads(f.read_text())
        except: pass

    products  = listings.get("products", [])
    published = 0
    updated   = []

    for product in products:
        name        = product.get("name", "")
        prev_result = product.get("gumroad_result", {})

        # Skip only if BOTH marked live AND confirmed in live Gumroad map
        if prev_result.get("status") == "live" and name in live_map:
            updated.append(product)
            continue

        result  = publish_product(product, live_map)
        product = dict(product)

        if result["success"]:
            product["gumroad_result"] = {
                "status":       "live",
                "action":       result["action"],
                "gumroad_id":   result["gumroad_id"],
                "gumroad_url":  result["url"],
                "published_at": now,
            }
            product["gumroad_id"] = result["gumroad_id"]
            live_map[name] = result["gumroad_id"]
            print(f"  ✅ {result['action']}: {name} → {result['url']}")
            published += 1
        else:
            product["gumroad_result"] = {"status": "error", "error": result.get("error", "")[:200], "ts": now}
            print(f"  ❌ Failed: {name} — {result.get('error', '')[:80]}")

        updated.append(product)

    live_count             = sum(1 for p in updated if p.get("gumroad_result", {}).get("status") == "live")
    listings["products"]   = updated
    listings["gumroad_live"] = live_count
    listings["last_run"]   = now
    f.write_text(json.dumps(listings, indent=2))

    # Update state
    sf = DATA / "gumroad_engine_state.json"
    state = {"cycles": 0, "total_live": 0, "published": [], "last_run": now, "status": "ok"}
    if sf.exists():
        try:
            old = json.loads(sf.read_text())
            state["cycles"]    = old.get("cycles", 0) + 1
            state["published"] = old.get("published", [])
        except: pass
    state["total_live"] = live_count
    if published > 0:
        state["published"].append({"count": published, "ts": now})
    sf.write_text(json.dumps(state, indent=2))

    print(f"  📊 Published this cycle: {published} | Total live: {live_count}/{len(products)}")
    return state


if __name__ == "__main__":
    run()
