# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
REVENUE_AUDIT.py — finds every broken link/dead end blocking sales
===================================================================
Root cause of zero sales: every buy button linked to a 404 Gumroad store.
This engine finds all of them automatically every cycle.

Outputs data/revenue_audit.json with:
  - broken_links
  - revenue_blockers (critical path)
  - human_action_required
  - recommended_fixes
"""
import os, json, urllib.request, urllib.error, re, time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs")

REVENUE_URLS = [
    ("gumroad_store",  "https://meekotharaccoon.gumroad.com",   "critical"),
    ("gumroad_typo",   "https://meekotharacoon.gumroad.com",    "critical"),
    ("kofi_profile",   "https://ko-fi.com/meekotharaccoon",     "critical"),
    ("kofi_shop",      "https://ko-fi.com/meekotharaccoon/shop","critical"),
    ("gh_sponsors",    "https://github.com/sponsors/meekotharaccoon-cell", "important"),
    ("store_page",     "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html", "critical"),
    ("art_page",       "https://meekotharaccoon-cell.github.io/meeko-nerve-center/art.html",   "critical"),
    ("prompt_packs",   "https://meekotharaccoon-cell.github.io/meeko-nerve-center/ai-prompt-packs/", "important"),
    ("gh_actions_tmpl","https://meekotharaccoon-cell.github.io/meeko-nerve-center/github-actions-templates/", "important"),
    ("notion_tmpl",    "https://meekotharaccoon-cell.github.io/meeko-nerve-center/notion-templates-for-freelancers/", "important"),
]


def check_url(name, url, priority):
    try:
        req = urllib.request.Request(url, method="HEAD",
            headers={"User-Agent": "SolarPunk-RevenueAudit/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return {"name": name, "url": url, "status": r.status,
                    "ok": r.status < 400, "priority": priority}
    except urllib.error.HTTPError as e:
        return {"name": name, "url": url, "status": e.code,
                "ok": False, "priority": priority, "error": str(e)}
    except Exception as e:
        return {"name": name, "url": url, "status": 0,
                "ok": False, "priority": priority, "error": str(e)[:80]}


def scan_buy_links():
    issues = []
    for page in ["store.html", "art.html"]:
        fpath = DOCS / page
        if not fpath.exists(): continue
        content = fpath.read_text(encoding="utf-8", errors="replace")
        for url in re.findall(r'href=["\']([^"\'> ]+)["\']', content):
            if not url.startswith("http"): continue
            if "gumroad" not in url and "ko-fi" not in url: continue
            if "meekotharacoon.gumroad" in url:
                issues.append({"page": page, "url": url,
                    "issue": "TYPO: meekotharacoon (missing r)"})
            elif url.rstrip("/") == "https://meekotharaccoon.gumroad.com":
                issues.append({"page": page, "url": url,
                    "issue": "GENERIC store link — not product-specific, causes drop-off"})
    return issues


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"REVENUE_AUDIT {ts}")

    checked = []
    for name, url, priority in REVENUE_URLS:
        r = check_url(name, url, priority)
        checked.append(r)
        icon = "OK" if r["ok"] else "XX"
        print(f"  {icon} [{priority}] {name}: {r['status']}")
        time.sleep(0.25)

    broken   = [c for c in checked if not c["ok"]]
    working  = [c for c in checked if c["ok"]]
    critical = [c for c in broken  if c["priority"] == "critical"]
    buy_issues = scan_buy_links()

    gumroad_dead = any(c["name"] == "gumroad_store" and not c["ok"] for c in checked)
    kofi_alive   = any(c["name"] == "kofi_profile"  and c["ok"]  for c in checked)

    recs = []
    human_actions = []

    if gumroad_dead:
        human_actions.append({
            "priority": 1,
            "action": "Create/activate Gumroad account",
            "url": "https://gumroad.com",
            "detail": "gumroad.com -> signup -> username: meekotharaccoon -> create 1 product -> get real URL",
            "impact": "UNLOCKS ALL SALES. Every buy button is currently a 404.",
        })
        if kofi_alive:
            recs.append("Gumroad 404 detected: redirect all store buy buttons to Ko-fi immediately")

    if buy_issues:
        recs.append(f"Fix {len(buy_issues)} buy links: replace generic gumroad.com with product-specific URLs")

    recs.append("Add actual art preview images to store — selling art with no visuals = no trust")
    recs.append("Add free art lead magnet to top of store with interaction CTA")
    recs.append("Note: GitHub clone count includes automated CI checkouts — real human visitors are much lower")

    audit = {
        "ts": ts,
        "total_checked": len(checked),
        "working": len(working),
        "broken": len(broken),
        "critical_broken": len(critical),
        "buy_link_issues": len(buy_issues),
        "gumroad_alive": not gumroad_dead,
        "kofi_alive": kofi_alive,
        "revenue_blockers": critical,
        "buy_link_details": buy_issues[:20],
        "all_results": checked,
        "recommended_fixes": recs,
        "human_action_required": human_actions,
    }

    (DATA / "revenue_audit.json").write_text(json.dumps(audit, indent=2))
    print(f"  Working: {len(working)} | Broken: {len(broken)} | Critical: {len(critical)}")
    print(f"  Buy link issues: {len(buy_issues)}")
    for ha in human_actions:
        print(f"  !! HUMAN ACTION: {ha['action']} -> {ha['impact']}")
    return audit


if __name__ == "__main__":
    run()
