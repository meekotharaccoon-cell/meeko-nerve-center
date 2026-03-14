# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
PAYPAL_PAYOUT.py — Automated revenue distribution to human contributors

Secrets needed:
  PAYPAL_CLIENT_ID     — developer.paypal.com > My Apps > Create App
  PAYPAL_CLIENT_SECRET — same app
  PAYPAL_SANDBOX       — 'true' to test, 'false' for real payouts

Flow:
  1. Reads data/contributor_registry.json (managed by CONTRIBUTOR_REGISTRY)
  2. Sends real PayPal payouts to contributors who earned >= $1.00
  3. Records all transactions in data/payout_ledger.json (public audit trail)
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

CLIENT_ID     = os.environ.get("PAYPAL_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
SANDBOX       = os.environ.get("PAYPAL_SANDBOX", "true").lower() != "false"
BASE_URL      = "https://api.sandbox.paypal.com" if SANDBOX else "https://api.paypal.com"
MIN_PAYOUT    = 1.00


def get_token():
    r = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["access_token"]


def send_payout(token, items, batch_id):
    payload = {
        "sender_batch_header": {
            "sender_batch_id": batch_id,
            "email_subject": "SolarPunk™ Revenue Share — You've been paid!",
            "email_message": "Your SolarPunk™ contributor revenue has arrived. Thank you."
        },
        "items": items
    }
    r = requests.post(
        f"{BASE_URL}/v1/payments/payouts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    return r.status_code, r.json()


def load_registry():
    f = DATA / "contributor_registry.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"contributors": []}


def load_ledger():
    f = DATA / "payout_ledger.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"payouts": [], "total_paid_usd": 0.0}


def run():
    print("PAYPAL_PAYOUT running...")
    now = datetime.now(timezone.utc).isoformat()
    env = "SANDBOX" if SANDBOX else "LIVE"

    if not CLIENT_ID or not CLIENT_SECRET:
        print("  ⚠️  PayPal credentials missing")
        print("  HOW TO GET:")
        print("  1. Go to developer.paypal.com > My Apps & Credentials")
        print("  2. Create App (Business account) > copy Client ID + Secret")
        print("  3. GitHub Secrets: PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET")
        print("  4. Set PAYPAL_SANDBOX=true to test, false for real payouts")
        (DATA / "paypal_payout_state.json").write_text(
            json.dumps({"last_run": now, "status": "no_credentials", "env": env}, indent=2))
        return

    registry = load_registry()
    contributors = registry.get("contributors", [])
    ledger = load_ledger()

    if not contributors:
        print("  ℹ️  No contributors registered. Add via data/contributor_registry.json")
        (DATA / "paypal_payout_state.json").write_text(
            json.dumps({"last_run": now, "status": "no_contributors", "env": env}, indent=2))
        return

    batch_id = f"sp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payout_items, contributors_paid = [], []

    for i, contrib in enumerate(contributors):
        earned = contrib.get("pending_usd", 0.0)
        paypal_email = contrib.get("paypal_email", "")
        if not paypal_email or paypal_email == "MEEKO_PAYPAL_EMAIL_HERE":
            print(f"  ⚠️  {contrib.get('name', '?')}: PayPal email not set")
            continue
        if earned < MIN_PAYOUT:
            print(f"  ⏳ {contrib.get('name', '?')}: ${earned:.2f} pending (min ${MIN_PAYOUT:.2f})")
            continue
        payout_items.append({
            "recipient_type": "EMAIL",
            "amount": {"value": f"{earned:.2f}", "currency": "USD"},
            "receiver": paypal_email,
            "note": f"SolarPunk™ revenue share — {contrib.get('role', 'contributor')}",
            "sender_item_id": f"contrib_{i}_{batch_id}"
        })
        contributors_paid.append({"name": contrib.get("name"), "email": paypal_email, "amount": earned})

    if not payout_items:
        print(f"  ℹ️  No contributors ready for payout (threshold: ${MIN_PAYOUT:.2f})")
        print("  📝 Update 'paypal_email' in data/contributor_registry.json to enable payouts")
        (DATA / "paypal_payout_state.json").write_text(
            json.dumps({"last_run": now, "status": "no_eligible_contributors", "env": env}, indent=2))
        return

    try:
        token = get_token()
        status_code, result = send_payout(token, payout_items, batch_id)
    except Exception as ex:
        print(f"  ❌ PayPal API error: {ex}")
        (DATA / "paypal_payout_state.json").write_text(
            json.dumps({"last_run": now, "status": f"error: {str(ex)[:100]}", "env": env}, indent=2))
        return

    if status_code == 201:
        total_sent = sum(c["amount"] for c in contributors_paid)
        print(f"  ✅ Payout sent! ({env}) ${total_sent:.2f} to {len(contributors_paid)} recipients")
        ledger["payouts"].append({
            "ts": now, "batch_id": batch_id, "env": env,
            "recipients": contributors_paid, "total": total_sent
        })
        ledger["total_paid_usd"] = round(ledger.get("total_paid_usd", 0) + total_sent, 2)
        (DATA / "payout_ledger.json").write_text(json.dumps(ledger, indent=2))
        paid_emails = [c["email"] for c in contributors_paid]
        for contrib in contributors:
            if contrib.get("paypal_email") in paid_emails:
                contrib["total_earned"] = round(contrib.get("total_earned", 0) + contrib.get("pending_usd", 0), 4)
                contrib["pending_usd"] = 0.0
        registry["last_payout"] = now
        (DATA / "contributor_registry.json").write_text(json.dumps(registry, indent=2))
    else:
        print(f"  ❌ PayPal error {status_code}: {str(result)[:200]}")

    (DATA / "paypal_payout_state.json").write_text(
        json.dumps({"last_run": now, "status": "ok" if status_code == 201 else "error", "env": env}, indent=2))


if __name__ == "__main__": run()
