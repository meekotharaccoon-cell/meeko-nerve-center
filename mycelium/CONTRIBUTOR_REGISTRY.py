#!/usr/bin/env python3
"""
CONTRIBUTOR_REGISTRY.py — Manages humans who get automatic revenue shares

To add a contributor:
  1. Open data/contributor_registry.json on GitHub
  2. Add entry with paypal_email and split_percent
  3. This engine validates and credits them each cycle

Revenue flow:
  Sale > DISPATCH_HANDLER > payout_queue.json > HERE > credits contributors > PAYPAL_PAYOUT sends it

Split structure MUST equal 100%:
  Example: Meeko 55% + Gaza 15% + Loop 30% = 100%
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

DEFAULT_REGISTRY = {
    "last_updated": "",
    "description": "SolarPunk™ contributor revenue registry. Each active contributor gets their split automatically via PayPal.",
    "contributors": [
        {
            "id": "meeko",
            "name": "Meeko (Founder)",
            "role": "founder",
            "paypal_email": "MEEKO_PAYPAL_EMAIL_HERE",
            "split_percent": 55,
            "pending_usd": 0.0,
            "total_earned": 0.0,
            "joined": "2026-03-05",
            "active": True,
            "note": "55% product revenue. Update 'paypal_email' with your real PayPal email."
        }
    ],
    "special_accounts": {
        "gaza_fund": {
            "name": "Gaza / PCRF (EIN 93-1057665)",
            "split_percent": 15,
            "pending_usd": 0.0,
            "total_donated": 0.0,
            "method": "Manual PCRF.net donation monthly by Meeko"
        },
        "loop_fund": {
            "name": "SolarPunk™ Loop Fund",
            "split_percent": 30,
            "pending_usd": 0.0,
            "total_cycled": 0.0,
            "note": "Auto-reinvests when balance hits $1 via KOFI_ENGINE"
        }
    }
}


def load_registry():
    f = DATA / "contributor_registry.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return DEFAULT_REGISTRY.copy()


def save_registry(r):
    (DATA / "contributor_registry.json").write_text(json.dumps(r, indent=2))


def process_payout_queue(registry):
    qf = DATA / "payout_queue.json"
    if not qf.exists():
        return 0
    try: queue = json.loads(qf.read_text())
    except: return 0
    pending = queue.get("pending", [])
    processed = 0
    for entry in pending:
        if entry.get("processed"):
            continue
        amount = float(entry.get("amount_usd", 0))
        if amount <= 0:
            continue
        for contrib in registry.get("contributors", []):
            if not contrib.get("active"):
                continue
            split = contrib.get("split_percent", 0) / 100.0
            contrib["pending_usd"] = round(contrib.get("pending_usd", 0) + amount * split, 4)
        for key, acct in registry.get("special_accounts", {}).items():
            s = acct.get("split_percent", 0) / 100.0
            acct["pending_usd"] = round(acct.get("pending_usd", 0) + amount * s, 4)
            if key == "gaza_fund":
                acct["total_donated"] = round(acct.get("total_donated", 0) + amount * s, 4)
        entry["processed"] = True
        processed += 1
    queue["pending"] = pending
    queue["last_processed"] = datetime.now(timezone.utc).isoformat()
    qf.write_text(json.dumps(queue, indent=2))
    return processed


def validate_splits(registry):
    contrib_total = sum(c.get("split_percent", 0) for c in registry.get("contributors", []) if c.get("active"))
    special_total = sum(v.get("split_percent", 0) for v in registry.get("special_accounts", {}).values())
    total = contrib_total + special_total
    return total, total == 100


def run():
    print("CONTRIBUTOR_REGISTRY running...")
    now = datetime.now(timezone.utc).isoformat()
    registry = load_registry()
    if not registry.get("contributors"):
        registry = DEFAULT_REGISTRY.copy()
        print("  📋 Initialized default registry")
    registry["last_updated"] = now
    processed = process_payout_queue(registry)
    if processed:
        print(f"  💰 Processed {processed} payout queue entries")
    total_split, valid = validate_splits(registry)
    if not valid:
        print(f"  ⚠️  Split total: {total_split}% (must be 100%)")
    else:
        print(f"  ✅ Split validation OK: {total_split}%")
    for contrib in registry.get("contributors", []):
        pending = contrib.get("pending_usd", 0)
        earned = contrib.get("total_earned", 0)
        paypal_set = contrib.get("paypal_email", "") not in ["", "MEEKO_PAYPAL_EMAIL_HERE"]
        print(f"  👤 {contrib['name']}: ${pending:.2f} pending | ${earned:.2f} earned | PayPal: {'✅ set' if paypal_set else '❌ NOT SET'}")
    special = registry.get("special_accounts", {})
    if "gaza_fund" in special:
        print(f"  🌹 Gaza Fund: ${special['gaza_fund'].get('total_donated', 0):.2f} total donated to PCRF")
    if "loop_fund" in special:
        print(f"  🔄 Loop Fund: ${special['loop_fund'].get('pending_usd', 0):.2f} available")
    save_registry(registry)
    print(f"  📊 Registry saved. {len(registry.get('contributors', []))} contributors active.")
    print("  📝 To add PayPal: edit 'paypal_email' in data/contributor_registry.json on GitHub")


if __name__ == "__main__": run()
