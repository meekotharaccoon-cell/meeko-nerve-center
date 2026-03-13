#!/usr/bin/env python3
"""
GUMROAD_PRODUCT_PUBLISHER.py — autonomous Gumroad listing manager
=================================================================
Creates and maintains ALL product listings on Gumroad via API.

REQUIRES: GUMROAD_ACCESS_TOKEN in GitHub Secrets
  1. gumroad.com/settings/advanced
  2. API section → Generate/copy access token
  3. GitHub repo Settings → Secrets → GUMROAD_ACCESS_TOKEN
  (2 minutes, never needed again)

Once set, this engine handles everything forever:
  - Creates listings for all products
  - Updates descriptions with real download URLs
  - Sets prices, titles, descriptions autonomously
  - Publishes new products as they're generated
"""
import os, json, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
API   = "https://api.gumroad.com/v2"


def gumroad(method, endpoint, params=None):
    url  = f"{API}{endpoint}"
    data = None
    if params:
        params["access_token"] = TOKEN
        if method in ("POST", "PUT", "PATCH"):
            data = urllib.parse.urlencode(params).encode()
            req  = urllib.request.Request(url, data=data, method=method,
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "User-Agent": "SolarPunk-Gumroad/2.0"})
        else:
            qs  = urllib.parse.urlencode(params)
            req = urllib.request.Request(f"{url}?{qs}", method=method,
                headers={"User-Agent": "SolarPunk-Gumroad/2.0"})
    else:
        qs  = urllib.parse.urlencode({"access_token": TOKEN})
        req = urllib.request.Request(f"{url}?{qs}", method=method,
            headers={"User-Agent": "SolarPunk-Gumroad/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return None, str(e)[:80]


def list_products():
    result, err = gumroad("GET", "/products")
    if result and result.get("success"):
        return {p["name"]: p for p in result.get("products", [])}
    return {}


def create_product(name, price_cents, description):
    result, err = gumroad("POST", "/products", {
        "name": name,
        "price": price_cents,
        "description": description,
    })
    if result and result.get("success"):
        return result["product"], None
    return None, err


def update_product(product_id, name, price_cents, description):
    result, err = gumroad("PUT", f"/products/{product_id}", {
        "name": name,
        "price": price_cents,
        "description": description,
    })
    if result and result.get("success"):
        return result["product"], None
    return None, err


def build_description(spec, download_url=None):
    lines = [spec["tagline"], ""]
    lines.append(f"**{spec.get('target_pages', 40)} pages** of real, actionable content.")
    lines.append("")
    if download_url:
        lines.append(f"📥 **Instant download:** {download_url}")
        lines.append("Direct link — no login, no expiry, works forever.")
    else:
        lines.append("📥 **Instant download** — delivered automatically after purchase.")
    lines.append("")
    lines.append(f"🌹 **{spec.get('gaza_split_pct', 15)}% of your purchase → Gaza**")
    lines.append("PCRF EIN: 93-1057665 · 4★ Charity Navigator · Gaza children since 1991")
    lines.append("")
    lines.append("---")
    lines.append("Built by SolarPunk™ — an autonomous AI revenue system.")
    lines.append("https://meekotharaccoon-cell.github.io/meeko-nerve-center/")
    return "\n".join(lines)


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nGUMROAD_PRODUCT_PUBLISHER — {ts}")

    if not TOKEN:
        print("  BLOCKED: GUMROAD_ACCESS_TOKEN not set")
        print("  ─────────────────────────────────────────")
        print("  ONE-TIME SETUP (2 minutes, never again):")
        print("    1. gumroad.com/settings/advanced")
        print("    2. Find 'API' → Generate/copy access token")
        print("    3. GitHub repo → Settings → Secrets → Actions")
        print("    4. New secret → GUMROAD_ACCESS_TOKEN → paste → Save")
        print("  ─────────────────────────────────────────")
        (DATA / "gumroad_setup_needed.json").write_text(json.dumps({
            "status": "needs_token",
            "ts": ts,
            "message": "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets to unlock full Gumroad automation",
            "steps": [
                "gumroad.com/settings/advanced",
                "Find 'API' section → Generate access token",
                "GitHub repo Settings → Secrets → GUMROAD_ACCESS_TOKEN"
            ]
        }, indent=2))
        return {"status": "needs_token"}

    # Load product registry for download URLs
    registry = {}
    reg_path = DATA / "product_registry.json"
    if reg_path.exists():
        registry = json.loads(reg_path.read_text()).get("products", {})

    # Load canonical product list
    directive = {}
    dir_path = DATA / "system_directive.json"
    if dir_path.exists():
        directive = json.loads(dir_path.read_text())
    canonical = directive.get("product_line_canonical", [])

    if not canonical:
        print("  No canonical products in system_directive.json")
        return {"status": "no_products"}

    # Get current Gumroad listings
    existing = list_products()
    print(f"  Existing Gumroad products: {len(existing)}")

    results = []
    for spec in canonical:
        pid   = spec["id"]
        title = spec["title"]
        price = int(spec["price_usd"] * 100)
        dl_url = registry.get(pid, {}).get("download_url")
        desc  = build_description(spec, dl_url)

        if title in existing:
            gp   = existing[title]
            prod, err = update_product(gp["id"], title, price, desc)
            if prod:
                url = f"https://meekotharaccoon.gumroad.com/l/{gp.get('custom_permalink') or gp['id']}"
                if pid in registry:
                    registry[pid]["gumroad_url"] = url
                print(f"  UPDATED: {title[:50]}")
                results.append({"id": pid, "status": "updated", "url": url})
            else:
                print(f"  UPDATE FAIL {pid}: {err}")
                results.append({"id": pid, "status": "error", "error": str(err)[:60]})
        else:
            prod, err = create_product(title, price, desc)
            if prod:
                url = f"https://meekotharaccoon.gumroad.com/l/{prod.get('custom_permalink') or prod.get('id', pid)}"
                registry.setdefault(pid, {})["gumroad_url"] = url
                registry[pid]["gumroad_id"] = prod.get("id")
                print(f"  CREATED: {title[:50]} → {url}")
                results.append({"id": pid, "status": "created", "url": url})
            else:
                print(f"  CREATE FAIL {pid}: {err}")
                results.append({"id": pid, "status": "error", "error": str(err)[:60]})

    # Save updated registry
    if reg_path.exists():
        full = json.loads(reg_path.read_text())
        full["products"] = registry
        full["last_updated"] = ts
        reg_path.write_text(json.dumps(full, indent=2))

    state = {"ts": ts, "existing_before": len(existing), "results": results}
    (DATA / "gumroad_publisher_state.json").write_text(json.dumps(state, indent=2))
    print(f"  Done: {len(results)} products processed")
    return state


if __name__ == "__main__":
    run()
