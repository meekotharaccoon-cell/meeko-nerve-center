# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""GITHUB_POSTER.py — SolarPunk product launches via GitHub Releases
Uses ONLY GITHUB_TOKEN (always present in Actions — zero external API keys needed).
Creates a GitHub Release for each new product launch.
Releases are public, indexed by Google, appear on the repo page, have permanent URLs.
This is the zero-dependency social channel.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
BASE_URL = f"https://api.github.com/repos/{REPO}"

def load():
    f = DATA / "github_poster_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "released": [], "total_releases": 0}

def save(s):
    (DATA / "github_poster_state.json").write_text(json.dumps(s, indent=2))

def gh(method, path, **kwargs):
    r = requests.request(
        method, f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
        timeout=30, **kwargs
    )
    return r

def get_existing_tags():
    r = gh("GET", "/releases?per_page=100")
    if r.status_code == 200:
        return {rel["tag_name"] for rel in r.json()}
    return set()

def create_release(slug, name, price, description, landing_url, gumroad_url):
    tag = f"product-{slug}"
    body = f"""## {name}

{description}

---

**Price:** {price}  
**15% of every sale goes to Palestinian relief (PCRF)**

### Links
- 🌐 **Landing page:** {landing_url}
- 🛒 **Buy:** {gumroad_url}
- 💚 **Ko-fi:** https://ko-fi.com/meekotharaccoon

---

*Built autonomously by SolarPunk — a self-running AI system that funds Gaza with every cycle.*  
*[SolarPunk Engine] — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*
"""
    r = gh("POST", "/releases", json={
        "tag_name": tag,
        "name": f"🌿 {name} — {price}",
        "body": body,
        "draft": False,
        "prerelease": False,
    })
    if r.status_code == 201:
        return r.json().get("html_url", "")
    elif r.status_code == 422:
        # Tag already exists — update the release body instead
        r2 = gh("GET", f"/releases/tags/{tag}")
        if r2.status_code == 200:
            rel_id = r2.json()["id"]
            r3 = gh("PATCH", f"/releases/{rel_id}", json={"body": body})
            return r3.json().get("html_url", "") if r3.status_code == 200 else ""
    print(f"  Release error {r.status_code}: {r.text[:200]}")
    return ""

def run():
    state = load()
    state["cycles"] = state.get("cycles", 0) + 1
    print(f"GITHUB_POSTER cycle {state['cycles']}")

    if not GITHUB_TOKEN:
        print("  No GITHUB_TOKEN — skipping (this runs fine inside GitHub Actions)")
        save(state); return state

    # Load all business packages
    existing_tags = get_existing_tags()
    released = set(state.get("released", []))
    new_this_cycle = 0

    # Discover all business_*.json files
    for biz_file in sorted(DATA.glob("business_*.json")):
        try:
            pkg = json.loads(biz_file.read_text())
        except:
            continue

        slug = pkg.get("slug") or biz_file.stem.replace("business_", "").replace("_", "-")
        tag = f"product-{slug}"

        if tag in existing_tags and slug in released:
            continue  # already posted

        name = pkg.get("name", slug.replace("-", " ").title())
        price = f"${pkg.get('price', 0)}"
        description = pkg.get("description") or pkg.get("tagline") or f"Digital product: {name}"
        landing_url = pkg.get("landing_url") or f"https://meekotharaccoon-cell.github.io/meeko-nerve-center/{slug}/"
        gumroad_url = pkg.get("gumroad_url") or "https://meekotharacoon.gumroad.com"

        url = create_release(slug, name, price, description, landing_url, gumroad_url)
        if url:
            released.add(slug)
            new_this_cycle += 1
            print(f"  ✅ Released: {name} → {url}")
        else:
            print(f"  ⚠️  Skipped: {name}")

    state["released"] = list(released)
    state["total_releases"] = len(released)
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"  {new_this_cycle} new releases | {len(released)} total")
    save(state); return state

if __name__ == "__main__": run()
