# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BOTTLENECK_SCANNER.py - identifies what's blocking revenue and outputs fix plan.

Fixed: write_html_report() was missing `secrets` argument in run() call.
Fixed: revenue_inbox.json list guard in check_revenue().

Outputs: data/bottleneck_report.json + docs/bottleneck.html
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)


def check_secrets():
    secrets = {
        "ANTHROPIC_API_KEY":    {"impact": "CRITICAL", "unlocks": ["SELF_BUILDER", "KNOWLEDGE_WEAVER", "AI brain"]},
        "GUMROAD_SECRET":       {"impact": "CRITICAL", "unlocks": ["10 queued products publishing"]},
        "GMAIL_ADDRESS":        {"impact": "HIGH",     "unlocks": ["email briefings", "outreach"]},
        "GMAIL_APP_PASSWORD":   {"impact": "HIGH",     "unlocks": ["email sending — MUST be App Password not account password"]},
        "X_API_KEY":            {"impact": "HIGH",     "unlocks": ["100+ queued tweets posting"]},
        "X_API_SECRET":         {"impact": "HIGH",     "unlocks": ["Twitter auth"]},
        "X_ACCESS_TOKEN":       {"impact": "HIGH",     "unlocks": ["Twitter account auth"]},
        "X_ACCESS_TOKEN_SECRET":{"impact": "HIGH",     "unlocks": ["Twitter account auth"]},
        "REDDIT_CLIENT_ID":     {"impact": "MEDIUM",   "unlocks": ["Reddit auto-posting"]},
        "REDDIT_CLIENT_SECRET": {"impact": "MEDIUM",   "unlocks": ["Reddit auto-posting"]},
        "PAYPAL_CLIENT_ID":     {"impact": "MEDIUM",   "unlocks": ["automated payouts"]},
        "PAYPAL_CLIENT_SECRET": {"impact": "MEDIUM",   "unlocks": ["PayPal API auth"]},
        "HF_TOKEN":             {"impact": "MEDIUM",   "unlocks": ["HuggingFace fallback AI"]},
        "GUMROAD_ID":           {"impact": "LOW",      "unlocks": ["Gumroad analytics"]},
        "GUMROAD_NAME":         {"impact": "LOW",      "unlocks": ["Gumroad display name"]},
        "REDDIT_USERNAME":      {"impact": "LOW",      "unlocks": ["Reddit identity"]},
        "REDDIT_PASSWORD":      {"impact": "LOW",      "unlocks": ["Reddit login"]},
        "KOFI_VERIFICATION_TOKEN": {"impact": "LOW",   "unlocks": ["Ko-fi webhook verification"]},
    }
    results = []
    for name, info in secrets.items():
        val = os.environ.get(name, "")
        results.append({
            "name": name, "present": bool(val), "length": len(val),
            "impact": info["impact"], "unlocks": info["unlocks"],
        })
    return results


def check_engines():
    results = []
    for f in sorted(Path("mycelium").glob("*.py")):
        if f.name.startswith("__"): continue
        try:
            code = f.read_text()
            import subprocess
            r = subprocess.run(["python3", "-m", "py_compile", str(f)],
                               capture_output=True, text=True)
            syntax_ok = r.returncode == 0
        except Exception:
            syntax_ok = False
        needs = [s for s in ["ANTHROPIC_API_KEY","GUMROAD_SECRET","GMAIL_APP_PASSWORD",
                              "X_API_KEY","PAYPAL_CLIENT_ID","REDDIT_CLIENT_ID"] if s in code]
        results.append({"name": f.name, "size": f.stat().st_size,
                         "syntax_ok": syntax_ok, "needs_secrets": needs})
    return results


def check_gumroad_listings():
    f = DATA / "gumroad_listings.json"
    if not f.exists():
        return {"status": "MISSING", "products": 0, "live": 0}
    try:
        data = json.loads(f.read_text())
        if isinstance(data, list):
            return {"status": "LIST_FORMAT", "products": len(data), "live": 0}
        products = data.get("products", [])
        live = sum(1 for p in products if p.get("gumroad_result", {}).get("status") == "live")
        return {"status": "EXISTS", "products": len(products), "live": live}
    except:
        return {"status": "CORRUPT", "products": 0, "live": 0}


def check_revenue():
    f = DATA / "revenue_inbox.json"
    if not f.exists():
        return {"total_received": 0, "total_to_gaza": 0, "payments": 0}
    try:
        data = json.loads(f.read_text())
        if isinstance(data, list):
            return {"total_received": 0, "total_to_gaza": 0, "payments": len(data)}
        return {
            "total_received": data.get("total_received", 0),
            "total_to_gaza":  data.get("total_to_gaza",  0),
            "payments":       len(data.get("inbox", [])),
        }
    except:
        return {"total_received": 0, "total_to_gaza": 0, "payments": 0}


