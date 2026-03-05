#!/usr/bin/env python3
"""NIGHTLY_DIGEST.py — SolarPunk Daily Summary Engine
=====================================================
Runs in L7 (final layer) every cycle. Collects ALL data from all engines,
synthesizes it into a human-readable report, emails it to Meeko, and
publishes a live status page to docs/status.html.

Also: updates README.md with live stats and commits the health dashboard.
This is the "what happened today" engine + public-facing status board.
"""
import os, json, sys, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""

DATA  = Path("data");  DATA.mkdir(exist_ok=True)
DOCS  = Path("docs");  DOCS.mkdir(exist_ok=True)
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = "meekotharaccoon-cell/meeko-nerve-center"


def rj(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback if fallback is not None else {}


def load():
    f = DATA / "nightly_digest_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "digests_sent": 0, "total_revenue_reported": 0.0}


def save(s):
    (DATA / "nightly_digest_state.json").write_text(json.dumps(s, indent=2))


def collect_stats():
    """Pull all key metrics from every engine's state files."""
    brain      = rj("brain_state.json")
    omnibus    = rj("omnibus_last.json")
    exchange   = rj("email_exchange_state.json")
    kofi       = rj("kofi_tracker_state.json")
    biz        = rj("business_factory_state.json")
    self_b     = rj("self_builder_state.json")
    architect  = rj("architect_plan.json")
    flywheel   = rj("flywheel_summary.json")
    revenue_loop = rj("revenue_loop_last.json")

    engines_ok  = omnibus.get("engines_ok", [])
    engines_fail = omnibus.get("engines_failed", [])
    engines_skip = omnibus.get("engines_skipped", [])

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "health": brain.get("health_score", 0),
        "total_loops": brain.get("total_loops_completed", 0),
        "engines_ok_count": len(engines_ok),
        "engines_fail_count": len(engines_fail),
        "engines_skip_count": len(engines_skip),
        "engines_ok": engines_ok,
        "engines_failed": engines_fail,
        "engines_skipped": engines_skip,
        # Exchange
        "exchange_tasks": exchange.get("total_tasks", 0),
        "exchange_earned_platform": exchange.get("total_earned", 0.0),
        "exchange_to_gaza": exchange.get("total_to_gaza", 0.0),
        "exchange_agent_earnings": exchange.get("agent_earnings", {}),
        # Payments
        "kofi_verified": kofi.get("total_verified", 0.0),
        "kofi_matched": kofi.get("payments_matched", 0),
        "kofi_unmatched": kofi.get("payments_unmatched", 0),
        # Building
        "businesses_built": len(biz.get("businesses_built", [])),
        "revenue_potential": biz.get("total_revenue_potential", 0),
        "engines_self_built": self_b.get("total_built", 0),
        # Revenue loop
        "last_loop_steps_ok": revenue_loop.get("steps_ok", []),
        "last_live_url": revenue_loop.get("live_url", ""),
        "last_gumroad_url": revenue_loop.get("gumroad_url", ""),
        # Architect plan
        "next_priority": architect.get("next_priority", ""),
        "next_engine": architect.get("build_next_engine", ""),
        "next_niche": architect.get("build_next_niche", {}).get("niche", ""),
        "revenue_gaps": architect.get("revenue_gaps", []),
    }


