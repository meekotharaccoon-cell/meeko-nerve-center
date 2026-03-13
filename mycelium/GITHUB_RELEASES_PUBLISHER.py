#!/usr/bin/env python3
"""
GITHUB_RELEASES_PUBLISHER.py — hosts product files as GitHub Release assets
============================================================================
Takes generated guides from product_registry.json and uploads them as
GitHub Release assets. Gives every product a permanent, free download URL
that SolarPunk fully controls.

Download URL format:
  https://github.com/meekotharaccoon-cell/meeko-nerve-center/releases/download/products-{date}/{id}.md

No Gumroad needed for delivery. No Ko-fi needed for delivery.
Just a real URL that works forever.
"""
import os, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data"); DATA.mkdir(exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "meekotharaccoon-cell"
REPO  = "meeko-nerve-center"
API   = "https://api.github.com"


def gh(method, path, body=None, upload_url=None, content_type="application/json"):
    url  = upload_url or f"{API}{path}"
    data = json.dumps(body).encode() if (body and not upload_url) else body
    req  = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": content_type,
        "User-Agent": "SolarPunk-Releases/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:150]}"
    except Exception as e:
        return None, str(e)[:80]


def get_or_create_release(tag):
    releases, _ = gh("GET", f"/repos/{OWNER}/{REPO}/releases")
    if releases:
        for r in releases:
            if r.get("tag_name") == tag:
                return r, None
    return gh("POST", f"/repos/{OWNER}/{REPO}/releases", {
        "tag_name": tag,
        "name": f"SolarPunk Digital Products — {tag}",
        "body": "Autonomous product release. 15% of all sales → PCRF Gaza. Built by AI. Running forever.",
        "draft": False,
        "prerelease": False,
    })


def upload_asset(release, filename, content_bytes):
    upload_url = release["upload_url"].replace("{?name,label}", "")
    return gh("POST", None, body=content_bytes,
              upload_url=f"{upload_url}?name={filename}",
              content_type="text/markdown")


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nGITHUB_RELEASES_PUBLISHER — {ts}")

    if not TOKEN:
        print("  SKIP: no GITHUB_TOKEN")
        return {"status": "no_token"}

    registry_path = DATA / "product_registry.json"
    if not registry_path.exists():
        print("  No product_registry.json — run PDF_GENERATOR first")
        return {"status": "no_registry"}

    registry = json.loads(registry_path.read_text())
    products = registry.get("products", {})

    # Only process products with content
    ready = {pid: p for pid, p in products.items() if p.get("content_ready")}
    if not ready:
        print("  No products with content_ready=True")
        return {"status": "nothing_ready"}

    version = datetime.now(timezone.utc).strftime("%Y%m%d")
    tag     = f"products-{version}"
    print(f"  Release tag: {tag}")

    release, err = get_or_create_release(tag)
    if not release:
        print(f"  Release creation failed: {err}")
        # Use raw GitHub fallback URLs
        for pid, product in ready.items():
            if not product.get("download_url"):
                fname = f"guide_{pid}.md"
                raw = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/data/{fname}"
                product["download_url"] = raw
                print(f"  Fallback URL for {pid}: {raw}")
        registry["last_updated"] = ts
        registry_path.write_text(json.dumps(registry, indent=2))
        return {"status": "fallback_urls"}

    print(f"  Release: {release.get('html_url')}")
    results = []

    for pid, product in ready.items():
        # Skip if already has a release URL
        existing = product.get("download_url", "")
        if existing and "releases/download" in existing:
            print(f"  SKIP {pid} — already uploaded")
            continue

        fpath = Path(product.get("file_path", DATA / f"guide_{pid}.md"))
        if not fpath.exists():
            # Try default location
            fpath = DATA / f"guide_{pid}.md"
        if not fpath.exists():
            print(f"  SKIP {pid} — file not found")
            # Set fallback
            product["download_url"] = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/data/guide_{pid}.md"
            continue

        content = fpath.read_bytes()
        filename = f"{pid}.md"
        print(f"  Uploading {filename} ({len(content):,} bytes)...")

        asset, err = upload_asset(release, filename, content)
        if asset:
            url = asset.get("browser_download_url", "")
            product["download_url"] = url
            product["release_tag"]  = tag
            product["uploaded_at"]  = ts
            print(f"  ✓ {url}")
            results.append({"id": pid, "status": "uploaded", "url": url})
        else:
            # Fallback to raw URL
            raw = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/data/guide_{pid}.md"
            product["download_url"] = raw
            print(f"  Upload failed ({err}), fallback: {raw}")
            results.append({"id": pid, "status": "fallback", "url": raw})

    registry["last_updated"]  = ts
    registry["release_url"]   = release.get("html_url", "")
    registry_path.write_text(json.dumps(registry, indent=2))

    state = {"ts": ts, "tag": tag, "results": results}
    (DATA / "github_releases_state.json").write_text(json.dumps(state, indent=2))
    print(f"  Done: {len(results)} assets processed")
    return state


if __name__ == "__main__":
    run()
