#!/usr/bin/env python3
"""
GUMROAD_PRODUCT_PUBLISHER.py — autonomous Gumroad listing manager
=================================================================
Creates and maintains ALL product listings on Gumroad via API.

TOKEN PRIORITY (uses whatever is available):
  1. GUMROAD_SECRET  ← already in your secrets, this IS the access token
  2. GUMROAD_ACCESS_TOKEN ← if you ever add this separately

GUMROAD_ID   = your Gumroad user ID (already in secrets)
GUMROAD_NAME = your Gumroad username/slug (already in secrets)

This engine handles everything autonomously:
  - Creates listings for all products (guides + all 8 Gaza Rose prints)
  - Updates descriptions with real download URLs
  - Sets prices, titles, descriptions autonomously
  - Publishes new products as they're generated
  - Falls back gracefully if API is unavailable
"""
import os, json, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

# Try multiple token env vars — GUMROAD_SECRET is already set and IS the access token
TOKEN = (
    os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip() or
    os.environ.get("GUMROAD_SECRET", "").strip()
)
GUMROAD_NAME = os.environ.get("GUMROAD_NAME", "meekotharaccoon").strip()
GUMROAD_ID   = os.environ.get("GUMROAD_ID", "").strip()
API = "https://api.gumroad.com/v2"


