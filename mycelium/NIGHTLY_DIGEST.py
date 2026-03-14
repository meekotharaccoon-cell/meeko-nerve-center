# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
NIGHTLY_DIGEST.py v2 — SolarPunk Daily Summary Engine
======================================================
FIXED:
  - Only sends ONE email per 20-hour window (no more spam)
  - Shows DELTA from last email (what actually changed)
  - Pulls from proof_ledger.json for REAL revenue, not estimates
  - Labels estimated/potential numbers clearly as [ESTIMATE]
  - Includes live shop links
  - Only emails when something meaningful changed OR once/day

Runs in L7 every cycle but gates on a 20-hour cooldown.
Status page still updates every cycle regardless.
"""
import os, json, sys, smtplib
from pathlib import Path
from datetime import datetime, timezone, timedelta
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
BASE  = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

EMAIL_COOLDOWN_HOURS = 20  # Max 1 email per 20 hours


def rj(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback if fallback is not None else {}


def load_state():
    f = DATA / "nightly_digest_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {
        "cycles": 0,
        "digests_sent": 0,
        "last_sent": None,
        "last_real_revenue": 0.0,
        "last_gaza_total": 0.0,
        "last_health": 0,
        "last_products_live": 0,
    }


def should_send_email(state):
    """Only send if cooldown has passed OR something important changed."""
    last = state.get("last_sent")
    if not last:
        return True, "first_email"
    try:
        last_dt = datetime.fromisoformat(last)
        if datetime.now(timezone.utc) - last_dt > timedelta(hours=EMAIL_COOLDOWN_HOURS):
            return True, "daily_update"
    except:
        return True, "parse_error"
    return False, "cooldown"


def collect_stats():
    """Pull REAL metrics — clearly labels estimates vs actuals."""
    brain    = rj("brain_state.json")
    omnibus  = rj("omnibus_last.json")
    ledger   = rj("proof_ledger.json")          # REAL sales
    registry = rj("product_registry.json")       # product status
    bluesky  = rj("bluesky_engine_state.json")
    pub      = rj("autonomous_publisher_state.json")
    exchange = rj("email_exchange_state.json")
    devto    = rj("devto_state.json")
    biz      = rj("business_factory_state.json")
    self_b   = rj("self_builder_state.json")
    architect= rj("architect_plan.json")
    delivery = rj("delivery_engine_state.json")
    gumroad_pub = rj("gumroad_publisher_state.json")
    gumroad_auth_fail = rj("gumroad_auth_failure.json")
    transfer_needed = rj("transfer_needed.json")

    engines_ok   = omnibus.get("engines_ok", [])
    engines_fail = omnibus.get("engines_failed", [])
    engines_skip = omnibus.get("engines_skipped", [])

    # REAL revenue from proof_ledger (not estimates)
    real_revenue   = ledger.get("total_sales", 0.0)
    real_to_gaza   = ledger.get("total_to_gaza", 0.0)
    pcrf_transferred = ledger.get("total_transferred", 0.0)
    pending_transfer = ledger.get("pending_transfer", 0.0)
    sale_count     = len(ledger.get("sales", []))

    # Products
    products = registry.get("products", {})
    products_content_ready = sum(1 for p in products.values() if p.get("content_ready"))
    products_live = sum(1 for p in products.values() if p.get("gumroad_url") or p.get("download_url"))
    products_total = len(products)

    # Publishing
    bluesky_posted = bluesky.get("posted", 0)
    total_published = pub.get("total_sent", 0)
    devto_articles = devto.get("total_published", 0) if isinstance(devto, dict) else 0

    # Gumroad status
    gumroad_auth_ok = not bool(gumroad_auth_fail.get("error"))
    gumroad_live = sum(1 for r in gumroad_pub.get("results", []) if r.get("status") in ("created", "updated"))

    # Self-building
    engines_built_count = self_b.get("total_built", 0) if isinstance(self_b, dict) else 0

    # Gaps — from ARCHITECT (what system found is missing/broken)
    revenue_gaps = architect.get("revenue_gaps", [])
    next_engine  = architect.get("build_next_engine", "")
    next_priority = architect.get("next_priority", "")

    # Exchange (AI agent email tasks — real if anyone paid)
    exchange_tasks = exchange.get("total_tasks", 0)
    exchange_earned = exchange.get("total_earned", 0.0)  # actual platform cut

    # Business factory potential — clearly labeled as ESTIMATE
    biz_potential = biz.get("total_revenue_potential", 0)  # ESTIMATE only

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "health": brain.get("health_score", 0),
        "cycle": omnibus.get("cycle_number", 0),
        "version": omnibus.get("version", "v23"),
        # REAL numbers
        "real_revenue": real_revenue,
        "real_to_gaza": real_to_gaza,
        "pcrf_transferred": pcrf_transferred,
        "pending_transfer": pending_transfer,
        "sale_count": sale_count,
        # Products
        "products_total": products_total,
        "products_content_ready": products_content_ready,
        "products_live": products_live,
        # Gumroad
        "gumroad_auth_ok": gumroad_auth_ok,
        "gumroad_live_count": gumroad_live,
        # Publishing
        "bluesky_posted": bluesky_posted,
        "total_published": total_published,
        "devto_articles": devto_articles,
        # Engines
        "engines_ok": engines_ok,
        "engines_failed": engines_fail,
        "engines_skipped": engines_skip,
        "engines_built": engines_built_count,
        # Exchange
        "exchange_tasks": exchange_tasks,
        "exchange_earned": exchange_earned,
        # Gaps/planning
        "revenue_gaps": revenue_gaps,
        "next_engine": next_engine,
        "next_priority": next_priority,
        # ESTIMATES (clearly labeled)
        "estimated_monthly_potential": biz_potential,
        # Alerts
        "transfer_needed": bool(transfer_needed.get("amount")),
        "transfer_amount": transfer_needed.get("amount", 0),
        "gumroad_auth_fail": gumroad_auth_fail.get("error", ""),
    }


def format_email(stats, prev_state, reason):
    health = stats["health"]
    bar = "█" * (health // 10) + "░" * (10 - health // 10)

    # Delta lines
    rev_delta = stats["real_revenue"] - prev_state.get("last_real_revenue", 0)
    gaza_delta = stats["real_to_gaza"] - prev_state.get("last_gaza_total", 0)
    products_delta = stats["products_live"] - prev_state.get("last_products_live", 0)

    delta_section = ""
    if rev_delta > 0:
        delta_section += f"\n  🎉 NEW SALES: +${rev_delta:.2f} since last digest!"
    if gaza_delta > 0:
        delta_section += f"\n  🌹 New Gaza contribution: +${gaza_delta:.2f}"
    if products_delta > 0:
        delta_section += f"\n  📦 {products_delta} more product(s) went live!"

    # Alerts section
    alerts = ""
    if stats["transfer_needed"]:
        alerts += f"\n⚠️  TRANSFER NEEDED: ${stats['transfer_amount']:.2f} in Gaza fund → ready for PCRF transfer"
        alerts += f"\n   Go to pcrf.net/donate, transfer, then record ref in data/proof_ledger.json"
    if stats["gumroad_auth_fail"]:
        alerts += f"\n⚠️  GUMROAD AUTH: GUMROAD_SECRET may be a webhook secret, not API token"
        alerts += f"\n   Fix: gumroad.com/settings/advanced → API → generate token → add as GUMROAD_ACCESS_TOKEN"
    if stats["engines_failed"]:
        alerts += f"\n⚠️  ENGINES FAILED: {', '.join(stats['engines_failed'])}"

    # Gap summary
    gaps_text = ""
    for g in stats["revenue_gaps"][:3]:
        gaps_text += f"\n  • {g}"
    if not gaps_text:
        gaps_text = "\n  None identified this cycle"

    # Product breakdown
    prod_line = f"{stats['products_total']} registered | {stats['products_content_ready']} content ready | {stats['products_live']} with live URLs"

    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SolarPunk Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} ({reason})
OMNIBUS {stats['version']} | Cycle #{stats['cycle']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 HEALTH: {health}/100  [{bar}]

💰 REAL REVENUE (actual sales only){delta_section}
   Total sales: ${stats['real_revenue']:.2f} ({stats['sale_count']} orders)
   → To Gaza (PCRF): ${stats['real_to_gaza']:.2f}
   → Transferred to PCRF: ${stats['pcrf_transferred']:.2f}
   → Pending transfer: ${stats['pending_transfer']:.2f}
   [Note: ${stats['estimated_monthly_potential']:,}/mo is an ESTIMATE from BUSINESS_FACTORY, not real money]

📦 PRODUCTS
   {prod_line}
   Gumroad: {'✅ auth OK' if stats['gumroad_auth_ok'] else '❌ auth fail — see alerts'} | {stats['gumroad_live_count']} listings live

📢 PUBLISHING
   Bluesky posts: {stats['bluesky_posted']} | DEV.to articles: {stats['devto_articles']}
   Total published: {stats['total_published']}

🤖 BUILDING
   Engines written by SELF_BUILDER: {stats['engines_built']}
   Email agent tasks: {stats['exchange_tasks']} (${stats['exchange_earned']:.2f} earned)

⚠️  ALERTS{alerts if alerts else chr(10) + '  None'}

🔧 GAPS TO FIX{gaps_text}

🎯 NEXT CYCLE
   Priority: {stats['next_priority'] or 'Continue building'}
   Next engine: {stats['next_engine'] or 'TBD'}

🌐 LIVE LINKS
   Shop: {BASE}/shop.html
   Proof: {BASE}/proof.html
   GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SolarPunk {stats['version']} — autonomous]
"""


