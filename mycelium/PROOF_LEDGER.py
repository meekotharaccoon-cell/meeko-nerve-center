# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
PROOF_LEDGER.py — public verifiable Gaza donation tracker
=========================================================
Maintains data/proof_ledger.json — the source of truth for:
  - Every sale logged
  - Gaza fund accumulation
  - Transfer records to PCRF
  - Public verification chain

This file is read by docs/proof.html in real time.
No sensitive information is ever written here — only:
  date, amount, product, platform, PCRF ref number (when transferred)

STOP PROTOCOL:
  When logging transfers: write amount + PCRF confirmation ref only.
  Never write: PayPal transaction IDs, bank details, account numbers, 
  login credentials, or full email addresses.
  The system logs what proves the donation happened, nothing more.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)

PRODUCT_SPLITS = {
    "solarpunk-starter":       {"title": "Build Your Own SolarPunk",           "price": 1.00,  "gaza_pct": 15},
    "local-ai-agent":          {"title": "Build a Local AI Agent with Ollama",  "price": 1.00,  "gaza_pct": 15},
    "github-actions-autonomous":{"title": "GitHub Actions for Autonomous AI",   "price": 15.00, "gaza_pct": 15},
    "ai-prompt-packs":         {"title": "AI Prompt Packs",                     "price": 17.00, "gaza_pct": 15},
    "gaza-art-pack":           {"title": "Gaza Rose Gallery — 7-Pack",          "price": 7.00,  "gaza_pct": 70},
    "gaza-rose-dove":          {"title": "White Doves Over Gaza",               "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-olive":         {"title": "Ancient Olive Grove",                 "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-tatreez":       {"title": "Tatreez — Living Embroidery",         "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-coast":         {"title": "Gaza Coastline at Golden Hour",       "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-star":          {"title": "Star of Hope Rising",                 "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-pomegranate":   {"title": "Pomegranate Season",                  "price": 1.00,  "gaza_pct": 70},
    "gaza-rose-night":         {"title": "Night Garden of Palestine",           "price": 1.00,  "gaza_pct": 70},
}

TRANSFER_THRESHOLD = 10.00  # Trigger transfer notification at $10 Gaza fund


def load_ledger():
    path = DATA / "proof_ledger.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {
        "total_sales": 0.0,
        "total_to_gaza": 0.0,
        "total_transferred": 0.0,
        "pending_transfer": 0.0,
        "sales": [],
        "transfers": [],
        "last_updated": None,
        "pcrf_ein": "93-1057665",
        "pcrf_charity_navigator": "https://www.charitynavigator.org/ein/931057665",
        "pcrf_donate": "https://www.pcrf.net/donate",
        "verification_note": "All Gaza donations tracked here. STOP protocol active — sensitive data never logged.",
    }


def log_sale(ledger, product_id, amount, platform="unknown", date=None):
    """Log a sale to the ledger. Call this when a sale is confirmed."""
    ts = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    spec = PRODUCT_SPLITS.get(product_id, {"title": product_id, "price": amount, "gaza_pct": 15})
    gaza_pct = spec["gaza_pct"]
    gaza_amt = round(amount * gaza_pct / 100, 2)

    sale = {
        "date": ts,
        "product": spec["title"],
        "product_id": product_id,
        "amount": amount,
        "gaza_pct": gaza_pct,
        "gaza_amount": gaza_amt,
        "platform": platform,
    }
    ledger["sales"].append(sale)
    ledger["total_sales"] = round(ledger.get("total_sales", 0) + amount, 2)
    ledger["total_to_gaza"] = round(ledger.get("total_to_gaza", 0) + gaza_amt, 2)
    ledger["pending_transfer"] = round(
        ledger.get("total_to_gaza", 0) - ledger.get("total_transferred", 0), 2
    )
    return sale


def log_transfer(ledger, amount, pcrf_ref, date=None):
    """
    Log a PCRF transfer. STOP PROTOCOL ENFORCED:
    Only logs: amount, PCRF reference number (publicly safe), date.
    Does NOT log: PayPal IDs, bank details, account numbers.
    """
    ts = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    transfer = {
        "date": ts,
        "amount": amount,
        "pcrf_ref": pcrf_ref,  # Just the PCRF confirmation number — safe to be public
        "note": "STOP: Only PCRF ref logged. Full receipt available on request.",
    }
    ledger["transfers"].append(transfer)
    ledger["total_transferred"] = round(ledger.get("total_transferred", 0) + amount, 2)
    ledger["pending_transfer"] = max(0, round(
        ledger.get("total_to_gaza", 0) - ledger.get("total_transferred", 0), 2
    ))
    return transfer


def check_gumroad_sales(ledger):
    """Pull new sales from Gumroad engine state."""
    gumroad_state = DATA / "gumroad_engine_state.json"
    if not gumroad_state.exists():
        return 0

    # Track what we've already logged
    logged_keys = {f"{s['date']}_{s['product_id']}_{s['platform']}" for s in ledger.get("sales", [])}
    new = 0

    # The gumroad state doesn't have individual sale records yet
    # When GUMROAD_ENGINE logs a new sale, it will appear in revenue_inbox.json
    revenue = DATA / "revenue_inbox.json"
    if revenue.exists():
        try:
            data = json.loads(revenue.read_text())
            for sale in data.get("sales", []):
                pid = sale.get("product_id", "unknown")
                date = sale.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
                key = f"{date}_{pid}_gumroad"
                if key not in logged_keys:
                    log_sale(ledger, pid, sale.get("amount", 1.0), "gumroad", date)
                    new += 1
        except:
            pass
    return new


def check_delivery_log(ledger):
    """Pull sales from PRODUCT_DELIVERY_ENGINE delivery log."""
    delivery_log = DATA / "delivery_log.json"
    if not delivery_log.exists():
        return 0

    logged_keys = {f"{s['date']}_{s.get('product_id','?')}" for s in ledger.get("sales", [])}
    new = 0
    try:
        data = json.loads(delivery_log.read_text())
        for d in data.get("deliveries", []):
            if not d.get("ok"):
                continue
            pid  = d.get("pid", "unknown")
            date = d.get("ts", "")[:10]
            key  = f"{date}_{pid}"
            if key not in logged_keys:
                spec = PRODUCT_SPLITS.get(pid, {"price": 1.0})
                log_sale(ledger, pid, spec.get("price", 1.0), "auto-delivered", date)
                new += 1
    except:
        pass
    return new


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nPROOF_LEDGER — {ts}")

    ledger = load_ledger()

    # Pull new sales from available sources
    new_from_gumroad  = check_gumroad_sales(ledger)
    new_from_delivery = check_delivery_log(ledger)
    new_total = new_from_gumroad + new_from_delivery

    # Check if transfer threshold reached
    pending = ledger.get("pending_transfer", 0)
    if pending >= TRANSFER_THRESHOLD:
        print(f"  ⚠️  Gaza fund pending transfer: ${pending:.2f} (threshold: ${TRANSFER_THRESHOLD})")
        print(f"  ACTION NEEDED: Transfer ${pending:.2f} to PCRF (pcrf.net/donate)")
        print(f"  After transferring, call log_transfer() with PCRF confirmation ref")
        print(f"  STOP: Do NOT log PayPal IDs or bank details here — only PCRF ref")
        # Write a flag file that OMNIBUS can surface
        (DATA / "transfer_needed.json").write_text(json.dumps({
            "amount": pending,
            "threshold": TRANSFER_THRESHOLD,
            "pcrf_url": "https://www.pcrf.net/donate",
            "pcrf_ein": "93-1057665",
            "action": "Transfer to PCRF, then call PROOF_LEDGER.log_transfer(ledger, amount, pcrf_ref)",
            "stop_protocol": "Log ONLY the PCRF confirmation ref number — nothing else",
            "ts": ts,
        }, indent=2))
    elif (DATA / "transfer_needed.json").exists() and pending < 1.0:
        (DATA / "transfer_needed.json").unlink()

    ledger["last_updated"] = ts
    ledger["pending_transfer"] = max(0, round(
        ledger.get("total_to_gaza", 0) - ledger.get("total_transferred", 0), 2
    ))

    # Save
    path = DATA / "proof_ledger.json"
    path.write_text(json.dumps(ledger, indent=2))

    print(f"  Total sales: ${ledger['total_sales']:.2f}")
    print(f"  Total to Gaza: ${ledger['total_to_gaza']:.2f}")
    print(f"  Transferred to PCRF: ${ledger['total_transferred']:.2f}")
    print(f"  Pending transfer: ${ledger['pending_transfer']:.2f}")
    print(f"  New sales logged: {new_total}")
    print(f"  Transfer threshold: ${TRANSFER_THRESHOLD} ({'' if pending < TRANSFER_THRESHOLD else '⚠️ EXCEEDED — action needed'})")

    state = {
        "ts": ts,
        "total_sales": ledger["total_sales"],
        "total_to_gaza": ledger["total_to_gaza"],
        "total_transferred": ledger["total_transferred"],
        "pending_transfer": ledger["pending_transfer"],
        "new_sales_this_cycle": new_total,
        "transfer_threshold_exceeded": pending >= TRANSFER_THRESHOLD,
    }
    (DATA / "proof_ledger_state.json").write_text(json.dumps(state, indent=2))
    return state


if __name__ == "__main__":
    run()