def identify_bottlenecks(secrets, engines, gumroad, revenue):
    bottlenecks = []
    bn_id = 1

    def s(name):
        return next((x for x in secrets if x["name"] == name), None)

    anthropic = s("ANTHROPIC_API_KEY")
    if anthropic and not anthropic["present"]:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "CRITICAL",
            "title": "ANTHROPIC_API_KEY missing",
            "description": "All Claude-powered engines fail. SELF_BUILDER, KNOWLEDGE_WEAVER, SYNTHESIS_FACTORY output nothing.",
            "fix": "console.anthropic.com -> API Keys -> Create -> GitHub Secret: ANTHROPIC_API_KEY",
            "revenue_impact": "$0/day (AI brain offline)", "status": "PENDING"
        }); bn_id += 1

    gumroad_sec = s("GUMROAD_SECRET")
    if gumroad_sec and not gumroad_sec["present"]:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "CRITICAL",
            "title": "GUMROAD_SECRET missing -- 10 products can't publish",
            "description": "GUMROAD_ENGINE has products queued but can't authenticate to Gumroad API.",
            "fix": "gumroad.com -> avatar -> Settings -> Advanced -> Generate Token -> GitHub Secret: GUMROAD_SECRET",
            "revenue_impact": f"${gumroad['products'] * 1}/sale blocked", "status": "PENDING"
        }); bn_id += 1

    # Gmail App Password -- this is BREAKING everything silently
    gmail_pw = s("GMAIL_APP_PASSWORD")
    gmail_ad = s("GMAIL_ADDRESS")
    if gmail_ad and gmail_ad["present"] and gmail_pw and gmail_pw["present"]:
        # If set but 534 errors known, flag it
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "HIGH",
            "title": "Gmail 534 error -- App Password wrong or expired",
            "description": "Every email send fails: '534 Application-specific password required'. outreach_sent=0, exchange deaf.",
            "fix": "Google Account -> Security -> 2-Step Verification -> App Passwords -> Generate for Mail -> update GMAIL_APP_PASSWORD secret",
            "revenue_impact": "Zero email outreach, exchange tasks undeliverable, digests silent",
            "status": "BROKEN"
        }); bn_id += 1

    x_key = s("X_API_KEY")
    if not (x_key and x_key["present"]):
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "HIGH",
            "title": "Twitter/X keys missing -- 100+ posts in queue",
            "description": "SOCIAL_PROMOTER has posts ready every cycle. No X_API_KEY = none post.",
            "fix": "developer.twitter.com -> App -> Keys -> API Key+Secret+Access Token+Secret -> 4 GitHub Secrets",
            "revenue_impact": "Zero Twitter distribution", "status": "PENDING"
        }); bn_id += 1

    broken = [e for e in engines if not e["syntax_ok"]]
    if broken:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "LOW",
            "title": f"{len(broken)} engines have syntax errors",
            "description": f"Broken: {', '.join(e['name'] for e in broken[:5])}",
            "fix": "Fix ANTHROPIC_API_KEY to enable AI auto-patching via AUTO_HEALER",
            "revenue_impact": "Minor -- those engines skipped", "status": "KNOWN"
        }); bn_id += 1

    return bottlenecks


