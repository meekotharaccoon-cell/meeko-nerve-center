# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
HUMAN_PAYOUT.py — Automated PayPal payouts to collaborators + Gaza
===================================================================
Sends revenue shares automatically via PayPal Payouts API.
Gaza donations → PCRF (Palestine Children's Relief Fund)
Human collaborators → their PayPal emails

Secrets needed (add to GitHub Secrets):
  PAYPAL_CLIENT_ID     from developer.paypal.com → My Apps → Create App
  PAYPAL_CLIENT_SECRET same place
  PAYPAL_MODE          'sandbox' (testing) or 'live' (real money)

How to get PayPal API keys (3 steps):
  1. Go to developer.paypal.com — log in with your PayPal account
  2. My Apps & Credentials → Create App → name it 'SolarPunk'
  3. Copy Client ID + Secret → add to GitHub Secrets
  Note: Start with sandbox mode for testing, switch to live when ready
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET    = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_MODE      = os.environ.get("PAYPAL_MODE", "sandbox")
PAYPAL_BASE      = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"

PCRF_EMAIL = "donate@pcrf.net"  # PCRF official PayPal donation email


def load_state():
    f = DATA / "payout_ledger.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {
        "payouts": [], "failed": [], "pending": [],
        "total_paid_usd": 0.0, "total_to_gaza_usd": 0.0,
        "collaborators": {}, "last_run": None,
    }


def save_state(s):
    (DATA / "payout_ledger.json").write_text(json.dumps(s, indent=2))


def get_token():
    r = requests.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        data={"grant_type": "client_credentials"}, timeout=30
    )
    r.raise_for_status()
    return r.json()["access_token"]


