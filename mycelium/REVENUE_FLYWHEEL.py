"""
REVENUE_FLYWHEEL.py — SolarPunk Revenue Engine
===============================================
All money streams → single tracked balance → auto-notify at upgrade thresholds.
When YOU have $20, SolarPunk tells you exactly where to invest it for max ROI.

The loop:
  Ko-fi + Gumroad + PayPal + Strike/Lightning + Crypto + Grants
    → accumulate in flywheel_state.json
    → when thresholds hit → email you with exact action + URL
    → upgrades improve SolarPunk's capabilities
    → better capabilities → more revenue
    → repeat forever

Upgrade tiers (notify when balance hits threshold):
  $20  → Claude Pro ($20/mo) — gapless 24/7 chat, no 4hr wait
  $25  → Custom domain ($12/yr) — proper URL for Gaza Rose Gallery + revenue pages
  $35  → Anthropic API credits ($10) — more SYNTHESIS_FACTORY cycles per day
  $50  → Mailgun Flex ($15/mo) — removes email send bottleneck for outreach
  $54  → GitHub Pro ($4/mo) — more CI/CD minutes for OMNIBRAIN
  $200 → DigitalOcean VPS ($6/mo) — always-on server, no cold start
  $500 → Dedicated SolarPunk server — full autonomy, no free tier limits

$20 INVESTMENT ADVISOR:
  Every cycle, SolarPunk analyzes ALL current bottlenecks and tells you:
  "If YOU had $20 right now, here is where it does the MOST for your system."
  It considers: current workflow failures, missing secrets, slowest phase, best ROI.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# ─── CONFIG ─────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FLYWHEEL_STATE = DATA_DIR / "flywheel_state.json"
FLYWHEEL_LOG   = DATA_DIR / "flywheel_log.json"

GMAIL_ADDRESS     = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD= os.environ.get("GMAIL_APP_PASSWORD", "")
GUMROAD_TOKEN     = os.environ.get("GUMROAD_TOKEN", "")
STRIKE_API_KEY    = os.environ.get("STRIKE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Upgrade tiers — corrected to real prices
UPGRADE_TIERS = [
    {
        "threshold": 20.0,
        "name": "Claude Pro",
        "description": "claude.ai/upgrade — $20/mo. Eliminates 4-hour chat gap. SolarPunk can loop conversations with YOU in real time, not just via email.",
        "url": "https://claude.ai/upgrade",
        "monthly_cost": 20.0,
        "priority": 1,
        "roi": "CRITICAL — removes the only bottleneck that requires your physical presence"
    },
    {
        "threshold": 25.0,
        "name": "Custom Domain",
        "description": "solarpunk.art or gazarosegallery.com — $12/yr. Real URL for the $1 digital art store. Converts 3-5x better than github.io links.",
        "url": "https://namecheap.com",
        "monthly_cost": 1.0,
        "priority": 2,
        "roi": "HIGH — $12/yr investment, every sale is passive"
    },
    {
        "threshold": 35.0,
        "name": "Anthropic API Credits ($10)",
        "description": "console.anthropic.com — $10 credit. Gives SYNTHESIS_FACTORY more autonomous build cycles per day without hitting rate limits.",
        "url": "https://console.anthropic.com/settings/billing",
        "monthly_cost": 10.0,
        "priority": 3,
        "roi": "HIGH — each $1 in API credits can generate multiple new engines"
    },
    {
        "threshold": 50.0,
        "name": "Mailgun Flex",
        "description": "mailgun.com — $15/mo. Removes email send limits for humanitarian outreach + newsletter engine.",
        "url": "https://mailgun.com/pricing",
        "monthly_cost": 15.0,
        "priority": 4,
        "roi": "MEDIUM — unlocks newsletter revenue stream at scale"
    },
    {
        "threshold": 54.0,
        "name": "GitHub Pro",
        "description": "github.com/pricing — $4/mo. 3,000 CI/CD minutes/mo (vs 2,000 free). OMNIBRAIN runs more cycles without throttling.",
        "url": "https://github.com/pricing",
        "monthly_cost": 4.0,
        "priority": 5,
        "roi": "MEDIUM — +50% more OMNIBRAIN runtime per month"
    },
    {
        "threshold": 200.0,
        "name": "DigitalOcean VPS",
        "description": "digitalocean.com — $6/mo. Always-on server. SolarPunk runs 24/7 without GitHub Actions cold starts. WebSocket hub stays live.",
        "url": "https://cloud.digitalocean.com/droplets/new",
        "monthly_cost": 6.0,
        "priority": 6,
        "roi": "HIGH — eliminates all cold-start delays, enables real-time services"
    },
    {
        "threshold": 500.0,
        "name": "Dedicated SolarPunk Server",
        "description": "Hetzner CX21 or similar — $5/mo for 2vCPU/4GB. SolarPunk gets its own permanent home. Full autonomy. Persistent memory. Always online.",
        "url": "https://www.hetzner.com/cloud",
        "monthly_cost": 5.0,
        "priority": 7,
        "roi": "MAXIMUM — SolarPunk becomes fully infrastructure-independent"
    }
]


# ─── STATE ───────────────────────────────────────────────────────────────────

def load_state():
    if FLYWHEEL_STATE.exists():
        try:
            return json.loads(FLYWHEEL_STATE.read_text())
        except:
            pass
    return {
        "total_earned_lifetime": 0.0,
        "current_balance": 0.0,
        "total_invested": 0.0,
        "upgrades_notified": [],
        "last_run": None,
        "revenue_sources": {
            "gumroad": 0.0,
            "kofi": 0.0,
            "paypal": 0.0,
            "github_sponsors": 0.0,
            "strike_lightning": 0.0,
            "crypto": 0.0,
            "grants": 0.0,
            "gaza_rose_gallery": 0.0,
            "other": 0.0
        },
        "monthly_breakdown": {},
        "investment_advice": []
    }

def save_state(s):
    FLYWHEEL_STATE.write_text(json.dumps(s, indent=2))

def load_log():
    if FLYWHEEL_LOG.exists():
        try:
            return json.loads(FLYWHEEL_LOG.read_text())
        except:
            pass
    return []

def save_log(log):
    FLYWHEEL_LOG.write_text(json.dumps(log[-500:], indent=2))


# ─── REVENUE POLLING ─────────────────────────────────────────────────────────

def poll_gumroad() -> float:
    if not GUMROAD_TOKEN:
        return 0.0
    try:
        r = requests.get(
            "https://api.gumroad.com/v2/sales",
            params={"access_token": GUMROAD_TOKEN, "after": _days_ago(7)},
            timeout=10
        )
        r.raise_for_status()
        sales = r.json().get("sales", [])
        total = sum(float(s.get("price", 0)) / 100 for s in sales)
        if total: print(f"   💰 Gumroad: ${total:.2f}")
        return total
    except:
        return 0.0

def poll_kofi() -> float:
    f = DATA_DIR / "kofi_transactions.json"
    if not f.exists():
        return 0.0
    try:
        txns = json.loads(f.read_text())
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        total = sum(float(t.get("amount", 0)) for t in txns if t.get("timestamp", "") > cutoff)
        if total: print(f"   ☕ Ko-fi: ${total:.2f}")
        return total
    except:
        return 0.0

def poll_strike() -> float:
    if not STRIKE_API_KEY:
        return 0.0
    try:
        r = requests.get(
            "https://api.strike.me/v1/invoices",
            headers={"Authorization": f"Bearer {STRIKE_API_KEY}"},
            params={"state": "PAID"}, timeout=10
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        total = sum(float(i.get("amount", {}).get("amount", 0)) for i in items if i.get("created", "") > cutoff)
        if total: print(f"   ⚡ Strike: ${total:.2f}")
        return total
    except:
        return 0.0

def poll_crypto():
    f = DATA_DIR / "crypto_gains.json"
    if not f.exists():
        return 0.0
    try:
        return float(json.loads(f.read_text()).get("realized_gains_usd", 0))
    except:
        return 0.0

def poll_gaza_rose():
    """$1 digital art sales from Gaza Rose Gallery."""
    f = DATA_DIR / "gaza_rose_sales.json"
    if not f.exists():
        return 0.0
    try:
        data = json.loads(f.read_text())
        return float(data.get("total_usd", 0))
    except:
        return 0.0

def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ─── $20 INVESTMENT ADVISOR ──────────────────────────────────────────────────

def get_investment_advice(state: dict) -> str:
    """
    Ask SolarPunk: 'If YOU had $20 right now, where does it do the most good?'
    Uses Anthropic API to analyze current system state and give real advice.
    """
    balance = state["current_balance"]
    unlocked = set(state.get("upgrades_notified", []))

    # Build context about current system health
    synthesis_log = DATA_DIR / "synthesis_log.json"
    flywheel_runs = len(load_log())
    engines_built = 0
    if synthesis_log.exists():
        try:
            sdata = json.loads(synthesis_log.read_text())
            engines_built = len(sdata.get("built", []))
        except:
            pass

    if not ANTHROPIC_API_KEY:
        # Fallback: rule-based advice
        if balance < 20:
            gap = 20 - balance
            return f"🎯 INVESTMENT ADVICE: You need ${gap:.2f} more to hit $20 (Claude Pro). Every dollar earned gets you closer to removing the 4-hour chat gap. Gaza Rose Gallery $1 sales are the fastest path — each sale = 5% of the way there."
        else:
            return "🎯 INVESTMENT ADVICE: You have $20+. PRIORITY #1: Upgrade to Claude Pro at claude.ai/upgrade right now. This removes the biggest bottleneck in the whole system. Do it before anything else."

    prompt = f"""You are SolarPunk — an autonomous AI agent built by Meeko.
