#!/usr/bin/env python3
"""
HEALTH_BOOSTER.py — System Diagnostics + Honest Scoring
Diagnoses every known blocker. Reports what needs human action.
Updates health score in brain_state.json.

Health score (100 pts):
  20 — ANTHROPIC_API_KEY valid
  15 — Shop page deployed
  10 — Gumroad listings created
  10 — Social media credentials
  10 — Email delivery credentials
  10 — Data pipeline flowing
  15 — Revenue > $0

SolarPunk heals itself. Meeko heals the rest.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data")
DOCS  = Path("docs")
DATA.mkdir(exist_ok=True)

SECRETS_NEEDED = {
    "ANTHROPIC_API_KEY":    {"pts": 20, "category": "AI",       "how": "anthropic.com/console → API Keys"},
    "GUMROAD_ACCESS_TOKEN": {"pts": 10, "category": "Revenue",  "how": "gumroad.com → Settings → Advanced → Access Token"},
    "GMAIL_ADDRESS":        {"pts":  5, "category": "Delivery", "how": "Your Gmail address"},
    "GMAIL_APP_PASSWORD":   {"pts":  5, "category": "Delivery", "how": "Google Account → Security → App Passwords"},
    "HF_TOKEN":             {"pts":  5, "category": "Art",      "how": "huggingface.co → Settings → Access Tokens"},
    "X_API_KEY":            {"pts":  5, "category": "Social",   "how": "developer.twitter.com → App → Keys & Tokens"},
    "X_ACCESS_TOKEN":       {"pts":  3, "category": "Social",   "how": "developer.twitter.com → App → Keys & Tokens"},
    "REDDIT_CLIENT_ID":     {"pts":  2, "category": "Social",   "how": "reddit.com/prefs/apps → Create app (script type)"},
}

def check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return False, "ANTHROPIC_API_KEY not set"
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 10,
                  "messages": [{"role": "user", "content": "ping"}]}, timeout=10)
        if r.status_code == 200:
            return True, "API key valid ✓"
        elif r.status_code == 401:
            return False, "API key invalid (401) — regenerate at anthropic.com/console"
        elif r.status_code == 429:
            return True, "API key valid (rate limited)"
        else:
            return False, f"API error: {r.status_code}"
    except Exception as ex:
        return False, f"Network error: {ex}"

def check_revenue():
    try:
        ff = json.loads((DATA / "flywheel_state.json").read_text())
        return ff.get("total_sales", 0) > 0, ff.get("total_to_gaza", 0.0), ff.get("total_sales", 0)
    except:
        return False, 0.0, 0

def score_and_report():
    score = 0
    issues = []
    fixes = []
    achievements = []

    # API key check
    api_ok, api_msg = check_api_key()
    if api_ok:
        score += 20
        achievements.append(f"✅ Anthropic API: {api_msg}")
    else:
        issues.append(f"🔴 CRITICAL: {api_msg} — All AI features disabled")
        fixes.append("Go to anthropic.com/console → API Keys → Create new key → Add as ANTHROPIC_API_KEY in GitHub Secrets")

    # File checks
    if (DOCS / "index.html").exists():
        score += 15
        achievements.append("✅ Shop page: docs/index.html deployed")
    else:
        issues.append("🔴 Shop page missing — docs/index.html not found")

    for fname, pts, label in [("links.html", 3, "Links page"), ("dashboard.html", 3, "Dashboard")]:
        if (DOCS / fname).exists():
            score += pts
            achievements.append(f"✅ {label}: docs/{fname} exists")

    if (DATA / "flywheel_state.json").exists():
        score += 5
        achievements.append("✅ Data pipeline: flywheel_state.json exists")

    # Secret checks
    missing_secrets = []
    for secret, info in SECRETS_NEEDED.items():
        val = os.environ.get(secret, "")
        if val and len(val) > 3:
            score += info["pts"]
            achievements.append(f"✅ {secret}: configured")
        else:
            missing_secrets.append({**info, "secret": secret})

    grouped = {}
    for s in missing_secrets:
        grouped.setdefault(s["category"], []).append(s)
    for cat, secrets in grouped.items():
        pts_lost = sum(s["pts"] for s in secrets)
        issues.append(f"⚠️ {cat}: {len(secrets)} secret(s) missing → -{pts_lost} pts potential")
        for s in secrets:
            fixes.append(f"Add {s['secret']}: {s['how']}")

    # Revenue check
    has_revenue, gaza_total, sales = check_revenue()
    if has_revenue:
        score += 15
        achievements.append(f"✅ REVENUE: {sales} sales | ${gaza_total:.2f} to Gaza 🎉")
    else:
        issues.append("💰 No revenue yet — shop needs human promotion")
        fixes.append("Share shop URL: meekotharaccoon-cell.github.io/meeko-nerve-center")
        fixes.append("Use ready tweets in data/social_latest.json")

    score = min(score, 100)

    if score >= 80:   status = "THRIVING"
    elif score >= 60: status = "GROWING"
    elif score >= 40: status = "FUNCTIONAL"
    elif score >= 20: status = "BOOTSTRAPPING"
    else:             status = "OFFLINE"

    return {"score": score, "status": status, "achievements": achievements,
            "issues": issues, "fixes": fixes, "missing_secrets": missing_secrets,
            "has_revenue": has_revenue, "total_sales": sales, "total_to_gaza": gaza_total}

def update_brain_state(report):
    brain_file = DATA / "brain_state.json"
    brain = {}
    try:
        brain = json.loads(brain_file.read_text())
    except:
        pass
    old_score = brain.get("health_score", 0)
    brain["health_score"] = report["score"]
    brain["health_status"] = report["status"]
    brain["health_checked_at"] = datetime.now(timezone.utc).isoformat()
    brain["blockers"] = report["issues"][:5]
    brain["next_fixes"] = report["fixes"][:3]
    if report["score"] > old_score:
        brain.setdefault("milestones", []).append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "score": report["score"],
            "note": f"Health improved {old_score}→{report['score']}"
        })
    brain_file.write_text(json.dumps(brain, indent=2))
    return old_score

def run():
    print("HEALTH_BOOSTER: Scanning system...")
    report = score_and_report()
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    (DATA / "health_report.json").write_text(json.dumps(report, indent=2))
    old_score = update_brain_state(report)
    delta = report["score"] - old_score
    delta_str = f" (+{delta})" if delta > 0 else (f" ({delta})" if delta < 0 else " (=)")

    print(f"\n{'='*50}")
    print(f"  HEALTH: {report['score']}/100{delta_str} — {report['status']}")
    print(f"{'='*50}")
    for a in report["achievements"]:
        print(f"  {a}")
    if report["issues"]:
        print("\n⚠️ ISSUES:")
        for i in report["issues"]:
            print(f"  {i}")
    if report["fixes"]:
        print("\n🔧 NEXT FIXES (for Meeko):")
        for i, f in enumerate(report["fixes"][:5], 1):
            print(f"  {i}. {f}")
    print(f"\n📊 Revenue: {report['total_sales']} sales | ${report['total_to_gaza']:.2f} to Gaza")
    print(f"{'='*50}\n")
    return report

if __name__ == "__main__":
    run()
