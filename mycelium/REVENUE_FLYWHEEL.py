"""
REVENUE_FLYWHEEL.py
===================
Connects ALL revenue streams, tracks accumulated balance, and
automatically reinvests at threshold levels into system upgrades.

The loop:
  Ko-fi + Gumroad + Patreon + Donations + Crypto gains
    → accumulate in flywheel_balance.json
    → when thresholds hit → allocate to upgrades
    → upgrades improve system capabilities
    → better capabilities → more revenue
    → repeat

Upgrade tiers (auto-unlocked when balance hits threshold):
  $5   → Upgrade to Claude Pro ($20/mo) — no more 4hr gaps in chat
  $20  → Domain name for spawn.html (proper URL for revenue pages)
  $50  → Mailgun paid tier (higher email send limits)
  $100 → Anthropic API credits ($10 bump)
  $200 → GitHub Pro (more CI/CD minutes)
  $500 → Custom server (vs GitHub Actions free tier)

Run: python REVENUE_FLYWHEEL.py
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
FLYWHEEL_LOG = DATA_DIR / "flywheel_log.json"

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GUMROAD_TOKEN = os.environ.get("GUMROAD_TOKEN", "")
KOFI_TOKEN = os.environ.get("KOFI_TOKEN", "")
STRIKE_API_KEY = os.environ.get("STRIKE_API_KEY", "")

# Reinvestment thresholds (USD)
UPGRADE_TIERS = [
    {
        "threshold": 5.0,
        "name": "Claude Pro Upgrade",
        "description": "Upgrade Claude chat to Pro — eliminates 4-hour bottleneck completely",
        "url": "https://claude.ai/upgrade",
        "cost": 20.0,
        "priority": 1,
        "impact": "HIGH — removes biggest system bottleneck"
    },
    {
        "threshold": 20.0,
        "name": "Custom Domain",
        "description": "meeko-nerve-center.com or similar — proper revenue page URL",
        "url": "https://namecheap.com",
        "cost": 12.0,
        "priority": 2,
        "impact": "MEDIUM — professional presence, better conversions"
    },
    {
        "threshold": 50.0,
        "name": "Mailgun Flex Plan",
        "description": "Higher email send limits for outreach and newsletters",
        "url": "https://mailgun.com",
        "cost": 15.0,
        "priority": 3,
        "impact": "MEDIUM — removes email send bottleneck"
    },
    {
        "threshold": 100.0,
        "name": "Anthropic API Credits",
        "description": "$10 in API credits — more autonomous building cycles",
        "url": "https://console.anthropic.com",
        "cost": 10.0,
        "priority": 4,
        "impact": "HIGH — more synthesis cycles per day"
    },
    {
        "threshold": 200.0,
        "name": "GitHub Pro",
        "description": "More CI/CD minutes, larger artifacts, better Actions",
        "url": "https://github.com/pricing",
        "cost": 4.0,
        "priority": 5,
        "impact": "MEDIUM — more OMNIBRAIN cycles per month"
    },
    {
        "threshold": 500.0,
        "name": "VPS Server",
        "description": "Always-on server (DigitalOcean $6/mo) — no cold start delays",
        "url": "https://digitalocean.com",
        "cost": 6.0,
        "priority": 6,
        "impact": "HIGH — 24/7 always-running system"
    }
]

# ─── STATE ──────────────────────────────────────────────────────────────────

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
        "upgrades_unlocked": [],
        "last_run": None,
        "revenue_sources": {
            "gumroad": 0.0,
            "kofi": 0.0,
            "patreon": 0.0,
            "github_sponsors": 0.0,
            "crypto": 0.0,
            "grants": 0.0,
            "other": 0.0
        },
        "monthly_breakdown": {}
    }

def save_state(state):
    FLYWHEEL_STATE.write_text(json.dumps(state, indent=2))

def load_log():
    if FLYWHEEL_LOG.exists():
        try:
            return json.loads(FLYWHEEL_LOG.read_text())
        except:
            pass
    return []

def save_log(log):
    # Keep last 500 entries
    FLYWHEEL_LOG.write_text(json.dumps(log[-500:], indent=2))

# ─── REVENUE POLLING ────────────────────────────────────────────────────────

def poll_gumroad() -> float:
    """Get recent Gumroad sales."""
    if not GUMROAD_TOKEN:
        print("   ⚠️  No GUMROAD_TOKEN — skipping")
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
        print(f"   💰 Gumroad: ${total:.2f} (last 7 days, {len(sales)} sales)")
        return total
    except Exception as e:
        print(f"   ❌ Gumroad error: {e}")
        return 0.0

def poll_kofi() -> float:
    """Ko-fi doesn't have a public polling API — we read from webhook logs."""
    kofi_data_file = DATA_DIR / "kofi_transactions.json"
    if not kofi_data_file.exists():
        print("   ⚠️  No Ko-fi data file yet (needs kofi_webhook.py to populate it)")
        return 0.0
    
    try:
        transactions = json.loads(kofi_data_file.read_text())
        # Sum last 30 days
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        recent = [t for t in transactions if t.get("timestamp", "") > cutoff]
        total = sum(float(t.get("amount", 0)) for t in recent)
        print(f"   ☕ Ko-fi: ${total:.2f} (last 30 days, {len(recent)} transactions)")
        return total
    except Exception as e:
        print(f"   ❌ Ko-fi error: {e}")
        return 0.0

