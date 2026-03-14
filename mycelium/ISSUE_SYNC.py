# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""ISSUE_SYNC.py — keeps GitHub Issues current with real system state every cycle
Uses ONLY GITHUB_TOKEN. Reads omnibus_last.json + business files,
updates issue checkboxes to reflect actual secret/credential status.
Auto-creates issues for newly-built products.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
BASE = f"https://api.github.com/repos/{REPO}"
HEAD = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def gh(method, path, **kwargs):
    return requests.request(method, f"{BASE}{path}", headers=HEAD, timeout=30, **kwargs)

def rj(f):
    p = DATA / f
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {}

def get_product_issues():
    r = gh("GET", "/issues?state=open&labels=product&per_page=100")
    return r.json() if r.status_code == 200 else []

def build_body(pkg, omnibus):
    slug = pkg.get("slug", "?")
    name = pkg.get("name", slug)
    price = pkg.get("price", 0)
    landing = pkg.get("landing_url", f"https://meekotharaccoon-cell.github.io/meeko-nerve-center/{slug}/")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    has_gumroad = bool(os.environ.get("GUMROAD_ACCESS_TOKEN"))
    has_twitter = bool(os.environ.get("X_API_KEY"))
    has_gmail   = bool(os.environ.get("GMAIL_APP_PASSWORD"))
    engines_ok  = len(omnibus.get("engines_ok", []))
    engines_fail = len(omnibus.get("engines_failed", []))
    health = omnibus.get("health_after", 40)

    return f"""## {name}

**Landing:** {landing}
**Buy:** https://meekotharacoon.gumroad.com
**Price:** ${price} · 15% to PCRF

## Status
- [x] Business package built
- [x] Landing page deployed (GitHub Pages)
- [x] Social posts queued
- {'[x]' if has_gumroad else '[ ]'} Gumroad listing{'' if has_gumroad else ' — needs `GUMROAD_ACCESS_TOKEN`'}
- {'[x]' if has_twitter else '[ ]'} Twitter/Reddit auto-post{'' if has_twitter else ' — needs `X_API_KEY`'}
- {'[x]' if has_gmail else '[ ]'} Email briefing{'' if has_gmail else ' — needs Gmail App Password'}

## System state
- Engines: {engines_ok} OK / {engines_fail} failed
- Health: {health}/100
- Last run: {omnibus.get('completed','?')[:19].replace('T',' ')} UTC

## Posts
Copy-paste: https://meekotharaccoon-cell.github.io/meeko-nerve-center/social.html

*ISSUE_SYNC auto-updated {now}*"""

def run():
    print("ISSUE_SYNC running...")
    if not GITHUB_TOKEN:
        print("  No GITHUB_TOKEN"); return

    omnibus = rj("omnibus_last.json")
    issues = get_product_issues()
    updated = 0

    # Map title fragments to issue numbers
    title_map = {i["title"].lower(): i["number"] for i in issues}

    for biz_file in sorted(DATA.glob("business_*.json")):
        if "factory_state" in biz_file.name or "summary" in biz_file.name: continue
        try: pkg = json.loads(biz_file.read_text())
        except: continue

        name = pkg.get("name", "")
        slug = pkg.get("slug", "")
        price = pkg.get("price", 0)
        body = build_body(pkg, omnibus)

        # Find matching issue
        issue_num = None
        for title, num in title_map.items():
            if name.lower() in title or slug.lower().replace("-"," ") in title:
                issue_num = num
                break

        if issue_num:
            gh("PATCH", f"/issues/{issue_num}", json={"body": body})
            print(f"  Updated #{issue_num}: {name}")
            updated += 1
        else:
            r = gh("POST", "/issues", json={
                "title": f"🌿 LIVE: {name} — ${price} · 15% to Gaza",
                "body": body,
                "labels": ["product", "live"]
            })
            if r.status_code == 201:
                print(f"  Created #{r.json()['number']}: {name}")
                updated += 1

    (DATA / "issue_sync_state.json").write_text(json.dumps({
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "updated": updated,
    }, indent=2))

    print(f"  {updated} issues synced")

if __name__ == "__main__": run()
