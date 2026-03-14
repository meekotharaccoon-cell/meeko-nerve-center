#!/usr/bin/env python3
"""
SECRETS_CHECKER.py — Diagnoses exactly what's configured vs missing.
Runs every cycle. Writes docs/setup.html with live status + instructions.
Never crashes, never leaks secret values. Zero external APIs.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

# Complete map of every secret the system uses
# format: name → {required, description, how_to_get, engine, revenue_impact}
SECRETS_MAP = {
    # ── AI Brain ──────────────────────────────────────────────────────────
    "ANTHROPIC_API_KEY": {
        "required": True, "category": "🧠 AI Brain",
        "description": "Powers Claude — the core intelligence behind every engine",
        "revenue_impact": "critical",
        "how_to_get": [
            "Go to console.anthropic.com",
            "Sign in / create free account",
            "Click 'API Keys' in sidebar",
            "Click 'Create Key' — name it 'solarpunk'",
            "Copy the key (starts with sk-ant-...)",
            "GitHub → Settings → Secrets → Actions → New secret",
            "Name: ANTHROPIC_API_KEY  |  Value: paste key",
        ],
        "engines": ["AI_CLIENT", "BUILD_YOURSELF", "ARCHITECT", "SELF_BUILDER", "SOLARPUNK_LOOP"],
    },
    "HF_TOKEN": {
        "required": False, "category": "🧠 AI Brain",
        "description": "HuggingFace fallback AI (free) — used if Anthropic is down",
        "revenue_impact": "low",
        "how_to_get": [
            "Go to huggingface.co → Settings → Access Tokens",
            "Create a READ token",
            "Add as GitHub Secret: HF_TOKEN",
        ],
        "engines": ["AI_CLIENT"],
    },
    # ── Revenue ────────────────────────────────────────────────────────────
    "GUMROAD_SECRET": {
        "required": True, "category": "💰 Revenue",
        "description": "Publishes your products to Gumroad automatically",
        "revenue_impact": "critical",
        "how_to_get": [
            "Log in to gumroad.com",
            "Click your avatar → Settings",
            "Click 'Advanced' tab",
            "Scroll to 'Application' section",
            "Click 'Generate Token' or copy existing token",
            "Add as GitHub Secret: GUMROAD_SECRET",
        ],
        "engines": ["GUMROAD_ENGINE", "REVENUE_LOOP"],
    },
    "GUMROAD_ID": {
        "required": False, "category": "💰 Revenue",
        "description": "Your Gumroad seller ID (for analytics)",
        "revenue_impact": "low",
        "how_to_get": ["Already set — found in your Gumroad account URL"],
        "engines": ["GUMROAD_ENGINE"],
    },
    "GUMROAD_NAME": {
        "required": False, "category": "💰 Revenue",
        "description": "Your Gumroad display name",
        "revenue_impact": "low",
        "how_to_get": ["Already set — your Gumroad username"],
        "engines": ["GUMROAD_ENGINE"],
    },
    # ── Email ──────────────────────────────────────────────────────────────
    "GMAIL_ADDRESS": {
        "required": True, "category": "📧 Email",
        "description": "Gmail address SolarPunk sends briefings from/to",
        "revenue_impact": "medium",
        "how_to_get": ["Already set — your Gmail address"],
        "engines": ["BRIEFING_ENGINE", "EMAIL_BRAIN", "DISPATCH_HANDLER"],
    },
    "GMAIL_APP_PASSWORD": {
        "required": True, "category": "📧 Email",
        "description": "Gmail App Password — NOT your regular password",
        "revenue_impact": "medium",
        "how_to_get": [
            "Log in to myaccount.google.com",
            "Search 'App Passwords' in the search bar",
            "If not visible: enable 2-Step Verification first",
            "App name: 'SolarPunk' → click Generate",
            "Copy the 16-character password (spaces don't matter)",
            "Add as GitHub Secret: GMAIL_APP_PASSWORD",
        ],
        "engines": ["BRIEFING_ENGINE", "EMAIL_BRAIN", "NIGHTLY_DIGEST"],
    },
    # ── Social ─────────────────────────────────────────────────────────────
    "X_API_KEY": {
        "required": False, "category": "📣 Social",
        "description": "Twitter/X API — auto-posts 24 queued tweets",
        "revenue_impact": "high",
        "how_to_get": [
            "Go to developer.twitter.com",
            "Create a project + app (free tier: 1500 tweets/month)",
            "Keys and Tokens tab → generate all 4 keys",
            "Add: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET",
        ],
        "engines": ["SOCIAL_PROMOTER"],
    },
    "X_API_SECRET": {
        "required": False, "category": "📣 Social",
        "description": "Twitter/X API Secret",
        "revenue_impact": "high",
        "how_to_get": ["Same step as X_API_KEY above"],
        "engines": ["SOCIAL_PROMOTER"],
    },
    "X_ACCESS_TOKEN": {
        "required": False, "category": "📣 Social",
        "description": "Twitter/X Access Token",
        "revenue_impact": "high",
        "how_to_get": ["Same step as X_API_KEY above"],
        "engines": ["SOCIAL_PROMOTER"],
    },
    "X_ACCESS_SECRET": {
        "required": False, "category": "📣 Social",
        "description": "Twitter/X Access Secret",
        "revenue_impact": "high",
        "how_to_get": ["Same step as X_API_KEY above"],
        "engines": ["SOCIAL_PROMOTER"],
    },
    "REDDIT_CLIENT_ID": {
        "required": False, "category": "📣 Social",
        "description": "Reddit API — auto-posts to relevant subreddits",
        "revenue_impact": "high",
        "how_to_get": [
            "Go to reddit.com/prefs/apps",
            "Click 'Create App' at bottom",
            "Type: 'script' | Name: 'SolarPunk'",
            "Redirect URI: http://localhost:8080",
            "Copy Client ID (under 'personal use script')",
            "Add as REDDIT_CLIENT_ID",
        ],
        "engines": ["SOCIAL_PROMOTER"],
    },
    "REDDIT_CLIENT_SECRET": {
        "required": False, "category": "📣 Social",
        "description": "Reddit API Secret",
        "revenue_impact": "high",
        "how_to_get": ["Same step as REDDIT_CLIENT_ID — it's the 'secret' field"],
        "engines": ["SOCIAL_PROMOTER"],
    },
    # ── Payments ───────────────────────────────────────────────────────────
    "PAYPAL_CLIENT_ID": {
        "required": False, "category": "💸 Payments",
        "description": "PayPal — enables automatic revenue payouts to collaborators",
        "revenue_impact": "medium",
        "how_to_get": [
            "Go to developer.paypal.com",
            "Log in with PayPal account",
            "My Apps → Create App → name: 'SolarPunk'",
            "Copy Client ID + Secret",
            "Add: PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET",
        ],
        "engines": ["HUMAN_PAYOUT"],
    },
    "PAYPAL_CLIENT_SECRET": {
        "required": False, "category": "💸 Payments",
        "description": "PayPal Client Secret",
        "revenue_impact": "medium",
        "how_to_get": ["Same step as PAYPAL_CLIENT_ID"],
        "engines": ["HUMAN_PAYOUT"],
    },
    "PAYPAL_MODE": {
        "required": False, "category": "💸 Payments",
        "description": "sandbox or live — start with sandbox for testing",
        "revenue_impact": "low",
        "how_to_get": ["Add GitHub Secret PAYPAL_MODE with value: sandbox (then switch to live later)"],
        "engines": ["HUMAN_PAYOUT"],
    },
}


def check_secrets():
    """Check which secrets are present (does not expose values)."""
    results = {}
    for name, meta in SECRETS_MAP.items():
        val = os.environ.get(name, "")
        results[name] = {
            **meta,
            "present": bool(val),
            "name": name,
        }
    return results


def build_html(results):
    """Build docs/setup.html — the master setup guide with live status."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    total = len(results)
    configured = sum(1 for r in results.values() if r["present"])
    critical_missing = [n for n, r in results.items() if r["required"] and not r["present"]]
    high_impact_missing = [n for n, r in results.items() if not r["present"] and r.get("revenue_impact") in ("high", "critical")]

    # Group by category
    categories = {}
    for name, r in results.items():
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, r))

    cards_html = ""
    for cat, items in categories.items():
        cards_html += f'<h2 class="cat">{cat}</h2>\n'
        for name, r in items:
            present = r["present"]
            required = r["required"]
            impact = r.get("revenue_impact", "low")
            status_cls = "ok" if present else ("critical" if required else f"impact-{impact}")
            status_label = "✅ CONFIGURED" if present else ("🔴 MISSING — CRITICAL" if required else f"⚪ OPTIONAL ({impact} impact)")

            steps_html = ""
            for i, step in enumerate(r.get("how_to_get", []), 1):
                steps_html += f'<div class="step"><span class="step-n">{i}</span>{step}</div>\n'

            engines_html = " ".join(f'<code>{e}</code>' for e in r.get("engines", []))

            cards_html += f"""<div class="card {status_cls}">
  <div class="card-head">
    <span class="secret-name">{name}</span>
    <span class="status-badge {status_cls}">{status_label}</span>
  </div>
  <div class="desc">{r['description']}</div>
  <div class="engines">Used by: {engines_html}</div>
  {"" if present else f'<div class="steps-wrap"><div class="steps-label">How to get it (super simple):</div>{steps_html}</div>'}
</div>\n"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk™ Setup Guide</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060e;color:#ddd;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:20px;max-width:860px;margin:0 auto;line-height:1.6}}
h1{{color:#81c784;font-size:22px;margin-bottom:4px}}
.sub{{color:#555;font-size:12px;margin-bottom:24px}}
.progress-bar{{background:#111;border-radius:20px;height:12px;margin:16px 0 8px;overflow:hidden}}
.progress-fill{{background:linear-gradient(90deg,#4caf50,#81c784);height:100%;border-radius:20px;transition:width .5s}}
.progress-label{{font-size:12px;color:#555;margin-bottom:20px}}
.hero-stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}}
.hstat{{background:#0f0f1c;border:1px solid #1a1a2e;border-radius:8px;padding:12px 20px;text-align:center}}
.hstat .n{{font-size:24px;font-weight:700;color:#81c784}}
.hstat .l{{font-size:10px;color:#555;text-transform:uppercase;letter-spacing:1px}}
.hstat.warn .n{{color:#ff7043}}
.critical-box{{background:#1a0a0a;border:1px solid #f44336;border-radius:8px;padding:16px;margin-bottom:24px}}
.critical-box h3{{color:#f44336;margin-bottom:8px;font-size:14px}}
.critical-box code{{background:#0a0a0a;padding:2px 8px;border-radius:3px;color:#ef9a9a;font-size:12px;margin:2px;display:inline-block}}
h2.cat{{color:#90caf9;font-size:13px;text-transform:uppercase;letter-spacing:2px;border-bottom:1px solid #1a1a2e;padding-bottom:8px;margin:28px 0 12px}}
.card{{background:#0f0f1c;border:1px solid #1a1a2e;border-radius:10px;padding:18px;margin:8px 0;transition:border-color .2s}}
.card.ok{{border-left:3px solid #4caf50}}
.card.critical{{border-left:3px solid #f44336}}
.card.impact-high{{border-left:3px solid #ff9800}}
.card.impact-medium{{border-left:3px solid #ff9800;opacity:.8}}
.card.impact-low{{border-left:3px solid #333}}
.card-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px}}
.secret-name{{font-family:monospace;font-size:15px;font-weight:700;color:#e0e0e0}}
.status-badge{{font-size:11px;padding:3px 10px;border-radius:4px}}
.status-badge.ok{{background:#0d1a0d;color:#81c784}}
.status-badge.critical{{background:#1a0a0a;color:#f44336}}
.status-badge.impact-high{{background:#1a0f0a;color:#ff9800}}
.status-badge.impact-medium{{background:#111;color:#aaa}}
.status-badge.impact-low{{background:#111;color:#666}}
.desc{{font-size:13px;color:#888;margin-bottom:8px}}
.engines{{font-size:11px;color:#555;margin-bottom:10px}}
.engines code{{background:#0a0a0a;padding:1px 6px;border-radius:3px;color:#546e7a;margin:2px;font-size:10px}}
.steps-wrap{{background:#080810;border-radius:6px;padding:12px;margin-top:8px}}
.steps-label{{font-size:11px;color:#4caf50;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.step{{display:flex;gap:8px;margin:6px 0;font-size:12px;color:#aaa;align-items:flex-start}}
.step-n{{background:#1a2a1a;color:#81c784;border-radius:3px;padding:1px 6px;font-size:10px;font-weight:700;flex-shrink:0;margin-top:2px}}
.github-link{{display:inline-block;background:#4caf50;color:#000;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;margin:16px 0}}
footer{{color:#333;font-size:11px;margin-top:48px;border-top:1px solid #111;padding-top:12px}}
footer a{{color:#444}}
</style>
</head>
<body>

<h1>⚡ SolarPunk™ Setup Guide</h1>
<p class="sub">Live status — auto-updated every cycle · {now}</p>

<div class="hero-stats">
  <div class="hstat"><div class="n">{configured}</div><div class="l">Configured</div></div>
  <div class="hstat {'warn' if critical_missing else ''}"><div class="n">{len(critical_missing)}</div><div class="l">Critical Missing</div></div>
  <div class="hstat"><div class="n">{total - configured}</div><div class="l">Optional Remaining</div></div>
  <div class="hstat"><div class="n">{configured * 100 // total}%</div><div class="l">Complete</div></div>
</div>

<div class="progress-bar"><div class="progress-fill" style="width:{configured * 100 // total}%"></div></div>
<div class="progress-label">{configured}/{total} secrets configured</div>

{"" if not critical_missing else f'''<div class="critical-box">
  <h3>🔴 Critical — fix these first (blocking revenue):</h3>
  {"".join(f"<code>{n}</code>" for n in critical_missing)}
</div>'''}

<a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions" class="github-link" target="_blank">
  → Open GitHub Secrets (add secrets here)
</a>

{cards_html}

<footer>
  SolarPunk™ · <a href="store.html">Store</a> · <a href="social.html">Social Queue</a> · <a href="dashboard.html">Dashboard</a><br>
  Auto-generated by SECRETS_CHECKER engine
</footer>
</body>
</html>"""


def run():
    print("SECRETS_CHECKER running...")
    results = check_secrets()

    configured = sum(1 for r in results.values() if r["present"])
    total = len(results)
    critical_missing = [n for n, r in results.items() if r["required"] and not r["present"]]

    print(f"  Secrets: {configured}/{total} configured")
    if critical_missing:
        print(f"  🔴 CRITICAL missing: {', '.join(critical_missing)}")
    else:
        print("  ✅ All critical secrets present")

    # Save state
    state = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "configured": configured,
        "total": total,
        "critical_missing": critical_missing,
        "secrets": {n: {"present": r["present"], "required": r["required"], "impact": r.get("revenue_impact")}
                    for n, r in results.items()},
    }
    (DATA / "secrets_checker_state.json").write_text(json.dumps(state, indent=2))

    # Build setup page
    html = build_html(results)
    (DOCS / "setup.html").write_text(html)
    print(f"  ✅ docs/setup.html updated — {len(html):,} bytes")
    print(f"  URL: https://meekotharaccoon-cell.github.io/meeko-nerve-center/setup.html")

    return state


if __name__ == "__main__": run()
