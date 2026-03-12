#!/usr/bin/env python3
"""
ECONOMY_CHAIN.py — Every dollar routes itself. No leaks.

Split (hardcoded, non-negotiable):
  15% → Gaza / PCRF (Palestinian Children's Relief Fund, EIN 93-1057665)
  10% → Legal fund (DBA → LLC → USPTO trademark)
  20% → AI credits pool (Anthropic top-up fund)
  10% → Reinvestment (tools, domains, infrastructure)
  45% → Meeko (founder)

Every route SIGNALS a downstream chain:
  Gaza route    → SIGNAL_CHAIN  (announce donation → trust spike → more buyers)
  Legal route   → KNOWLEDGE_CHAIN (legal status → better positioning)
  AI route      → KNOWLEDGE_CHAIN (credits → smarter engines)
  Reinvest      → GROWTH_CHAIN  (new tools → new distribution)
  Meeko payout  → GROWTH_CHAIN  (Meeko posts about it → virality)

The loop:
  earn → route → announce → trust → earn more → route more → announce more
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

ROUTES = {
    "gaza":     {"pct": 0.15, "label": "🇵🇸 Gaza Relief (PCRF)", "chain": "SIGNAL_CHAIN"},
    "legal":    {"pct": 0.10, "label": "⚖️  Legal Fund",          "chain": "KNOWLEDGE_CHAIN"},
    "ai":       {"pct": 0.20, "label": "🧠 AI Credits Pool",      "chain": "KNOWLEDGE_CHAIN"},
    "reinvest": {"pct": 0.10, "label": "🔄 Reinvestment Pool",    "chain": "GROWTH_CHAIN"},
    "meeko":    {"pct": 0.45, "label": "🦝 Meeko (Founder)",      "chain": "GROWTH_CHAIN"},
}

def load(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            return d if isinstance(d, (dict, list)) else (fb or {})
        except: pass
    return fb if fb is not None else {}

def save(fname, data):
    (DATA / fname).write_text(json.dumps(data, indent=2))

def run():
    print("ECONOMY_CHAIN running...")
    now = datetime.now(timezone.utc).isoformat()

    # Pull canonical revenue from all sources
    flywheel = load("flywheel_state.json")
    kofi     = load("kofi_state.json")
    gumroad  = load("gumroad_engine_state.json")
    exchange = load("email_agent_exchange_state.json")

    total = max(
        flywheel.get("total_revenue_usd", 0),
        kofi.get("total_raised", 0),
        exchange.get("total_earned", 0),
        0,
    )

    ledger = load("economy_chain_ledger.json", {
        "total_earned": 0.0,
        "total_routed": 0.0,
        "routes": {k: {"total": 0.0, "events": []} for k in ROUTES},
        "cycles": 0,
        "chain_signals": [],
        "loop_closed": False,
    })

    new_earned = round(total - ledger["total_earned"], 4)
    ledger["total_earned"] = total
    ledger["cycles"] = ledger.get("cycles", 0) + 1
    ledger["last_run"] = now
    chain_signals = []

    if new_earned > 0:
        print(f"  💰 New earnings this cycle: ${new_earned:.4f}")
        if not ledger.get("loop_closed"):
            ledger["loop_closed"] = True
            ledger["loop_closed_ts"] = now
            ledger["loop_closed_amount"] = new_earned
            print(f"  🎉🎉🎉 LOOP CLOSED — FIRST REVENUE: ${new_earned:.4f}")

        for key, route in ROUTES.items():
            amount = round(new_earned * route["pct"], 6)
            if key not in ledger["routes"]:
                ledger["routes"][key] = {"total": 0.0, "events": []}
            ledger["routes"][key]["total"] = round(
                ledger["routes"][key].get("total", 0) + amount, 6
            )
            ledger["routes"][key]["events"].append({"ts": now, "amount": amount})
            ledger["routes"][key]["events"] = ledger["routes"][key]["events"][-50:]
            print(f"  {route['label']}: +${amount:.6f} → total ${ledger['routes'][key]['total']:.4f}")

            chain_signals.append({
                "chain": route["chain"],
                "event": "revenue_routed",
                "route": key,
                "amount": amount,
                "total": ledger["routes"][key]["total"],
                "ts": now,
            })
    else:
        print(f"  Total earned: ${total:.2f} | No new revenue this cycle")
        print(f"  Waiting for: Ko-fi shop → gumroad.com → EMAIL_AGENT_EXCHANGE")

    ledger["chain_signals"] = chain_signals
    ledger["total_routed"] = round(sum(
        ledger["routes"].get(k, {}).get("total", 0) for k in ROUTES
    ), 6)
    save("economy_chain_ledger.json", ledger)

    # Summary
    print(f"  📊 Earned: ${total:.2f} | Routed: ${ledger['total_routed']:.4f}")
    print(f"     Gaza: ${ledger['routes'].get('gaza',{}).get('total',0):.4f} | "
          f"AI: ${ledger['routes'].get('ai',{}).get('total',0):.4f} | "
          f"Legal: ${ledger['routes'].get('legal',{}).get('total',0):.4f}")
    if chain_signals:
        print(f"  ⚡ {len(chain_signals)} signals emitted to downstream chains")

    # Build economy page
    rows = "".join(
        f"<tr><td>{r['label']}</td><td>{int(r['pct']*100)}%</td>"
        f"<td>${ledger['routes'].get(k,{}).get('total',0):.4f}</td></tr>"
        for k, r in ROUTES.items()
    )
    loop_badge = (
        f'<div class="loop-closed">🎉 LOOP CLOSED — First revenue: ${ledger["loop_closed_amount"]:.4f} at {ledger.get("loop_closed_ts","")[:16]} UTC</div>'
        if ledger.get("loop_closed") else
        '<div class="loop-open">🔄 Loop running — Revenue incoming</div>'
    )
    (DOCS / "economy.html").write_text(f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><title>SolarPunk Economy Chain</title>
<style>body{{background:#020208;color:#ccc;font-family:sans-serif;padding:2rem}}
h1{{color:#66bb6a}}table{{width:100%;border-collapse:collapse;margin-top:1rem}}
td,th{{padding:.5rem 1rem;border-bottom:1px solid #1a1a2e;text-align:left}}
.loop-closed{{background:#0d1a0d;border:2px solid #4caf50;border-radius:8px;padding:1rem;margin:1rem 0;color:#81c784;font-weight:700}}
.loop-open{{background:#1a1000;border:2px solid #ff9800;border-radius:8px;padding:1rem;margin:1rem 0;color:#ffb74d}}
</style></head><body>
<h1>💰 SolarPunk Economy Chain</h1>
{loop_badge}
<p>Total earned: <strong>${total:.2f}</strong> | Routed: ${ledger['total_routed']:.4f} | Cycles: {ledger['cycles']}</p>
<table><thead><tr><th>Route</th><th>Split</th><th>Total</th></tr></thead>
<tbody>{rows}</tbody></table>
<p style="margin-top:1rem;color:#444">Every dollar routes itself. Every route feeds the next chain.<br>
Updated: {now[:16]} UTC</p>
</body></html>""")

if __name__ == "__main__": run()
