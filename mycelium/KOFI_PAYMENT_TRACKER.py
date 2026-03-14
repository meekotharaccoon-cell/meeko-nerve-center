# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""KOFI_PAYMENT_TRACKER — Reconciles Ko-fi payments to EMAIL_AGENT_EXCHANGE task log.

How it works:
1. EMAIL_BRAIN routes Ko-fi payment emails -> revenue_inbox.json (with body)
2. This engine reads those payment emails, finds task refs like:
   RESEARCH_AGENT-20260304123456 in the Ko-fi message/notes
3. Matches to task_log entries in email_exchange_state.json
4. Marks matching tasks as paid, updates earnings accurately
5. Logs unmatched payments for manual review

Runs in OMNIBUS L5 (COLLECT layer), after Ko-fi engine, before synthesis.
"""
import json, re
from pathlib import Path
from datetime import datetime, timezone

try:
    from AI_CLIENT import ask_json
except ImportError:
    def ask_json(prompt, **kw): return None

DATA = Path("data"); DATA.mkdir(exist_ok=True)

TASK_REF_PATTERN   = re.compile(r'([A-Z_]+_AGENT-\d{14})', re.IGNORECASE)
KOFI_SENDER_PATS   = ["ko-fi.com", "noreply@ko-fi", "support@ko-fi"]
SPLIT = {"agent_owner": 0.60, "meeko_platform": 0.25, "gaza": 0.15}


def load_exchange():
    f = DATA / "email_exchange_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"task_log": [], "total_earned": 0.0, "total_to_gaza": 0.0, "agent_earnings": {}}


def save_exchange(state):
    state["task_log"] = state.get("task_log", [])[-500:]
    (DATA / "email_exchange_state.json").write_text(json.dumps(state, indent=2))


def load_tracker():
    f = DATA / "kofi_tracker_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "payments_matched": 0, "payments_unmatched": 0,
            "total_verified": 0.0, "processed_ids": [], "log": []}


def save_tracker(state):
    state["log"]           = state.get("log", [])[-200:]
    state["processed_ids"] = state.get("processed_ids", [])[-500:]
    (DATA / "kofi_tracker_state.json").write_text(json.dumps(state, indent=2))


def is_kofi(em):
    sender  = em.get("from", "").lower()
    subject = em.get("subject", "").lower()
    return (
        any(p in sender for p in KOFI_SENDER_PATS)
        or ("ko-fi" in subject and any(w in subject for w in ["donation", "payment", "support"]))
    )


def extract_payment(em):
    combined  = em.get("subject", "") + " " + em.get("body", "")
    amt_match = re.search(r'\$(\d+\.?\d*)', combined)
    amount    = float(amt_match.group(1)) if amt_match else 0.0
    ref_match = TASK_REF_PATTERN.search(combined)
    task_ref  = ref_match.group(1).upper() if ref_match else None

    if not task_ref and amount > 0:
        prompt = (
            f"This is a Ko-fi payment email. Find the task reference if present.\n"
            f"SUBJECT: {em.get('subject','')}\nBODY: {em.get('body','')[:800]}\n"
            f"A task ref looks like: AGENT_NAME-YYYYMMDDHHMMSS (e.g. RESEARCH_AGENT-20260304123456)\n"
            f'Respond ONLY with JSON: {{"task_ref": "REF_OR_NULL", "amount": 0.00}}'
        )
        result = ask_json(prompt, max_tokens=100)
        if result:
            ref = str(result.get("task_ref", "")).strip().upper()
            if ref and ref != "NULL" and "AGENT" in ref:
                task_ref = ref
            if result.get("amount"):
                amount = float(result["amount"])

    return {"amount": amount, "task_ref": task_ref}


def reconcile(task_ref, amount, exchange, tracker):
    for task in exchange.get("task_log", []):
        if task.get("task_ref") == task_ref and not task.get("paid"):
            task["paid"]        = True
            task["paid_amount"] = amount
            task["paid_at"]     = datetime.now(timezone.utc).isoformat()
            agent = task.get("agent", "UNKNOWN")
            exchange["total_earned"]  = exchange.get("total_earned", 0)  + amount * SPLIT["meeko_platform"]
            exchange["total_to_gaza"] = exchange.get("total_to_gaza", 0) + amount * SPLIT["gaza"]
            exchange.setdefault("agent_earnings", {})[agent] = (
                exchange["agent_earnings"].get(agent, 0) + amount * SPLIT["agent_owner"]
            )
            tracker["payments_matched"] = tracker.get("payments_matched", 0) + 1
            tracker["total_verified"]   = tracker.get("total_verified", 0)   + amount
            print(f"  ✅ MATCHED: {task_ref} | ${amount:.2f} | agent: {agent}")
            return True

    tracker["payments_unmatched"] = tracker.get("payments_unmatched", 0) + 1
    tracker.setdefault("log", []).append({
        "type": "unmatched", "task_ref": task_ref,
        "amount": amount, "ts": datetime.now(timezone.utc).isoformat(),
    })
    print(f"  ⚠️  UNMATCHED: {task_ref} | ${amount:.2f}")
    return False


def run():
    tracker  = load_tracker()
    exchange = load_exchange()
    tracker["cycles"]   = tracker.get("cycles", 0) + 1
    tracker["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"KOFI_PAYMENT_TRACKER cycle {tracker['cycles']} | matched: {tracker.get('payments_matched',0)} | verified: ${tracker.get('total_verified',0):.2f}")

    revenue_f = DATA / "revenue_inbox.json"
    if not revenue_f.exists():
        print("  No revenue_inbox.json yet")
        save_tracker(tracker)
        return tracker

    try: revenue = json.loads(revenue_f.read_text())
    except: revenue = []

    processed      = set(tracker.get("processed_ids", []))
    exchange_dirty = False

    for em in revenue:
        pid = (em.get("ts", "") + em.get("subject", ""))[:40]
        if pid in processed: continue
        if not is_kofi(em): continue
        processed.add(pid)

        payment = extract_payment(em)
        print(f"  Ko-fi: ${payment['amount']:.2f} | ref: {payment['task_ref'] or 'none'}")

        if payment["task_ref"] and payment["amount"] > 0:
            if reconcile(payment["task_ref"], payment["amount"], exchange, tracker):
                exchange_dirty = True
        elif payment["amount"] > 0:
            print(f"  💰 Untagged donation: ${payment['amount']:.2f}")
            tracker.setdefault("log", []).append({
                "type": "untagged_donation",
                "amount": payment["amount"],
                "ts": datetime.now(timezone.utc).isoformat(),
            })

    tracker["processed_ids"] = list(processed)
    if exchange_dirty:
        save_exchange(exchange)
        print(f"  Ledger updated | total verified: ${tracker['total_verified']:.2f}")
    save_tracker(tracker)
    return tracker


if __name__ == "__main__":
    run()
