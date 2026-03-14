# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BRAND_LEGAL — SolarPunk™ legal infrastructure engine
FIX: revenue_inbox.json can be a list — guard with isinstance check.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

FIRST_USE = "2026-03-05"
BRAND     = "SolarPunk™"
OWNER     = "Meeko (MeekoThaRaccoon)"

MILESTONES = [
    {"id": "dba",      "label": "File DBA — 'SolarPunk' fictitious business name", "cost": 50,  "notes": "~$50, county clerk."},
    {"id": "llc",      "label": "Form SolarPunk LLC",                               "cost": 100, "notes": "~$100, state filing."},
    {"id": "uspto_9",  "label": "USPTO Class 9 — Software / AI tools",              "cost": 400, "notes": "$400/class."},
    {"id": "uspto_35", "label": "USPTO Class 35 — Business services",               "cost": 400, "notes": "$400/class."},
    {"id": "uspto_42", "label": "USPTO Class 42 — AI / tech services",              "cost": 400, "notes": "$400/class."},
]
TOTAL_USPTO = sum(m["cost"] for m in MILESTONES)

STATE_FILE = DATA / "brand_legal_state.json"

def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: pass
    return {
        "brand": BRAND, "owner": OWNER,
        "first_use_in_commerce": FIRST_USE, "symbol": "™",
        "status": "common_law", "legal_fund_usd": 0.0,
        "total_revenue_tracked": 0.0, "legal_fund_rate": 0.10,
        "milestones_complete": [], "notes": [], "last_updated": None,
    }

state = load_state()

def rj_dict(fname):
    """Load JSON, always return a DICT. If list/invalid, return {}."""
    f = DATA / fname
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                return data
        except: pass
    return {}

revenue       = rj_dict("revenue_inbox.json")
payout_ledger = rj_dict("payout_ledger.json")
flywheel      = rj_dict("flywheel_summary.json")

total_revenue = revenue.get("total_received", 0) or flywheel.get("total_revenue_usd", 0)
legal_fund    = round(total_revenue * state["legal_fund_rate"], 2)

state["legal_fund_usd"]        = legal_fund
state["total_revenue_tracked"] = total_revenue

completed      = list(state.get("milestones_complete", []))
running_cost   = 0
auto_completed = []
for m in MILESTONES:
    running_cost += m["cost"]
    if legal_fund >= running_cost and m["id"] not in completed:
        completed.append(m["id"])
        auto_completed.append(m["id"])
state["milestones_complete"] = completed

if "llc" in completed:
    if "uspto_42" in completed: state["status"] = "registered_®"; state["symbol"] = "®"
    elif "uspto_9" in completed: state["status"] = "partial_®";   state["symbol"] = "®"
    else:                        state["status"] = "llc_formed";   state["symbol"] = "™"
elif "dba" in completed:         state["status"] = "dba_filed";    state["symbol"] = "™"
else:                            state["status"] = "common_law";   state["symbol"] = "™"

product_revenue  = revenue.get("product_revenue", total_revenue * 0.6)
gaza_due         = round(product_revenue * 0.15, 2)
gaza_paid        = payout_ledger.get("total_gaza_donated", 0)
gaza_outstanding = max(0, round(gaza_due - gaza_paid, 2))

state["last_updated"]              = datetime.now(timezone.utc).isoformat()
state["upto_fund_collected"]       = legal_fund
state["total_milestone_cost"]      = TOTAL_USPTO
state["pct_to_goal"]               = round(legal_fund / TOTAL_USPTO * 100, 1) if TOTAL_USPTO else 0
state["gaza_due_total"]            = gaza_due
state["gaza_paid_total"]           = gaza_paid
state["gaza_outstanding"]          = gaza_outstanding
state["auto_completed_this_cycle"] = auto_completed

STATE_FILE.write_text(json.dumps(state, indent=2))

def milestone_rows():
    rows = []
    running = 0
    for m in MILESTONES:
        running += m["cost"]
        done = m["id"] in completed
        pct  = min(100, round(legal_fund / running * 100)) if running else 0
        sc   = "done" if done else "pending"
        sl   = "✅ COMPLETE" if done else f"⏳ {pct}%"
        rows.append(f'<tr class="{sc}"><td>{m["label"]}</td><td>${m["cost"]:,}</td><td>${running:,}</td><td>{sl}</td><td>{m["notes"]}</td></tr>')
    return "\n".join(rows)

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{BRAND} Legal</title>
<style>body{{background:#0f172a;color:#e2e8f0;font-family:sans-serif;padding:2rem}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:.5rem;border-bottom:1px solid #334155}}
.done td{{color:#22c55e}}.pending td{{color:#94a3b8}}</style></head><body>
<h1>{BRAND} — Legal: {state['status']}</h1>
<p>Legal fund: ${legal_fund:.2f} / ${TOTAL_USPTO:,} ({state['pct_to_goal']}%) | Milestones: {len(completed)}/{len(MILESTONES)}</p>
<p>Gaza outstanding: ${gaza_outstanding:.2f} | First use: {FIRST_USE}</p>
<table><thead><tr><th>Action</th><th>Cost</th><th>Running</th><th>Status</th><th>Notes</th></tr></thead>
<tbody>{milestone_rows()}</tbody></table>
<p style="margin-top:1rem;color:#94a3b8">15% of revenue → PCRF. Auto-updated by BRAND_LEGAL.</p>
</body></html>"""

(DOCS / "legal.html").write_text(html)

print(f"⚖️  {BRAND} — {state['status']} | Fund: ${legal_fund:.2f} / ${TOTAL_USPTO:,}")
print(f"   Milestones: {len(completed)}/{len(MILESTONES)} | Gaza: ${gaza_outstanding:.2f} outstanding")
if auto_completed:
    print(f"   🎉 Unlocked: {', '.join(auto_completed)}")
print(f"   📄 docs/legal.html updated")