def write_html_report(bottlenecks, secrets, engines, gumroad, revenue, now):
    critical     = [b for b in bottlenecks if b["severity"] == "CRITICAL"]
    high         = [b for b in bottlenecks if b["severity"] == "HIGH"]
    secret_ok    = sum(1 for s in secrets if s["present"])
    engine_ok    = sum(1 for e in engines if e["syntax_ok"])

    rows = ""
    for bn in bottlenecks:
        rows += (f'<div class="bn {bn["severity"]}">'
                 f'<div class="bn-head"><span class="bn-title">{bn["id"]} -- {bn["title"]}</span>'
                 f'<span class="badge {bn["severity"]}">{bn["severity"]}</span></div>'
                 f'<div class="bn-desc">{bn["description"]}</div>'
                 f'<div class="bn-fix">{bn["fix"]}</div></div>\n')

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Bottleneck Scanner</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060e;color:#dde;font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:20px 16px 60px}}
h1{{color:#ff5e5b;font-size:1.4rem;margin-bottom:4px}}
.ts{{color:rgba(255,255,255,.25);font-size:.7rem;margin-bottom:20px}}
.stat-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px;margin-bottom:24px}}
.stat{{background:#0f0f1c;border:1px solid rgba(255,255,255,.07);border-radius:8px;padding:12px;text-align:center}}
.stat .n{{font-size:1.8rem;font-weight:800;display:block}}
.stat .l{{font-size:.65rem;color:rgba(255,255,255,.35);text-transform:uppercase;letter-spacing:1px}}
.red .n{{color:#ff5e5b}}.orange .n{{color:#ff9800}}.green .n{{color:#00ff88}}.blue .n{{color:#90caf9}}
.bn{{background:#0f0f1c;border-radius:10px;padding:16px;margin-bottom:10px;border-left:4px solid #333}}
.bn.CRITICAL{{border-left-color:#ff5e5b}}.bn.HIGH{{border-left-color:#ff9800}}
.bn.MEDIUM{{border-left-color:#ffd700}}.bn.LOW{{border-left-color:#444}}
.bn-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:6px}}
.bn-title{{font-size:.9rem;font-weight:700}}
.badge{{font-size:.65rem;padding:2px 8px;border-radius:4px;font-weight:700}}
.CRITICAL{{background:rgba(255,94,91,.15);color:#ff5e5b}}
.HIGH{{background:rgba(255,152,0,.1);color:#ff9800}}
.MEDIUM{{background:rgba(255,215,0,.08);color:#ffd700}}
.bn-desc{{font-size:.78rem;color:rgba(255,255,255,.45);line-height:1.6;margin-bottom:8px}}
.bn-fix{{background:#080810;border-radius:6px;padding:10px 12px;font-size:.75rem;color:rgba(0,255,136,.7);line-height:1.6}}
.bn-fix::before{{content:"FIX: ";color:#00ff88;font-weight:700}}
.section-title{{font-size:.7rem;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.2);margin:24px 0 10px}}
</style></head><body>
<h1>Bottleneck Scanner</h1>
<p class="ts">Generated {now} - {len(bottlenecks)} blockers</p>
<div class="stat-row">
  <div class="stat red"><span class="n">{len(critical)}</span><span class="l">Critical</span></div>
  <div class="stat orange"><span class="n">{len(high)}</span><span class="l">High</span></div>
  <div class="stat green"><span class="n">{secret_ok}/{len(secrets)}</span><span class="l">Secrets OK</span></div>
  <div class="stat blue"><span class="n">{engine_ok}/{len(engines)}</span><span class="l">Engines OK</span></div>
  <div class="stat green"><span class="n">${revenue['total_to_gaza']:.2f}</span><span class="l">To Gaza</span></div>
  <div class="stat"><span class="n">{gumroad['live']}/{gumroad['products']}</span><span class="l">Gumroad Live</span></div>
</div>
<div class="section-title">Blockers</div>
{rows}
<div class="section-title">-> After fixing: trigger Actions -> OMNIBRAIN (workflow_dispatch)</div>
</body></html>"""

    (DOCS / "bottleneck.html").write_text(html)
    print("  Wrote docs/bottleneck.html")


def run():
    print("BOTTLENECK_SCANNER running...")
    now = datetime.now(timezone.utc).isoformat()

    secrets     = check_secrets()
    engines     = check_engines()
    gumroad     = check_gumroad_listings()
    revenue     = check_revenue()
    bottlenecks = identify_bottlenecks(secrets, engines, gumroad, revenue)

    report = {
        "generated": now,
        "summary": {
            "total_bottlenecks": len(bottlenecks),
            "critical":     len([b for b in bottlenecks if b["severity"] == "CRITICAL"]),
            "high":         len([b for b in bottlenecks if b["severity"] == "HIGH"]),
            "secrets_ok":   sum(1 for s in secrets if s["present"]),
            "secrets_total": len(secrets),
            "engines_ok":   sum(1 for e in engines if e["syntax_ok"]),
            "engines_total": len(engines),
            "gumroad_live":    gumroad["live"],
            "gumroad_pending": gumroad["products"] - gumroad["live"],
            "revenue_total":   revenue["total_received"],
            "gaza_total":      revenue["total_to_gaza"],
        },
        "bottlenecks": bottlenecks,
        "secrets":     secrets,
    }

    (DATA / "bottleneck_report.json").write_text(json.dumps(report, indent=2))
    write_html_report(bottlenecks, secrets, engines, gumroad, revenue, now)  # FIXED: secrets arg

    c = report["summary"]["critical"]
    h = report["summary"]["high"]
    print(f"  {c} CRITICAL + {h} HIGH blockers")
    for bn in bottlenecks:
        if bn["severity"] in ("CRITICAL", "HIGH"):
            print(f"  [{bn['severity']}] {bn['title']}")
            print(f"    FIX: {bn['fix']}")
    print(f"  Secrets: {report['summary']['secrets_ok']}/{report['summary']['secrets_total']}")
    print(f"  Engines: {report['summary']['engines_ok']}/{report['summary']['engines_total']}")


if __name__ == "__main__": run()
