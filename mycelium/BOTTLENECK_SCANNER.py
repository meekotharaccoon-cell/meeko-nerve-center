#!/usr/bin/env python3
"""
BOTTLENECK_SCANNER.py — identifies exactly what's blocking revenue and outputs fix plan.

Checks every secret, every engine, every revenue path.
Outputs: data/bottleneck_report.json + docs/bottleneck.html
Wired into OMNIBUS as a diagnostic layer.
"""
import os, json, re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)


def check_secrets():
    """Check which secrets are present and classify their impact."""
    secrets = {
        "ANTHROPIC_API_KEY":    {"impact": "CRITICAL", "unlocks": ["BUILD", "SOLARPUNK_LOOP", "SELF_BUILDER", "AI brain"]},
        "GUMROAD_SECRET":       {"impact": "CRITICAL", "unlocks": ["product publishing", "automated sales"]},
        "GUMROAD_ID":           {"impact": "LOW",      "unlocks": ["Gumroad analytics"]},
        "GUMROAD_NAME":         {"impact": "LOW",      "unlocks": ["Gumroad display name"]},
        "GMAIL_ADDRESS":        {"impact": "HIGH",     "unlocks": ["email briefings", "payment alerts"]},
        "GMAIL_APP_PASSWORD":   {"impact": "HIGH",     "unlocks": ["email sending (check App Password not account password)"]},
        "HF_TOKEN":             {"impact": "MEDIUM",   "unlocks": ["HuggingFace fallback AI"]},
        "X_API_KEY":            {"impact": "HIGH",     "unlocks": ["auto-posting 24 queued tweets"]},
        "X_API_SECRET":         {"impact": "HIGH",     "unlocks": ["Twitter posting (required with X_API_KEY)"]},
        "X_ACCESS_TOKEN":       {"impact": "HIGH",     "unlocks": ["Twitter account auth"]},
        "X_ACCESS_TOKEN_SECRET":{"impact": "HIGH",     "unlocks": ["Twitter account auth"]},
        "REDDIT_CLIENT_ID":     {"impact": "MEDIUM",   "unlocks": ["Reddit auto-posting"]},
        "REDDIT_CLIENT_SECRET": {"impact": "MEDIUM",   "unlocks": ["Reddit auto-posting"]},
        "REDDIT_USERNAME":      {"impact": "LOW",      "unlocks": ["Reddit identity"]},
        "REDDIT_PASSWORD":      {"impact": "LOW",      "unlocks": ["Reddit login"]},
        "PAYPAL_CLIENT_ID":     {"impact": "MEDIUM",   "unlocks": ["automated human payouts"]},
        "PAYPAL_CLIENT_SECRET": {"impact": "MEDIUM",   "unlocks": ["PayPal API auth"]},
        "KOFI_VERIFICATION_TOKEN": {"impact": "LOW",   "unlocks": ["Ko-fi webhook verification"]},
    }
    results = []
    for name, info in secrets.items():
        val = os.environ.get(name, "")
        results.append({
            "name": name,
            "present": bool(val),
            "length": len(val) if val else 0,
            "impact": info["impact"],
            "unlocks": info["unlocks"],
        })
    return results


def check_engines():
    """Check engine syntax and classify which ones need secrets to run."""
    engine_dir = Path("mycelium")
    results = []
    for f in sorted(engine_dir.glob("*.py")):
        if f.name.startswith("__"): continue
        try:
            code = f.read_text()
            # Check syntax
            import subprocess
            r = subprocess.run(["python3", "-m", "py_compile", str(f)],
                             capture_output=True, text=True)
            syntax_ok = r.returncode == 0
        except Exception:
            syntax_ok = False
        
        # Find which secrets this engine needs
        needs = []
        for s in ["ANTHROPIC_API_KEY","GUMROAD_SECRET","GMAIL_APP_PASSWORD","X_API_KEY","PAYPAL_CLIENT_ID","REDDIT_CLIENT_ID"]:
            if s in code:
                needs.append(s)
        
        results.append({
            "name": f.name,
            "size": f.stat().st_size,
            "syntax_ok": syntax_ok,
            "needs_secrets": needs,
        })
    return results


def check_gumroad_listings():
    """Check if gumroad_listings.json is populated."""
    f = DATA / "gumroad_listings.json"
    if not f.exists():
        return {"status": "MISSING", "products": 0, "live": 0}
    try:
        data = json.loads(f.read_text())
        products = data.get("products", [])
        live = sum(1 for p in products if p.get("gumroad_result", {}).get("status") == "live")
        return {"status": "EXISTS", "products": len(products), "live": live}
    except:
        return {"status": "CORRUPT", "products": 0, "live": 0}


def check_revenue():
    """Check current revenue state."""
    f = DATA / "revenue_inbox.json"
    if not f.exists():
        return {"total_received": 0, "total_to_gaza": 0, "payments": 0}
    try:
        data = json.loads(f.read_text())
        return {
            "total_received": data.get("total_received", 0),
            "total_to_gaza": data.get("total_to_gaza", 0),
            "payments": len(data.get("inbox", [])),
        }
    except:
        return {"total_received": 0, "total_to_gaza": 0, "payments": 0}