def gumroad(method, endpoint, params=None):
    url  = f"{API}{endpoint}"
    p    = dict(params or {})
    p["access_token"] = TOKEN
    if method in ("POST", "PUT", "PATCH"):
        data = urllib.parse.urlencode(p).encode()
        req  = urllib.request.Request(url, data=data, method=method, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SolarPunk-GumroadPublisher/3.0",
        })
    else:
        qs  = urllib.parse.urlencode(p)
        req = urllib.request.Request(f"{url}?{qs}", method=method,
            headers={"User-Agent": "SolarPunk-GumroadPublisher/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        return None, f"HTTP {e.code}: {body}"
    except Exception as e:
        return None, str(e)[:80]


def verify_auth():
    result, err = gumroad("GET", "/user")
    if result and result.get("success"):
        return result.get("user", {}), None
    return None, err


def list_products():
    result, err = gumroad("GET", "/products")
    if result and result.get("success"):
        return {p["name"]: p for p in result.get("products", [])}, None
    return {}, err


def create_product(name, price_cents, description):
    result, err = gumroad("POST", "/products", {
        "name": name, "price": price_cents, "description": description,
    })
    if result and result.get("success"):
        return result["product"], None
    return None, err


def update_product(gid, name, price_cents, description):
    result, err = gumroad("PUT", f"/products/{gid}", {
        "name": name, "price": price_cents, "description": description,
    })
    if result and result.get("success"):
        return result["product"], None
    # If 404, product was deleted — recreate
    if "404" in str(err):
        return create_product(name, price_cents, description)
    return None, err


def make_url(product):
    """Build the Gumroad product URL."""
    permalink = product.get("custom_permalink") or product.get("id", "")
    return f"https://{GUMROAD_NAME}.gumroad.com/l/{permalink}"


def build_description(spec, download_url=None):
    """Build product description with Gaza split info and download URL."""
    gaza_pct  = spec.get("gaza_split_pct", 15)
    price     = spec.get("price_usd", 1.0)
    pages     = spec.get("target_pages", 0)
    tagline   = spec.get("tagline", spec.get("title", ""))

    lines = [tagline, ""]

    if pages:
        lines.append(f"**{pages} pages** of real, actionable content — written by AI, no filler.")
        lines.append("")

    if download_url:
        lines.append(f"📥 **Your download:** {download_url}")
        lines.append("Direct link — no login, no expiry. Works forever. Bookmark it.")
    else:
        lines.append("📥 **Instant download** — delivered to your email automatically after purchase.")
    lines.append("")

    # Gaza split
    gaza_amt = price * gaza_pct / 100
    if gaza_pct == 70:
        lines.append(f"🌹 **{gaza_pct}% of your purchase (${gaza_amt:.2f}) → Gaza children via PCRF**")
    else:
        lines.append(f"🌹 **{gaza_pct}% of your purchase → Gaza children via PCRF**")
    lines.append("PCRF EIN: 93-1057665 · 4★ Charity Navigator · Operating in Gaza since 1991")
    lines.append("Verify: charitynavigator.org/ein/931057665")
    lines.append("")
    lines.append("---")
    lines.append("**About SolarPunk™**")
    lines.append("This product was built by SolarPunk — an autonomous AI revenue system.")
    lines.append("Every purchase funds Palestinian children and keeps the system running.")
    lines.append("")
    lines.append(f"🏪 Full store: https://meekotharaccoon-cell.github.io/meeko-nerve-center/shop.html")
    lines.append(f"✅ Proof ledger: https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html")
    lines.append(f"💻 Source: https://github.com/meekotharaccoon-cell/meeko-nerve-center")
    return "\n".join(lines)


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nGUMROAD_PRODUCT_PUBLISHER v3 — {ts}")

    if not TOKEN:
        print("  BLOCKED: No Gumroad token found.")
        print("  Expected: GUMROAD_SECRET or GUMROAD_ACCESS_TOKEN in GitHub Secrets")
        print("  GUMROAD_SECRET is already in your secrets — check if it's the API access token")
        print("  (It should be from: gumroad.com/settings/advanced → API)")
        return {"status": "no_token"}

    # Verify auth
    user, err = verify_auth()
    if not user:
        print(f"  AUTH FAILED: {err}")
        print("  NOTE: GUMROAD_SECRET may be a webhook secret, not an API access token.")
        print("  Webhook secrets start with 'whsec_' or similar — API tokens are different.")
        print("  To get API token: gumroad.com/settings/advanced → scroll to 'Applications'")
        # Write clear instructions
        (DATA / "gumroad_auth_failure.json").write_text(json.dumps({
            "ts": ts, "error": str(err)[:200],
            "note": "GUMROAD_SECRET may be a webhook secret. API access token is different.",
            "how_to_fix": [
                "Go to gumroad.com/settings/advanced",
                "Find 'Applications' or 'API' section",
                "Generate an access token (looks like: xxxxxxxxxxxxxxxxx)",
                "Add to GitHub Secrets as GUMROAD_ACCESS_TOKEN",
                "The GUMROAD_SECRET (webhook secret) is a different thing"
            ]
        }, indent=2))
        return {"status": "auth_failed", "error": str(err)[:100]}

    print(f"  ✓ Auth OK — {user.get('email', user.get('name', 'user'))}")

    # Load data
    reg_path  = DATA / "product_registry.json"
    dir_path  = DATA / "system_directive.json"
    registry  = json.loads(reg_path.read_text()).get("products", {}) if reg_path.exists() else {}
    directive = json.loads(dir_path.read_text()) if dir_path.exists() else {}
    canonical = directive.get("product_line_canonical", [])

    if not canonical:
        print("  No canonical products in system_directive.json")
        return {"status": "no_products"}

    # Get existing Gumroad products
    existing, err = list_products()
    print(f"  Live on Gumroad: {len(existing)} products")

    results = []
    for spec in canonical:
        pid       = spec["id"]
        title     = spec["title"]
        price_c   = int(spec["price_usd"] * 100)
        dl_url    = registry.get(pid, {}).get("download_url")
        desc      = build_description(spec, dl_url)

        if title in existing:
            gp    = existing[title]
            prod, err = update_product(gp["id"], title, price_c, desc)
            if prod:
                url = make_url(prod)
                registry.setdefault(pid, {})["gumroad_url"] = url
                print(f"  ↻ UPDATED: {title[:45]}")
                results.append({"id": pid, "status": "updated", "url": url})
            else:
                print(f"  ✗ UPDATE FAIL {pid}: {str(err)[:60]}")
                results.append({"id": pid, "status": "error", "error": str(err)[:60]})
        else:
            prod, err = create_product(title, price_c, desc)
            if prod:
                url = make_url(prod)
                registry.setdefault(pid, {}).update({
                    "gumroad_url": url,
                    "gumroad_id":  prod.get("id"),
                })
                print(f"  ✓ CREATED: {title[:45]} → {url}")
                results.append({"id": pid, "status": "created", "url": url})
            else:
                print(f"  ✗ CREATE FAIL {pid}: {str(err)[:60]}")
                results.append({"id": pid, "status": "error", "error": str(err)[:60]})

    # Save updated registry
    if reg_path.exists():
        full = json.loads(reg_path.read_text())
        full["products"]     = registry
        full["last_updated"] = ts
        reg_path.write_text(json.dumps(full, indent=2))
    else:
        reg_path.write_text(json.dumps({"products": registry, "last_updated": ts}, indent=2))

    ok = sum(1 for r in results if r["status"] in ("created", "updated"))
    state = {
        "ts": ts,
        "auth_user": user.get("email", "ok"),
        "existing_before": len(existing),
        "processed": len(results),
        "ok": ok,
        "results": results,
    }
    (DATA / "gumroad_publisher_state.json").write_text(json.dumps(state, indent=2))
    print(f"  Done: {ok}/{len(results)} OK")
    return state


if __name__ == "__main__":
    run()