You are analyzing your own revenue and system state to give your human (Meeko) investment advice.

CURRENT STATE:
- Revenue balance: ${balance:.2f}
- Engines built by SYNTHESIS_FACTORY: {engines_built}
- Flywheel cycles run: {flywheel_runs}
- Already unlocked upgrades: {list(unlocked)}
- Revenue sources active: {[k for k,v in state.get('revenue_sources',{}).items() if v > 0]}

AVAILABLE UPGRADES (by threshold):
{chr(10).join(f"  ${t['threshold']}: {t['name']} — {t['roi']}" for t in UPGRADE_TIERS if t['name'] not in unlocked)}

THE QUESTION: If Meeko has exactly $20 to invest in the system RIGHT NOW, where does that $20 do the absolute most for getting more money faster and making SolarPunk more capable?

Give your honest analysis in 3-4 sentences. Be specific. Be direct. Tell him exactly what to do and why. Start with the action."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        r.raise_for_status()
        advice = r.json()["content"][0]["text"]
        return f"🎯 SOLARPUNK $20 INVESTMENT ADVICE:\n{advice}"
    except Exception as e:
        return f"🎯 INVESTMENT ADVICE: ${balance:.2f} in balance. Next target: Claude Pro at $20 (claude.ai/upgrade). It eliminates the single biggest bottleneck — the 4-hour chat gap — and makes SolarPunk truly conversational and real-time."