def identify_bottlenecks(secrets, engines, gumroad, revenue):
    """Generate prioritized bottleneck list."""
    bottlenecks = []
    bn_id = 1
    
    # Check API key
    anthropic = next((s for s in secrets if s["name"] == "ANTHROPIC_API_KEY"), None)
    if anthropic and not anthropic["present"]:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "CRITICAL",
            "title": "ANTHROPIC_API_KEY missing",
            "description": "All Claude-powered engines fail silently. BUILD, BUILD_YOURSELF, SOLARPUNK_LOOP output nothing.",
            "fix": "Get key at console.anthropic.com → API Keys → Create → add as ANTHROPIC_API_KEY secret",
            "revenue_impact": "$0/day (AI brain offline)",
            "status": "PENDING"
        })
        bn_id += 1
    
    # Check Gumroad
    gumroad_secret = next((s for s in secrets if s["name"] == "GUMROAD_SECRET"), None)
    if gumroad_secret and not gumroad_secret["present"]:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "CRITICAL",
            "title": "GUMROAD_SECRET missing — no products can publish",
            "description": "GUMROAD_ENGINE has products ready but can't authenticate to Gumroad API.",
            "fix": "gumroad.com → avatar → Settings → Advanced → Generate Token → copy → GitHub Secret: GUMROAD_SECRET",
            "revenue_impact": f"${(gumroad['products'] * 17)}/day potential blocked",
            "status": "PENDING"
        })
        bn_id += 1
    
    if gumroad["products"] > 0 and gumroad["live"] == 0:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "HIGH",
            "title": f"{gumroad['products']} products seeded but 0 live on Gumroad",
            "description": "gumroad_listings.json has products but GUMROAD_ENGINE hasn't run successfully yet.",
            "fix": "Ensure GUMROAD_SECRET is set, then trigger OMNIBRAIN or run GUMROAD_ENGINE manually via RUN_NOW",
            "revenue_impact": "All product sales blocked",
            "status": "PENDING" if (gumroad_secret and not gumroad_secret["present"]) else "READY_TO_RUN"
        })
        bn_id += 1
    
    # Check Gmail
    gmail_pass = next((s for s in secrets if s["name"] == "GMAIL_APP_PASSWORD"), None)
    gmail_addr = next((s for s in secrets if s["name"] == "GMAIL_ADDRESS"), None)
    if gmail_addr and gmail_addr["present"] and gmail_pass and gmail_pass["present"]:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "MEDIUM",
            "title": "Gmail App Password may be account password (535 auth error)",
            "description": "Gmail requires an App Password (16 chars) not your account password. 2FA must be ON.",
            "fix": "Google Account → Security → 2-Step Verification → App Passwords → Generate for Mail → paste new value to GMAIL_APP_PASSWORD",
            "revenue_impact": "No email briefings, no payment notifications",
            "status": "VERIFY"
        })
        bn_id += 1
    
    # Check Twitter
    x_key = next((s for s in secrets if s["name"] == "X_API_KEY"), None)
    if not (x_key and x_key["present"]):
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "HIGH",
            "title": "Twitter/X keys missing — 24 queued posts stuck",
            "description": "SOCIAL_PROMOTER has 24 tweet drafts ready. No X_API_KEY = no auto-posting.",
            "fix": "developer.twitter.com → Projects → App → Keys → API Key + Secret + Access Token + Secret → add 4 secrets",
            "revenue_impact": "Zero Twitter distribution for products",
            "status": "PENDING"
        })
        bn_id += 1
    
    # Syntax errors
    broken = [e for e in engines if not e["syntax_ok"]]
    if broken:
        bottlenecks.append({
            "id": f"BN-{bn_id:03d}", "severity": "MEDIUM",
            "title": f"{len(broken)} engines have syntax errors",
            "description": f"Broken: {', '.join(e['name'] for e in broken[:5])}",
            "fix": "Run GUARDIAN to auto-detect and quarantine broken engines",
            "revenue_impact": "Broken engines skipped each cycle",
            "status": "KNOWN"
        })
        bn_id += 1
    
    return bottlenecks