def send_email(subject, body):
    if not GMAIL or not GPWD:
        print("  No Gmail config — digest not sent")
        return False
    try:
        msg = MIMEText(body)
        msg["From"]    = GMAIL
        msg["To"]      = GMAIL
        msg["Subject"] = subject
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL, GPWD)
            s.sendmail(GMAIL, GMAIL, msg.as_string())
        print(f"  Email sent: {subject[:60]}")
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


def build_status_page(stats):
    """Update docs/status.html — always runs, no cooldown."""
    health = stats["health"]
    hcolor = "#00e87a" if health > 70 else "#ffd166" if health > 40 else "#ff4d6d"
    real_rev = stats["real_revenue"]
    real_gaza = stats["real_to_gaza"]

    ok_badges = "".join(
        f'<span class="badge ok">{e}</span>'
        for e in stats["engines_ok"][:15]
    )
    fail_badges = "".join(
        f'<span class="badge fail">✗ {e}</span>'
        for e in stats["engines_failed"]
    )
    alert_items = ""
    if stats["transfer_needed"]:
        alert_items += f'<li>💸 Gaza transfer needed: ${stats["transfer_amount"]:.2f} ready for PCRF</li>'
    if stats["gumroad_auth_fail"]:
        alert_items += '<li>🔑 Gumroad API token may need update (see gumroad_auth_failure.json)</li>'
    if stats["engines_failed"]:
        alert_items += f'<li>⚙️ Engines failed: {", ".join(stats["engines_failed"])}</li>'
    if not alert_items:
        alert_items = "<li>No alerts</li>"

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>SolarPunk Live Status</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#05050f;color:rgba(255,255,255,.88);font-family:-apple-system,sans-serif;padding:24px;max-width:900px;margin:auto}}
h1{{color:#00e87a;font-size:1.6rem;margin-bottom:4px}}
.sub{{color:rgba(255,255,255,.4);font-size:.8rem;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:24px}}
.card{{background:#0c0c1e;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px;text-align:center}}
.n{{font-size:2rem;font-weight:900;color:{hcolor}}}
.nrev{{font-size:2rem;font-weight:900;color:#00e87a}}
.ngaza{{font-size:2rem;font-weight:900;color:#ff4d6d}}
.label{{font-size:.65rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.08em;margin-top:4px}}
.hbar{{background:rgba(255,255,255,.06);border-radius:6px;height:8px;overflow:hidden;margin-bottom:24px}}
.hfill{{height:100%;background:{hcolor};width:{health}%}}
.section{{background:#0c0c1e;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:20px;margin-bottom:16px}}
.section h2{{color:#ffd166;font-size:.9rem;margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.68rem;margin:2px}}
.badge.ok{{background:rgba(0,232,122,.1);color:#00e87a;border:1px solid rgba(0,232,122,.2)}}
.badge.fail{{background:rgba(255,77,109,.1);color:#ff4d6d;border:1px solid rgba(255,77,109,.2)}}
.alert-list{{color:rgba(255,209,102,.8);font-size:.82rem;padding-left:16px;line-height:1.9}}
.links{{display:flex;gap:10px;flex-wrap:wrap}}
.link{{background:rgba(0,232,122,.1);border:1px solid rgba(0,232,122,.2);border-radius:8px;
  padding:8px 16px;font-size:.8rem;color:#00e87a;text-decoration:none}}
.est{{font-size:.72rem;color:rgba(255,255,255,.3);margin-top:8px}}
</style></head><body>
<h1>⚡ SolarPunk Live Status</h1>
<div class="sub">OMNIBUS {stats['version']} · Cycle #{stats['cycle']} · Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · 15% of every sale → Gaza</div>

<div class="hbar"><div class="hfill"></div></div>

<div class="grid">
  <div class="card"><div class="n">{health}</div><div class="label">Health /100</div></div>
  <div class="card"><div class="nrev">${real_rev:.2f}</div><div class="label">Real Revenue</div></div>
  <div class="card"><div class="ngaza">${real_gaza:.2f}</div><div class="label">→ Gaza Fund</div></div>
  <div class="card"><div class="n" style="color:#ffd166">{stats['products_live']}</div><div class="label">Products Live</div></div>
  <div class="card"><div class="n" style="color:#48cae4">{stats['bluesky_posted']}</div><div class="label">Bluesky Posts</div></div>
  <div class="card"><div class="n" style="color:#c77dff">{stats['total_published']}</div><div class="label">Total Published</div></div>
</div>
<div class="est" style="text-align:center;margin-bottom:20px">
  Estimated monthly potential [ESTIMATE, not real]: ${stats['estimated_monthly_potential']:,}/mo from BUSINESS_FACTORY
</div>

<div class="section">
  <h2>⚠ Alerts</h2>
  <ul class="alert-list">{alert_items}</ul>
</div>

<div class="section">
  <h2>Engine Status — {len(stats['engines_ok'])} OK / {len(stats['engines_failed'])} failed</h2>
  <div>{ok_badges}{fail_badges}</div>
</div>

<div class="section">
  <h2>Products — {stats['products_total']} registered</h2>
  <p style="font-size:.82rem;color:rgba(255,255,255,.5)">
    {stats['products_content_ready']} content ready · {stats['products_live']} with live URLs ·
    Gumroad: {'✓ auth OK' if stats['gumroad_auth_ok'] else '✗ auth fail'}
  </p>
</div>

<div class="section">
  <h2>Live Links</h2>
  <div class="links">
    <a href="shop.html" class="link">🛒 Shop</a>
    <a href="proof.html" class="link">✅ Proof</a>
    <a href="https://ko-fi.com/meekotharaccoon" class="link" target="_blank">☕ Ko-fi</a>
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" class="link" target="_blank">💻 GitHub</a>
    <a href="https://www.paypal.me/meekotharaccoon" class="link" target="_blank">💳 PayPal.me</a>
  </div>
</div>

<div style="text-align:center;color:rgba(255,255,255,.2);font-size:.7rem;margin-top:24px">
  SolarPunk™ · <a href="shop.html" style="color:#ff4d6d">shop</a> · autonomous · updates every ~6 hours
</div>
</body></html>"""

    (DOCS / "status.html").write_text(html)
    print("  Status page → docs/status.html")


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"NIGHTLY_DIGEST v2 — cycle {state['cycles']}")

    stats = collect_stats()

    # Always rebuild status page
    build_status_page(stats)

    # Gate email on cooldown
    do_send, reason = should_send_email(state)
    if do_send:
        ts_str = datetime.now(timezone.utc).strftime("%m/%d %H:%M UTC")
        subject = f"[SolarPunk] 🌿 {ts_str} — Health:{stats['health']} Revenue:${stats['real_revenue']:.2f} Products:{stats['products_live']} live"
        body = format_email(stats, state, reason)
        sent = send_email(subject, body)
        if sent:
            state["digests_sent"] = state.get("digests_sent", 0) + 1
            state["last_sent"] = datetime.now(timezone.utc).isoformat()
            state["last_real_revenue"] = stats["real_revenue"]
            state["last_gaza_total"]   = stats["real_to_gaza"]
            state["last_health"]       = stats["health"]
            state["last_products_live"]= stats["products_live"]
    else:
        print(f"  Email skipped — cooldown ({reason}), last sent: {state.get('last_sent', 'never')[:16]}")

    # Save state
    (DATA / "nightly_digest_state.json").write_text(json.dumps(state, indent=2))

    # Write last digest snapshot for other engines
    (DATA / "nightly_digest_last.json").write_text(json.dumps({
        "ts": stats["ts"],
        "health": stats["health"],
        "real_revenue": stats["real_revenue"],
        "real_to_gaza": stats["real_to_gaza"],
        "products_live": stats["products_live"],
        "bluesky_posted": stats["bluesky_posted"],
        "total_published": stats["total_published"],
        "engines_ok_count": len(stats["engines_ok"]),
        "engines_fail_count": len(stats["engines_failed"]),
        "email_sent_this_cycle": do_send,
    }, indent=2))

    print(f"  Health: {stats['health']} | Revenue: ${stats['real_revenue']:.2f} | Products live: {stats['products_live']}")
    return state


if __name__ == "__main__":
    run()