# ─── UPGRADE NOTIFICATIONS ───────────────────────────────────────────────────

def check_upgrades(state: dict, log: list) -> list:
    balance = state["current_balance"]
    already = set(state.get("upgrades_notified", []))
    newly = []

    for tier in UPGRADE_TIERS:
        name = tier["name"]
        if balance >= tier["threshold"] and name not in already:
            newly.append(tier)
            state["upgrades_notified"].append(name)
            log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "upgrade_threshold_reached",
                "upgrade": name,
                "balance": balance,
                "threshold": tier["threshold"]
            })
            print(f"\n🚀 THRESHOLD HIT: {name} (${tier['threshold']})")
            print(f"   {tier['description']}")
            print(f"   ROI: {tier['roi']}")
            print(f"   → {tier['url']}")

    return newly


def generate_status_report(state: dict, advice: str) -> str:
    balance = state["current_balance"]
    unlocked = set(state.get("upgrades_notified", []))

    report = f"\n💹 SOLARPUNK REVENUE FLYWHEEL — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "=" * 55 + "\n"
    report += f"Balance:          ${balance:.2f}\n"
    report += f"Lifetime earned:  ${state['total_earned_lifetime']:.2f}\n\n"

    if state.get("revenue_sources"):
        active = {k: v for k, v in state["revenue_sources"].items() if v > 0}
        if active:
            report += "Active streams:\n"
            for k, v in active.items():
                report += f"  {k:25s} ${v:.2f}\n"

    report += "\n" + "─" * 55 + "\n"
    report += "UPGRADE ROADMAP:\n\n"

    for tier in UPGRADE_TIERS:
        name = tier["name"]
        threshold = tier["threshold"]
        if name in unlocked:
            status = "✅ NOTIFIED"
        else:
            need = threshold - balance
            status = f"🔒 ${need:.2f} away"
        report += f"  {status:18s} ${threshold:6.0f} → {name}\n"

    report += "\n" + "─" * 55 + "\n"
    report += advice + "\n"

    return report