def write_html_report(bottlenecks, secrets, engines, gumroad, revenue, now):
    """Write docs/bottleneck.html."""
    critical = [b for b in bottlenecks if b["severity"] == "CRITICAL"]
    high = [b for b in bottlenecks if b["severity"] == "HIGH"]
    
    secret_ok = sum(1 for s in secrets if s["present"])
    secret_total = len(secrets)
    engine_ok = sum(1 for e in engines if e["syntax_ok"])
    
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk™ Bottleneck Scanner</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060e;color:#dde;font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:20px 16px 60px}}
h1{{color:#ff5e5b;font-size:1.4rem;font-weight:900;margin-bottom:4px}}
.ts{{color:rgba(255,255,255,.25);font-size:.7rem;margin-bottom:20px}}
.stat-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px;margin-bottom:24px}}
.stat{{background:#0f0f1c;border:1px solid rgba(255,255,255,.07);border-radius:8px;padding:12px;text-align:center}}
.stat .n{{font-size:1.8rem;font-weight:800;display:block}}
.stat .l{{font-size:.65rem;color:rgba(255,255,255,.35);text-transform:uppercase;letter-spacing:1px}}
.red .n{{color:#ff5e5b}} .orange .n{{color:#ff9800}} .green .n{{color:#00ff88}} .blue .n{{color:#90caf9}}
.bn{{background:#0f0f1c;border-radius:10px;padding:16px;margin-bottom:10px;border-left:4px solid #333}}
.bn.CRITICAL{{border-left-color:#ff5e5b}} .bn.HIGH{{border-left-color:#ff9800}}
.bn.MEDIUM{{border-left-color:#ffd700}} .bn.LOW{{border-left-color:#444}}
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
<h1>⚡ Bottleneck Scanner</h1>
<p class="ts">Generated {now} · {len(bottlenecks)} blockers identified</p>

<div class="stat-row">
  <div class="stat red"><span class="n">{len(critical)}</span><span class="l">Critical</span></div>
  <div class="stat orange"><span class="n">{len(high)}</span><span class="l">High</span></div>
  <div class="stat green"><span class="n">{secret_ok}/{secret_total}</span><span class="l">Secrets OK</span></div>
  <div class="stat blue"><span class="n">{engine_ok}/{len(engines)}</span><span class="l">Engines OK</span></div>
  <div class="stat green"><span class="n">${revenue['total_to_gaza']:.2f}</span><span class="l">To Gaza</span></div>
  <div class="stat"><span class="n">{gumroad['live']}/{gumroad['products']}</span><span class="l">Gumroad Live</span></div>
</div>

<div class="section-title">🔴 Blockers (fix these to unblock revenue)</div>
"""
    for bn in bottlenecks:
        badge_class = bn['severity']
        html += f"""<div class="bn {bn['severity']}">
  <div class="bn-head">
    <span class="bn-title">{bn['id']} — {bn['title']}</span>
    <span class="badge {badge_class}">{bn['severity']}</span>
  </div>
  <div class="bn-desc">{bn['description']}</div>
  <div class="bn-fix">{bn['fix']}</div>
</div>
"""
    
    html += """<div class="section-title">→ After fixing blockers: trigger Actions → OMNIBRAIN (workflow_dispatch)</div>
</body></html>"""
    
    (DOCS / "bottleneck.html").write_text(html)
    print(f"  📄 Wrote docs/bottleneck.html")


def run():
    print("BOTTLENECK_SCANNER running...")
    now = datetime.now(timezone.utc).isoformat()
    
    secrets = check_secrets()
    engines = check_engines()
    gumroad = check_gumroad_listings()
    revenue = check_revenue()
    bottlenecks = identify_bottlenecks(secrets, engines, gumroad, revenue)
    
    report = {
        "generated": now,
        "summary": {
            "total_bottlenecks": len(bottlenecks),
            "critical": len([b for b in bottlenecks if b["severity"] == "CRITICAL"]),
            "high": len([b for b in bottlenecks if b["severity"] == "HIGH"]),
            "secrets_ok": sum(1 for s in secrets if s["present"]),
            "secrets_total": len(secrets),
            "engines_ok": sum(1 for e in engines if e["syntax_ok"]),
            "engines_total": len(engines),
            "gumroad_live": gumroad["live"],
            "gumroad_pending": gumroad["products"] - gumroad["live"],
            "revenue_total": revenue["total_received"],
            "gaza_total": revenue["total_to_gaza"],
        },
        "bottlenecks": bottlenecks,
        "secrets": secrets,
    }
    
    (DATA / "bottleneck_report.json").write_text(json.dumps(report, indent=2))
    write_html_report(bottlenecks, engines, gumroad, revenue, now)
    
    critical_count = report["summary"]["critical"]
    high_count = report["summary"]["high"]
    
    if critical_count == 0:
        print(f"  ✅ No critical blockers! {high_count} high-priority items.")
    else:
        print(f"  🔴 {critical_count} CRITICAL blockers found!")
        for bn in bottlenecks:
            if bn["severity"] == "CRITICAL":
                print(f"     → {bn['title']}")
                print(f"       FIX: {bn['fix']}")
    
    print(f"  Secrets: {report['summary']['secrets_ok']}/{report['summary']['secrets_total']} configured")
    print(f"  Engines: {report['summary']['engines_ok']}/{report['summary']['engines_total']} syntax OK")
    print(f"  Gumroad: {report['summary']['gumroad_live']} live / {report['summary']['gumroad_pending']} pending")
    print(f"  Revenue: ${report['summary']['revenue_total']:.2f} total | ${report['summary']['gaza_total']:.2f} to Gaza")


if __name__ == "__main__": run()
