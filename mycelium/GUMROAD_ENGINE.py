#!/usr/bin/env python3
"""
GUMROAD_ENGINE.py — publishes products to Gumroad automatically

FIXED: Gumroad API v2 uses access_token as a QUERY PARAM / FORM FIELD,
NOT as a Bearer Authorization header. The old version was sending it wrong
which caused every call to return 401 even with a valid token.

Secret: GUMROAD_SECRET → your Gumroad access token
How to get: gumroad.com → Settings → Advanced → Applications → Generate Token
"""
import os, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

ACCESS_TOKEN = os.environ.get("GUMROAD_SECRET", "").strip()
SELLER_NAME  = os.environ.get("GUMROAD_NAME", "")

BASE = "https://api.gumroad.com/v2"


def gum_get(path):
    """GET — access_token as query param (correct Gumroad auth method)."""
    url = f"{BASE}{path}?access_token={urllib.parse.quote(ACCESS_TOKEN)}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "SolarPunk/1.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def gum_post(path, params):
    """POST — access_token in form body (correct Gumroad auth method)."""
    params = dict(params)
    params["access_token"] = ACCESS_TOKEN
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "SolarPunk/1.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def gum_put(path, params):
    """PUT — access_token in form body."""
    params = dict(params)
    params["access_token"] = ACCESS_TOKEN
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="PUT")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "SolarPunk/1.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def load_state():
    f = DATA / "gumroad_engine_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"published": [], "failed": [], "cycles": 0, "total_live": 0}


def save_state(s):
    (DATA / "gumroad_engine_state.json").write_text(json.dumps(s, indent=2))


def load_listings():
    f = DATA / "gumroad_listings.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"products": []}


def publish_product(product):
    name        = product.get("name", "")
    price_cents = int(product.get("price_cents", 100))
    description = product.get("description", "")
    existing_id = product.get("gumroad_id")

    params = {
        "name":             name,
        "price":            str(price_cents),
        "description":      description,
        "published":        "true",
        "require_shipping": "false",
    }
    if product.get("file_url"):    params["url"]         = product["file_url"]
    if product.get("preview_url"): params["preview_url"] = product["preview_url"]

    try:
        if existing_id:
            data   = gum_put(f"/products/{existing_id}", params)
            action = "updated"
        else:
            data   = gum_post("/products", params)
            action = "created"
    except Exception as e:
        return {"success": False, "name": name, "body": str(e)}

    if data.get("success"):
        prod = data.get("product", {})
        return {
            "success":    True,
            "action":     action,
            "gumroad_id": prod.get("id"),
            "gumroad_url": prod.get("short_url") or prod.get("url"),
            "name":       name,
        }
    return {"success": False, "name": name, "body": str(data)[:200]}


def run():
    print("GUMROAD_ENGINE running...")
    now   = datetime.now(timezone.utc).isoformat()
    state = load_state()

    if not ACCESS_TOKEN:
        print("  ⚠️  GUMROAD_SECRET not set — skipping")
        print("  Fix: gumroad.com → Settings → Advanced → Applications → Generate Token")
        state.update({"last_run": now, "status": "no_token"})
        save_state(state)
        return

    # Verify token with live API call
    try:
        data = gum_get("/user")
        if not data.get("success"):
            print(f"  ❌ GUMROAD_SECRET rejected by Gumroad: {data}")
            print(f"  Fix: gumroad.com → Settings → Advanced → Applications → Generate Token → copy entire token")
            state.update({"last_run": now, "status": "auth_failed"})
            save_state(state)
            return
        user = data.get("user", {})
        print(f"  ✅ Gumroad auth OK — {user.get('email', SELLER_NAME)}")
    except Exception as e:
        print(f"  ❌ Gumroad API error: {e}")
        state.update({"last_run": now, "status": f"api_error: {e}"})
        save_state(state)
        return

    listings = load_listings()
    products = listings.get("products", [])
    published_count  = 0
    updated_listings = []

    for product in products:
        if product.get("gumroad_result", {}).get("status") == "live":
            updated_listings.append(product)
            continue

        result  = publish_product(product)
        product = dict(product)

        if result["success"]:
            product["gumroad_result"] = {
                "status":      "live",
                "action":      result["action"],
                "gumroad_id":  result["gumroad_id"],
                "gumroad_url": result["gumroad_url"],
                "published_at": now,
            }
            state["published"].append({
                "name":       product["name"],
                "gumroad_id": result["gumroad_id"],
                "url":        result["gumroad_url"],
                "ts":         now,
            })
            print(f"  ✅ {result['action']}: {product['name']} → {result['gumroad_url']}")
            published_count += 1
        else:
            product["gumroad_result"] = {"status": "error", "detail": result.get("body", ""), "ts": now}
            print(f"  ❌ Failed: {product['name']} — {result.get('body', '')[:80]}")

        updated_listings.append(product)

    listings["products"]    = updated_listings
    listings["gumroad_live"] = sum(1 for p in updated_listings if p.get("gumroad_result", {}).get("status") == "live")
    listings["last_run"]    = now
    (DATA / "gumroad_listings.json").write_text(json.dumps(listings, indent=2))

    state["cycles"]    = state.get("cycles", 0) + 1
    state["total_live"] = listings["gumroad_live"]
    state["last_run"]  = now
    state["status"]    = "ok"
    save_state(state)

    print(f"  📊 Published this cycle: {published_count} | Total live: {listings['gumroad_live']}/{len(products)}")


if __name__ == "__main__": run()
