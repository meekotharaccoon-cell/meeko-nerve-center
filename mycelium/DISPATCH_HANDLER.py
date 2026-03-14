# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""DISPATCH_HANDLER.py — processes real payments arriving via repository_dispatch
Called by KOFI_PAYMENT.yml when Ko-fi fires a webhook.
Zero external API keys needed — uses env vars set by the workflow.

Flow: Ko-fi payment → Pipedream webhook → GitHub dispatch → this engine
Docs for wiring: .github/workflows/KOFI_PAYMENT.yml
"""
import os, json, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA = Path("data"); DATA.mkdir(exist_ok=True)

GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GPWD  = os.environ.get("GMAIL_APP_PASSWORD", "")

# Payment data injected by KOFI_PAYMENT.yml from dispatch payload
AMOUNT  = float(os.environ.get("PAYMENT_AMOUNT", "0") or "0")
EMAIL   = os.environ.get("PAYMENT_EMAIL", "")
MESSAGE = os.environ.get("PAYMENT_MESSAGE", "")
SOURCE  = os.environ.get("PAYMENT_SOURCE", "kofi_payment")

GAZA_CUT    = 0.15   # 15% to Gaza
LOOP_FUND   = 0.30   # 30% to reinvestment pool (art loop)
ARTIST_FUND = 0.70   # 70% to Gaza Rose Gallery (for $1 art purchases)

def load_revenue():
    f = DATA / "revenue_inbox.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {
        "total_received": 0.0,
        "total_to_gaza": 0.0,
        "total_loop_fund": 0.0,
        "events": [],
        "auto_loops": 0,
    }

def save_revenue(r):
    (DATA / "revenue_inbox.json").write_text(json.dumps(r, indent=2))

def load_kofi():
    f = DATA / "kofi_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"total_received": 0.0, "total_to_gaza": 0.0, "events": [], "auto_loops": 0}

def save_kofi(k):
    (DATA / "kofi_state.json").write_text(json.dumps(k, indent=2))

def send_notification(amount, to_gaza, loop_fund, total_received, total_to_gaza):
    """Send a real-time payment notification email if Gmail is configured"""
    if not GMAIL or not GPWD:
        print(f"  [EMAIL] Would notify: ${amount:.2f} received, ${to_gaza:.2f} to Gaza")
        return
    try:
        body = f"""💰 Payment received!

Amount: ${amount:.2f}
Buyer: {EMAIL or 'anonymous'}
Message: {MESSAGE or '(none)'}
Source: {SOURCE}

SPLIT:
  ${to_gaza:.2f} → Gaza (15%)
  ${loop_fund:.2f} → Loop Fund (30%)
  ${amount - to_gaza - loop_fund:.2f} → Revenue

RUNNING TOTALS:
  Total received: ${total_received:.2f}
  Total to Gaza: ${total_to_gaza:.2f}

[SolarPunk DISPATCH_HANDLER — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}]
"""
        msg = MIMEMultipart()
        msg["From"] = GMAIL; msg["To"] = GMAIL
        msg["Subject"] = f"[SolarPunk] 💰 ${amount:.2f} received → ${to_gaza:.2f} to Gaza"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls(); s.login(GMAIL, GPWD); s.sendmail(GMAIL, GMAIL, msg.as_string())
        print(f"  ✅ Notification email sent")
    except Exception as e:
        print(f"  Email error: {e}")

def check_loop_trigger(revenue):
    """If loop fund has hit $1, trigger auto-purchase"""
    if revenue["total_loop_fund"] >= 1.0:
        revenue["total_loop_fund"] -= 1.0
        revenue["auto_loops"] = revenue.get("auto_loops", 0) + 1
        print(f"  🔄 LOOP TRIGGERED — auto-loop #{revenue['auto_loops']} | Pool remaining: ${revenue['total_loop_fund']:.2f}")
        # Write a trigger file that KOFI_ENGINE and INCOME_ARCHITECT will see next cycle
        trigger = {
            "triggered": True,
            "trigger_time": datetime.now(timezone.utc).isoformat(),
            "loop_number": revenue["auto_loops"],
            "action": "auto_purchase",
        }
        (DATA / "loop_trigger.json").write_text(json.dumps(trigger, indent=2))
        return True
    return False

def run():
    print(f"DISPATCH_HANDLER starting...")
    print(f"  Source: {SOURCE}")
    print(f"  Amount: ${AMOUNT:.2f}")
    print(f"  Email: {EMAIL or 'anonymous'}")

    if AMOUNT <= 0:
        print("  ⚠️  No payment amount — nothing to process")
        return

    now = datetime.now(timezone.utc).isoformat()

    # Calculate splits
    to_gaza    = round(AMOUNT * GAZA_CUT, 4)
    loop_fund  = round(AMOUNT * LOOP_FUND, 4)

    # For $1 art purchases (Gaza Rose Gallery loop)
    # Art loop uses different split: 70% Gaza, 30% pool
    if SOURCE in ("kofi_payment", "kofi_test") and AMOUNT <= 1.10:
        to_gaza   = round(AMOUNT * ARTIST_FUND, 4)
        loop_fund = round(AMOUNT * (1 - ARTIST_FUND), 4)
        print(f"  Art purchase detected — Gaza split: 70/30")

    # Update revenue_inbox (what KOFI_PAYMENT_TRACKER reads)
    revenue = load_revenue()
    event = {
        "ts": now, "amount": AMOUNT, "email": EMAIL,
        "message": MESSAGE, "source": SOURCE,
        "to_gaza": to_gaza, "loop_fund": loop_fund,
    }
    revenue["events"].append(event)
    revenue["total_received"] = round(revenue.get("total_received", 0) + AMOUNT, 4)
    revenue["total_to_gaza"]  = round(revenue.get("total_to_gaza", 0) + to_gaza, 4)
    revenue["total_loop_fund"] = round(revenue.get("total_loop_fund", 0) + loop_fund, 4)
    revenue["last_payment"] = now

    # Also update kofi_state (what KOFI_ENGINE reads)
    kofi = load_kofi()
    kofi["events"].append(event)
    kofi["total_received"] = revenue["total_received"]
    kofi["total_to_gaza"]  = revenue["total_to_gaza"]
    kofi["last_payment"]   = now

    # Check loop trigger
    looped = check_loop_trigger(revenue)
    if looped:
        kofi["auto_loops"] = revenue["auto_loops"]

    save_revenue(revenue)
    save_kofi(kofi)

    print(f"  ✅ Payment recorded: ${AMOUNT:.2f} | Gaza: ${to_gaza:.2f} | Pool: ${revenue['total_loop_fund']:.2f}")
    print(f"  📊 Running total: ${revenue['total_received']:.2f} received | ${revenue['total_to_gaza']:.2f} to Gaza")

    # Send email notification
    send_notification(AMOUNT, to_gaza, loop_fund, revenue["total_received"], revenue["total_to_gaza"])

    # Update brain state health (payment = massive health boost)
    brain_f = DATA / "brain_state.json"
    if brain_f.exists():
        try:
            brain = json.loads(brain_f.read_text())
            old_h = brain.get("health_score", 40)
            brain["health_score"] = min(100, old_h + 20)
            brain["last_payment"] = now
            brain["total_revenue"] = revenue["total_received"]
            brain_f.write_text(json.dumps(brain, indent=2))
            print(f"  🧠 Health: {old_h} → {brain['health_score']}")
        except: pass

    return revenue

if __name__ == "__main__": run()