def poll_strike_lightning() -> float:
    """Check Strike/Lightning payments."""
    if not STRIKE_API_KEY:
        print("   ⚠️  No STRIKE_API_KEY — skipping Lightning")
        return 0.0
    
    try:
        r = requests.get(
            "https://api.strike.me/v1/invoices",
            headers={"Authorization": f"Bearer {STRIKE_API_KEY}"},
            params={"state": "PAID"},
            timeout=10
        )
        r.raise_for_status()
        invoices = r.json().get("items", [])
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        recent = [i for i in invoices if i.get("created", "") > cutoff]
        total = sum(float(i.get("amount", {}).get("amount", 0)) for i in recent)
        print(f"   ⚡ Strike/Lightning: ${total:.2f} (last 30 days)")
        return total
    except Exception as e:
        print(f"   ❌ Strike error: {e}")
        return 0.0

def poll_crypto_gains() -> float:
    """Read crypto_signals.py output for realized gains."""
    signals_file = DATA_DIR / "crypto_gains.json"
    if not signals_file.exists():
        print("   ⚠️  No crypto gains file yet")
        return 0.0
    
    try:
        data = json.loads(signals_file.read_text())
        total = float(data.get("realized_gains_usd", 0))
        print(f"   🪙 Crypto gains: ${total:.2f}")
        return total
    except:
        return 0.0

def poll_github_sponsors() -> float:
    """Read GitHub Sponsors data if available."""
    sponsors_file = DATA_DIR / "github_sponsors.json"
    if not sponsors_file.exists():
        return 0.0
    try:
        data = json.loads(sponsors_file.read_text())
        total = float(data.get("monthly_income_usd", 0))
        print(f"   💎 GitHub Sponsors: ${total:.2f}/mo")
        return total
    except:
        return 0.0

def _days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")

# ─── UPGRADE LOGIC ──────────────────────────────────────────────────────────

def check_upgrades(state: dict, log: list) -> list:
    """Check which upgrades are newly unlocked."""
    balance = state["current_balance"]
    already_unlocked = set(state.get("upgrades_unlocked", []))
    newly_unlocked = []
    
    for tier in UPGRADE_TIERS:
        name = tier["name"]
        if balance >= tier["threshold"] and name not in already_unlocked:
            newly_unlocked.append(tier)
            state["upgrades_unlocked"].append(name)
            log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "upgrade_unlocked",
                "upgrade": name,
                "balance_at_unlock": balance,
                "threshold": tier["threshold"]
            })
            print(f"\n🎯 UPGRADE UNLOCKED: {name}")
            print(f"   Balance: ${balance:.2f} ≥ Threshold: ${tier['threshold']:.2f}")
            print(f"   {tier['description']}")
            print(f"   Impact: {tier['impact']}")
            print(f"   URL: {tier['url']}")
    
    return newly_unlocked