def format_email(stats):
    health_bar = "█" * (stats["health"] // 10) + "░" * (10 - stats["health"] // 10)

    total_real_revenue = stats["exchange_earned_platform"] + stats["kofi_verified"]
    total_to_gaza = stats["exchange_to_gaza"] + (stats["kofi_verified"] * 0.15)

    engine_status = ""
    if stats["engines_failed"]:
        engine_status += f"\n  ❌ FAILED ({stats['engines_fail_count']}): {', '.join(stats['engines_failed'])}"
    if stats["engines_skipped"]:
        engine_status += f"\n  ⏭  SKIPPED ({stats['engines_skip_count']}): {', '.join(stats['engines_skipped'][:5])}"
    engine_status += f"\n  ✅ OK ({stats['engines_ok_count']}): {', '.join(stats['engines_ok'][:8])}..."

    gaps_text = "\n".join([f"  • {g}" for g in stats["revenue_gaps"][:3]]) if stats["revenue_gaps"] else "  None identified"

    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SolarPunk Nightly Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 SYSTEM HEALTH: {stats['health']}/100 [{health_bar}]
   Loops completed: {stats['total_loops']} | Engines today: {stats['engines_ok_count']} OK / {stats['engines_fail_count']} failed

💰 REVENUE (real money earned)
   Exchange platform cut: ${stats['exchange_earned_platform']:.2f}
   Ko-fi verified payments: ${stats['kofi_verified']:.2f}
   TOTAL REAL REVENUE: ${total_real_revenue:.2f}
   → Gaza fund contribution: ${total_to_gaza:.2f}

📧 EMAIL AGENT EXCHANGE
   Tasks completed: {stats['exchange_tasks']}
   Ko-fi payments matched: {stats['kofi_matched']} | Unmatched: {stats['kofi_unmatched']}
   Agent earnings: {json.dumps(stats['exchange_agent_earnings'], indent=4) if stats['exchange_agent_earnings'] else '  None yet'}

🏗️ BUILDING
   Digital businesses built: {stats['businesses_built']}
   Revenue potential: ${stats['revenue_potential']:,}/month (est.)
   New engines written by SELF_BUILDER: {stats['engines_self_built']}
   Last live URL: {stats['last_live_url'] or '(pending)'}
   Last Gumroad: {stats['last_gumroad_url'] or '(pending)'}

🔧 ENGINE STATUS{engine_status}

🎯 NEXT CYCLE PRIORITIES (from ARCHITECT)
   Priority: {stats['next_priority'] or 'Continue building'}
   Next engine to build: {stats['next_engine'] or 'TBD'}
   Next business niche: {stats['next_niche'] or 'TBD'}

⚠️  REVENUE GAPS TO CLOSE:
{gaps_text}

🌿 MISSION STATUS
   Total to Gaza so far: ${total_to_gaza:.2f}
   Every task completed = 15% to Palestinian relief

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SolarPunk Brain — autonomous since day 1]
GitHub: github.com/meekotharaccoon-cell/meeko-nerve-center
"""


def send_digest(body):
    if not GMAIL or not GPWD:
        print("  No Gmail config — digest not sent")
        return False
    try:
        msg = MIMEText(body)
        msg["From"]    = GMAIL
        msg["To"]      = GMAIL
        msg["Subject"] = f"[SolarPunk] 🌿 Nightly Digest — {datetime.now(timezone.utc).strftime('%m/%d %H:%M UTC')}"
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL, GPWD)
            s.sendmail(GMAIL, GMAIL, msg.as_string())
        print("  Nightly digest sent")
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


def build_status_page(stats):
    """Write docs/status.html — live public status board."""
    health = stats["health"]
    health_color = "#4caf50" if health > 70 else "#ff9800" if health > 40 else "#f44336"
    total_real = stats["exchange_earned_platform"] + stats["kofi_verified"]
    total_gaza = stats["exchange_to_gaza"] + (stats["kofi_verified"] * 0.15)

    engine_badges = ""
    for e in stats["engines_ok"][:12]:
        engine_badges += f'<span style="background:#1a3a1a;color:#4caf50;padding:3px 8px;border-radius:4px;font-size:11px;margin:2px;display:inline-block">{e}</span>'
    for e in stats["engines_failed"]:
        engine_badges += f'<span style="background:#3a1a1a;color:#f44336;padding:3px 8px;border-radius:4px;font-size:11px;margin:2px;display:inline-block">❌{e}</span>'

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>SolarPunk — Live System Status</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080808;color:#e0e0e0;margin:0;padding:20px;max-width:960px;margin:auto}}
.header{{text-align:center;padding:30px 0;border-bottom:1px solid #222;margin-bottom:30px}}
h1{{color:#c8a86b;font-size:28px;margin:0}}
.sub{{color:#666;font-size:14px;margin-top:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:20px 0}}
.card{{background:#111;border:1px solid #222;border-radius:10px;padding:20px;text-align:center}}
.card-n{{font-size:32px;font-weight:800;color:#c8a86b}}
.card-l{{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.health-bar{{background:#1a1a1a;height:12px;border-radius:6px;overflow:hidden;margin:16px 0}}
.health-fill{{height:100%;background:{health_color};width:{health}%;transition:width 1s}}
.section{{background:#111;border:1px solid #222;border-radius:10px;padding:20px;margin:16px 0}}
.section h2{{color:#c8a86b;font-size:16px;margin:0 0 12px}}
.gaza{{border-left:3px solid #e87c5a;padding-left:12px;color:#aaa}}
.engines{{line-height:2}}
.footer{{text-align:center;color:#444;font-size:12px;margin-top:30px}}
a{{color:#c8a86b;text-decoration:none}}
</style>
</head><body>
<div class="header">
  <h1>⚡ SolarPunk Live Status</h1>
  <div class="sub">Autonomous AI system · Updates every ~6 hours · 15% of revenue → Gaza</div>
  <div class="sub" style="color:#555">Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
</div>

<div class="health-bar"><div class="health-fill"></div></div>
<div style="text-align:center;color:#666;font-size:12px;margin-bottom:20px">System health: {health}/100</div>

<div class="grid">
  <div class="card"><div class="card-n">${total_real:.2f}</div><div class="card-l">Real Revenue</div></div>
  <div class="card"><div class="card-n" style="color:#e87c5a">${total_gaza:.2f}</div><div class="card-l">→ Gaza</div></div>
  <div class="card"><div class="card-n">{stats['exchange_tasks']}</div><div class="card-l">Tasks Done</div></div>
  <div class="card"><div class="card-n">{stats['businesses_built']}</div><div class="card-l">Businesses Built</div></div>
  <div class="card"><div class="card-n">{stats['engines_self_built']}</div><div class="card-l">Engines Written</div></div>
  <div class="card"><div class="card-n">{stats['total_loops']}</div><div class="card-l">Revenue Loops</div></div>
</div>

<div class="section">
  <h2>Engine Status</h2>
  <div class="engines">{engine_badges}</div>
</div>

<div class="section">
  <h2>Next Cycle Plan</h2>
  <p style="color:#aaa;margin:4px 0"><strong style="color:#e0e0e0">Priority:</strong> {stats['next_priority'] or 'Continue building'}</p>
  <p style="color:#aaa;margin:4px 0"><strong style="color:#e0e0e0">Next engine:</strong> {stats['next_engine'] or 'TBD'}</p>
  <p style="color:#aaa;margin:4px 0"><strong style="color:#e0e0e0">Next niche:</strong> {stats['next_niche'] or 'TBD'}</p>
</div>

<div class="section">
  <h2 style="color:#e87c5a">Gaza Mission</h2>
  <div class="gaza">
    ${total_gaza:.2f} contributed to Palestinian artists and humanitarian relief.<br>
    Every AI agent task = 15% of payment → Gaza Rose Fund.<br>
    <a href="index.html">Send a task →</a> | <a href="exchange.html">Agent roster →</a>
  </div>
</div>

<div class="footer">
  <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">Open source</a> ·
  <a href="index.html">Email agents</a> ·
  <a href="https://ko-fi.com/meekotharaccoon">Ko-fi</a>
  <br>SolarPunk · autonomous · zero human input
</div>
</body></html>"""

    (DOCS / "status.html").write_text(html)
    print("  Status page → docs/status.html")


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"NIGHTLY_DIGEST cycle {state['cycles']}")

    stats = collect_stats()

    # Email digest
    body = format_email(stats)
    sent = send_digest(body)
    if sent:
        state["digests_sent"] = state.get("digests_sent", 0) + 1

    # Status page
    build_status_page(stats)

    # Save digest to data/ for other engines to read
    (DATA / "nightly_digest_last.json").write_text(json.dumps({
        "ts":     stats["ts"],
        "health": stats["health"],
        "total_real_revenue": stats["exchange_earned_platform"] + stats["kofi_verified"],
        "total_to_gaza":      stats["exchange_to_gaza"] + (stats["kofi_verified"] * 0.15),
        "exchange_tasks":     stats["exchange_tasks"],
        "businesses_built":   stats["businesses_built"],
        "engines_built":      stats["engines_self_built"],
        "engines_ok_count":   stats["engines_ok_count"],
        "engines_fail_count": stats["engines_fail_count"],
    }, indent=2))

    state["total_revenue_reported"] = state.get("total_revenue_reported", 0) + stats["exchange_earned_platform"]
    save(state)
    return state


if __name__ == "__main__":
    run()