def send_payout(token, email, amount_usd, note, batch_id):
    payload = {
        "sender_batch_header": {
            "sender_batch_id": batch_id,
            "email_subject": "SolarPunk™ — Revenue Share",
            "email_message": note,
        },
        "items": [{
            "recipient_type": "EMAIL",
            "amount": {"value": f"{amount_usd:.2f}", "currency": "USD"},
            "note": note,
            "sender_item_id": batch_id,
            "receiver": email,
        }]
    }
    r = requests.post(
        f"{PAYPAL_BASE}/v1/payments/payouts",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    if r.status_code in (200, 201):
        d = r.json()
        batch = d.get("batch_header", {})
        return {"success": True, "batch_id": batch.get("payout_batch_id"), "status": batch.get("batch_status")}
    return {"success": False, "error": r.text[:200], "code": r.status_code}


def register_collaborator(email, name, paypal_email, share_pct, role):
    """Add a human collaborator for automatic revenue share."""
    collab_f = DATA / "collaborators.json"
    data = json.loads(collab_f.read_text()) if collab_f.exists() else {"collaborators": []}
    for c in data["collaborators"]:
        if c["email"] == email:
            c.update({"name": name, "paypal_email": paypal_email, "share_pct": share_pct, "role": role})
            collab_f.write_text(json.dumps(data, indent=2))
            return c
    new = {
        "id": f"c{len(data['collaborators'])+1:04d}",
        "email": email, "name": name, "paypal_email": paypal_email,
        "share_pct": share_pct, "role": role,
        "joined": datetime.now(timezone.utc).isoformat(),
        "total_earned": 0.0, "active": True,
    }
    data["collaborators"].append(new)
    collab_f.write_text(json.dumps(data, indent=2))
    print(f"  ✅ Registered: {name} ({role}) — {share_pct}% share → {paypal_email}")
    return new


def queue_payout(recipient_email, amount_usd, note, payout_type="collaborator"):
    """Queue a payout to be sent next cycle."""
    state = load_state()
    payout_id = f"sp_{int(datetime.now(timezone.utc).timestamp())}"
    state["pending"].append({
        "id": payout_id, "type": payout_type,
        "email": recipient_email, "amount_usd": amount_usd,
        "note": note, "queued": datetime.now(timezone.utc).isoformat(),
    })
    save_state(state)


def process_pending(state):
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        return state
    pending = state.get("pending", [])
    if not pending:
        return state
    try:
        token = get_token()
    except Exception as e:
        print(f"  ❌ PayPal auth failed: {e}")
        return state

    processed = []
    for p in pending:
        result = send_payout(token, p["email"], p["amount_usd"], p["note"], p["id"])
        p["result"] = result
        p["processed_at"] = datetime.now(timezone.utc).isoformat()
        if result["success"]:
            state["payouts"].append(p)
            state["total_paid_usd"] = round(state["total_paid_usd"] + p["amount_usd"], 2)
            if p.get("type") == "gaza":
                state["total_to_gaza_usd"] = round(state["total_to_gaza_usd"] + p["amount_usd"], 2)
            print(f"  ✅ Paid ${p['amount_usd']:.2f} → {p['email']}")
        else:
            state["failed"].append(p)
            print(f"  ❌ Failed: {p['email']} — {result.get('error','')[:60]}")
        processed.append(p["id"])

    state["pending"] = [p for p in pending if p["id"] not in processed]
    return state


def build_ledger_page(state):
    paid = state.get("total_paid_usd", 0)
    gaza = state.get("total_to_gaza_usd", 0)
    mode = PAYPAL_MODE.upper()
    payouts = state.get("payouts", [])[-20:]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = "".join(
        f"<tr><td>{'🌹' if p.get('type')=='gaza' else '💸'}</td>"
        f"<td>{p.get('processed_at','')[:10]}</td>"
        f"<td>${p.get('amount_usd',0):.2f}</td>"
        f"<td>{p.get('note','')[:60]}</td></tr>\n"
        for p in reversed(payouts)
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk™ Payout Ledger</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060e;color:#dde;font-family:-apple-system,sans-serif;padding:30px;max-width:800px;margin:0 auto}}
nav{{margin-bottom:24px;display:flex;gap:12px;flex-wrap:wrap}}
nav a{{color:rgba(255,255,255,.35);text-decoration:none;font-size:.8rem}}
nav a:hover{{color:#00ff88}}
h1{{color:#00ff88;margin-bottom:6px}}
.sub{{color:#555;font-size:.82rem;margin-bottom:20px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}}
.stat{{background:#0f0f1c;border:1px solid #1a1a2e;border-radius:8px;padding:14px 20px;text-align:center}}
.stat .n{{font-size:1.8rem;font-weight:700;color:#00ff88}}
.stat .l{{font-size:.7rem;color:#555;text-transform:uppercase}}
.no-paypal{{background:#1a0a0a;border:1px solid rgba(255,87,34,.2);border-radius:8px;padding:16px;margin-bottom:20px}}
.no-paypal h3{{color:#ff7043;margin-bottom:8px;font-size:.9rem}}
.no-paypal ol{{padding-left:18px;color:#888;font-size:.82rem;line-height:2}}
.no-paypal code{{background:#0a0a0a;padding:1px 6px;border-radius:3px;color:#ffb74d}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px;background:#0a0a18;color:#555;font-size:.72rem;text-transform:uppercase;letter-spacing:1px}}
td{{padding:10px;border-bottom:1px solid rgba(255,255,255,.04);font-size:.82rem;color:#aaa}}
.note{{background:#0a0a18;border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:14px;margin-top:20px;font-size:.78rem;color:#555;line-height:1.8}}
.note a{{color:#ff4d6d;text-decoration:none}}
</style></head><body>
<nav>
  <a href="index.html">Home</a> ·
  <a href="dashboard.html">Dashboard</a> ·
  <a href="store.html">Store</a> ·
  <a href="art.html">Art</a>
</nav>
<h1>💸 SolarPunk™ Payout Ledger</h1>
<p class="sub">Transparent auto-generated ledger. Updated {now}. Mode: {mode}.</p>

<div class="stats">
  <div class="stat"><div class="n">${paid:.2f}</div><div class="l">Total Paid Out</div></div>
  <div class="stat"><div class="n">${gaza:.2f}</div><div class="l">→ Gaza (PCRF)</div></div>
  <div class="stat"><div class="n">{len(state.get('payouts',[]))}</div><div class="l">Payouts Made</div></div>
  <div class="stat"><div class="n">{len(state.get('pending',[]))}</div><div class="l">Pending</div></div>
</div>

{"" if PAYPAL_CLIENT_ID else '''<div class="no-paypal">
<h3>⚠️ PayPal not connected — enable to auto-send payouts</h3>
<ol>
<li>Go to <b>developer.paypal.com</b> — sign in with PayPal</li>
<li>My Apps &amp; Credentials → <b>Create App</b> → name: "SolarPunk"</li>
<li>Copy <b>Client ID</b> and <b>Secret</b></li>
<li>GitHub Secrets → Add: <code>PAYPAL_CLIENT_ID</code> and <code>PAYPAL_CLIENT_SECRET</code></li>
<li>Also add: <code>PAYPAL_MODE</code> = <code>sandbox</code> (test first, then switch to <code>live</code>)</li>
</ol>
</div>'''}

<table>
<tr><th></th><th>Date</th><th>Amount</th><th>Description</th></tr>
{rows if rows else '<tr><td colspan="4" style="color:#333;padding:20px;text-align:center">No payouts yet — connect PayPal to enable</td></tr>'}
</table>

<div class="note">
🌹 Gaza donations go to <a href="https://www.pcrf.net" target="_blank">PCRF</a> (EIN 93-1057665, 4★ Charity Navigator).<br>
💸 Collaborator payouts are automatic — revenue share configures in HUMAN_PAYOUT engine.<br>
🔒 PayPal handles all financial security. SolarPunk™ never stores payment details.
</div>
</body></html>"""

    (DOCS / "payouts.html").write_text(html)


def run():
    print("HUMAN_PAYOUT running...")
    state = load_state()

    if not PAYPAL_CLIENT_ID:
        print("  ⚠️  PAYPAL not configured")
        print("  → developer.paypal.com → My Apps → Create App → copy keys → GitHub Secrets")
        print("  → PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET + PAYPAL_MODE=sandbox")
    else:
        print(f"  PayPal mode: {PAYPAL_MODE} | Pending payouts: {len(state.get('pending', []))}")
        state = process_pending(state)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    build_ledger_page(state)
    print(f"  Total paid: ${state['total_paid_usd']:.2f} | → Gaza: ${state['total_to_gaza_usd']:.2f}")
    print(f"  ✅ docs/payouts.html updated")


if __name__ == "__main__": run()