def generate_reinvestment_plan(state: dict) -> str:
    """Generate the prioritized upgrade roadmap."""
    balance = state["current_balance"]
    unlocked = set(state.get("upgrades_unlocked", []))
    
    plan = f"\n💹 REVENUE FLYWHEEL STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    plan += f"{'='*50}\n"
    plan += f"Current Balance:      ${balance:.2f}\n"
    plan += f"Total Earned Ever:    ${state['total_earned_lifetime']:.2f}\n"
    plan += f"Total Reinvested:     ${state['total_invested']:.2f}\n"
    plan += f"\nRevenue Sources (30d):\n"
    
    for source, amount in state.get("revenue_sources", {}).items():
        if amount > 0:
            plan += f"  {source:20s}: ${amount:.2f}\n"
    
    plan += f"\n{'─'*50}\n"
    plan += f"UPGRADE ROADMAP:\n\n"
    
    for tier in UPGRADE_TIERS:
        name = tier["name"]
        threshold = tier["threshold"]
        status = "✅ UNLOCKED" if name in unlocked else f"🔒 need ${threshold - balance:.2f} more"
        plan += f"  [{status}] ${threshold:.0f} → {name}\n"
        plan += f"    {tier['impact']}\n"
    
    return plan

# ─── NOTIFY ─────────────────────────────────────────────────────────────────

def send_flywheel_email(state: dict, newly_unlocked: list):
    """Email the flywheel status when upgrades unlock."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return
    if not newly_unlocked:
        return  # Only email when something unlocks
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        plan = generate_reinvestment_plan(state)
        body = f"🎉 REVENUE MILESTONE REACHED!\n\n"
        body += f"New upgrades unlocked this cycle:\n"
        for tier in newly_unlocked:
            body += f"  → {tier['name']}: {tier['url']}\n"
        body += f"\n{plan}"
        
        msg = MIMEText(body)
        msg["Subject"] = f"💹 Revenue unlocked: {', '.join(t['name'] for t in newly_unlocked)}"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_ADDRESS
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print("📧 Flywheel report emailed")
    except Exception as e:
        print(f"⚠️  Email failed: {e}")

# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    print("💹 REVENUE FLYWHEEL starting...")
    
    state = load_state()
    log = load_log()
    
    # Poll all revenue sources
    print("\n📊 Polling revenue sources...")
    gumroad = poll_gumroad()
    kofi = poll_kofi()
    strike = poll_strike_lightning()
    crypto = poll_crypto_gains()
    sponsors = poll_github_sponsors()
    
    # Update state
    state["revenue_sources"]["gumroad"] = gumroad
    state["revenue_sources"]["kofi"] = kofi
    state["revenue_sources"]["crypto"] = crypto
    state["revenue_sources"]["github_sponsors"] = sponsors
    
    new_revenue = gumroad + kofi + strike + crypto + sponsors
    state["current_balance"] += new_revenue
    state["total_earned_lifetime"] += new_revenue
    state["last_run"] = datetime.now().isoformat()
    
    # Monthly tracking
    month_key = datetime.now().strftime("%Y-%m")
    state["monthly_breakdown"][month_key] = state["monthly_breakdown"].get(month_key, 0) + new_revenue
    
    log.append({
        "timestamp": datetime.now().isoformat(),
        "event": "revenue_poll",
        "new_revenue": new_revenue,
        "balance": state["current_balance"],
        "sources": {"gumroad": gumroad, "kofi": kofi, "strike": strike, "crypto": crypto}
    })
    
    print(f"\n💰 New revenue this cycle: ${new_revenue:.2f}")
    print(f"🏦 Running balance: ${state['current_balance']:.2f}")
    
    # Check upgrades
    newly_unlocked = check_upgrades(state, log)
    
    # Print full plan
    print(generate_reinvestment_plan(state))
    
    # Email if milestones hit
    send_flywheel_email(state, newly_unlocked)
    
    # Save
    save_state(state)
    save_log(log)
    
    return {
        "balance": state["current_balance"],
        "new_revenue": new_revenue,
        "upgrades_unlocked": len(state.get("upgrades_unlocked", [])),
        "newly_unlocked": [t["name"] for t in newly_unlocked]
    }

if __name__ == "__main__":
    result = main()
    print(f"\n✅ Flywheel cycle complete: {result}")