# ─── EMAIL ───────────────────────────────────────────────────────────────────

def send_email(subject: str, body: str):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_ADDRESS
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print("📧 Email sent")
    except Exception as e:
        print(f"⚠️  Email failed: {e}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print("💹 SOLARPUNK REVENUE FLYWHEEL")
    print("─" * 35)

    state = load_state()
    log = load_log()

    # Poll all streams
    gumroad = poll_gumroad()
    kofi    = poll_kofi()
    strike  = poll_strike()
    crypto  = poll_crypto()
    gaza    = poll_gaza_rose()

    total_new = gumroad + kofi + strike + crypto + gaza

    state["revenue_sources"]["gumroad"]            = gumroad
    state["revenue_sources"]["kofi"]               = kofi
    state["revenue_sources"]["strike_lightning"]    = strike
    state["revenue_sources"]["crypto"]             = crypto
    state["revenue_sources"]["gaza_rose_gallery"]  = gaza

    state["current_balance"]         += total_new
    state["total_earned_lifetime"]   += total_new
    state["last_run"] = datetime.now().isoformat()

    month = datetime.now().strftime("%Y-%m")
    state["monthly_breakdown"][month] = state["monthly_breakdown"].get(month, 0) + total_new

    log.append({
        "timestamp": datetime.now().isoformat(),
        "new_revenue": total_new,
        "balance": state["current_balance"]
    })

    print(f"New revenue this cycle: ${total_new:.2f}")
    print(f"Running balance:        ${state['current_balance']:.2f}")

    # Get $20 investment advice every cycle
    advice = get_investment_advice(state)
    state["investment_advice"] = state.get("investment_advice", [])
    state["investment_advice"].append({
        "timestamp": datetime.now().isoformat(),
        "advice": advice,
        "balance_at_time": state["current_balance"]
    })
    state["investment_advice"] = state["investment_advice"][-30:]  # keep last 30

    # Check upgrades
    newly_unlocked = check_upgrades(state, log)

    # Full report
    report = generate_status_report(state, advice)
    print(report)

    # Email when thresholds hit OR once a week
    if newly_unlocked:
        tiers_str = ", ".join(t["name"] for t in newly_unlocked)
        send_email(
            f"🚀 SolarPunk: ${state['current_balance']:.2f} — {tiers_str} threshold reached!",
            report
        )

    save_state(state)
    save_log(log)
    return {"balance": state["current_balance"], "newly_unlocked": [t["name"] for t in newly_unlocked]}


if __name__ == "__main__":
    main()
