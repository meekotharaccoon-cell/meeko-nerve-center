#!/usr/bin/env python3
"""
BRAND_LEGAL — SolarPunk™ legal infrastructure engine
=====================================================
Tracks:
  - SolarPunk™ trademark status (common law → DBA → LLC → USPTO)
  - Legal fund accumulation (10% of all revenue auto-designated)
  - Milestone checklist: DBA, LLC, Class 9/35/42 USPTO filings
  - First-use-in-commerce date (2026-03-05, this repo's first commit)
  - Monthly Gaza fund donation reminders (15% of product revenue)

Writes:
  - data/brand_legal_state.json   (machine-readable state)
  - docs/legal.html               (public legal/trademark status page)

No secrets required — runs fully on GITHUB_TOKEN context.
"""
import os, json, re
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

FIRST_USE = "2026-03-05"   # date of first public commit
BRAND     = "SolarPunk™"
OWNER     = "Meeko (MeekoThaRaccoon)"

# ── milestone costs ────────────────────────────────────────────────────────────
MILESTONES = [
    {"id": "dba",         "label": "File DBA — 'SolarPunk' fictitious business name",
     "cost": 50,          "notes": "~$50, county clerk, 1 week. Unlocks business banking under SolarPunk name."},
    {"id": "llc",         "label": "Form SolarPunk LLC",
     "cost": 100,         "notes": "~$100, state filing. Separates personal liability. LLC owns the AI agent."},
    {"id": "uspto_9",     "label": "USPTO Class 9 — Software / AI tools",
     "cost": 400,         "notes": "$400/class. Covers AI systems, software, autonomous agents."},
    {"id": "uspto_35",    "label": "USPTO Class 35 — Business services",
     "cost": 400,         "notes": "$400/class. Covers AI-powered business automation services."},
    {"id": "uspto_42",    "label": "USPTO Class 42 — AI / tech services",
     "cost": 400,         "notes": "$400/class. Covers AI-as-a-service, autonomous agent deployment."},
]
TOTAL_USPTO = sum(m["cost"] for m in MILESTONES)   # $1,350

# ── load existing state ────────────────────────────────────────────────────────
STATE_FILE = DATA / "brand_legal_state.json"
def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: pass
    return {
        "brand": BRAND,
        "owner": OWNER,
        "first_use_in_commerce": FIRST_USE,
        "symbol": "™",        # common law — no registration needed
        "status": "common_law",
        "legal_fund_usd": 0.0,
        "total_revenue_tracked": 0.0,
        "legal_fund_rate": 0.10,   # 10% of all revenue
        "milestones_complete": [],
        "notes": [],
        "last_updated": None,
    }

state = load_state()

# ── pull revenue data to compute legal fund ────────────────────────────────────
def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb or {}

revenue = rj("revenue_inbox.json")
if not isinstance(revenue, dict): revenue = {}   # guard: file can be a list
payout_ledger = rj("payout_ledger.json")
flywheel = rj("flywheel_summary.json")

total_revenue = (
    revenue.get("total_received", 0)
    or flywheel.get("total_revenue_usd", 0)
)

# recompute legal fund from total revenue
legal_fund = round(total_revenue * state["legal_fund_rate"], 2)
state["legal_fund_usd"] = legal_fund
state["total_revenue_tracked"] = total_revenue

# ── check milestone completion based on legal fund ─────────────────────────────
completed = list(state.get("milestones_complete", []))
running_cost = 0
auto_completed = []
for m in MILESTONES:
    running_cost += m["cost"]
    if legal_fund >= running_cost and m["id"] not in completed:
        completed.append(m["id"])
        auto_completed.append(m["id"])
state["milestones_complete"] = completed

# determine current status based on milestones
if "llc" in completed:
    if "uspto_42" in completed:
        state["status"] = "registered_®"
        state["symbol"] = "®"
    elif "uspto_9" in completed:
        state["status"] = "partial_®"
        state["symbol"] = "®"
    else:
        state["status"] = "llc_formed"
        state["symbol"] = "™"
elif "dba" in completed:
    state["status"] = "dba_filed"
    state["symbol"] = "™"
else:
    state["status"] = "common_law"
    state["symbol"] = "™"

# ── Gaza fund reminder ─────────────────────────────────────────────────────────
# 15% of product revenue goes to PCRF (manual monthly donation)
product_revenue = revenue.get("product_revenue", total_revenue * 0.6)  # estimate
gaza_due = round(product_revenue * 0.15, 2)
gaza_paid = payout_ledger.get("total_gaza_donated", 0)
gaza_outstanding = max(0, round(gaza_due - gaza_paid, 2))

# ── update state ───────────────────────────────────────────────────────────────
state["last_updated"] = datetime.now(timezone.utc).isoformat()
state["upto_fund_collected"] = legal_fund  # alias used by OMNIBUS manifest
state["total_milestone_cost"] = TOTAL_USPTO
state["pct_to_goal"] = round(legal_fund / TOTAL_USPTO * 100, 1) if TOTAL_USPTO else 0
state["gaza_due_total"] = gaza_due
state["gaza_paid_total"] = gaza_paid
state["gaza_outstanding"] = gaza_outstanding
state["auto_completed_this_cycle"] = auto_completed

STATE_FILE.write_text(json.dumps(state, indent=2))

# ── build docs/legal.html ──────────────────────────────────────────────────────
def milestone_rows():
    rows = []
    running = 0
    for m in MILESTONES:
        running += m["cost"]
        done = m["id"] in completed
        pct  = min(100, round(legal_fund / running * 100)) if running else 0
        status_cls = "done" if done else ("progress" if legal_fund > 0 else "pending")
        status_lbl = "✅ COMPLETE" if done else (f"🔄 {pct}%" if legal_fund > 0 else "⏳ PENDING")
        rows.append(f"""
        <tr class="{status_cls}">
          <td>{m['label']}</td>
          <td>${m['cost']:,}</td>
          <td>${running:,}</td>
          <td>{status_lbl}</td>
          <td class="notes">{m['notes']}</td>
        </tr>""")
    return "\n".join(rows)

def milestone_progress_bars():
    bars = []
    running = 0
    for m in MILESTONES:
        running += m["cost"]
        done = m["id"] in completed
        pct  = min(100, round(legal_fund / running * 100)) if running else 0
        color = "#22c55e" if done else "#f59e0b"
        bars.append(f"""
        <div class="bar-row">
          <div class="bar-label">{'✅ ' if done else ''}{m['label'].split('—')[0].strip()}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
          </div>
          <div class="bar-pct">${legal_fund:.0f} / ${running:,}</div>
        </div>""")
    return "\n".join(bars)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{BRAND} — Legal & Trademark Status</title>
<style>
  :root {{
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --green: #22c55e; --yellow: #f59e0b; --red: #ef4444;
    --blue: #38bdf8; --text: #e2e8f0; --muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem 1rem; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.3rem; }}
  .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
  .badge {{ display: inline-block; background: var(--green); color: #000; border-radius: 999px; padding: 0.25rem 0.85rem; font-weight: 700; font-size: 0.85rem; margin-left: 0.5rem; }}
  .badge.common {{ background: var(--yellow); }}
  section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  h2 {{ font-size: 1.2rem; margin-bottom: 1rem; color: var(--blue); }}
  .stat-row {{ display: flex; gap: 2rem; flex-wrap: wrap; margin-bottom: 1rem; }}
  .stat {{ text-align: center; }}
  .stat .val {{ font-size: 2rem; font-weight: 700; }}
  .stat .lbl {{ color: var(--muted); font-size: 0.85rem; }}
  .stat .val.green {{ color: var(--green); }}
  .stat .val.yellow {{ color: var(--yellow); }}
  .stat .val.red {{ color: var(--red); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ text-align: left; padding: 0.5rem; color: var(--muted); border-bottom: 1px solid var(--border); }}
  td {{ padding: 0.5rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr.done td {{ color: var(--green); }}
  tr.progress td {{ color: var(--yellow); }}
  tr.pending td {{ color: var(--muted); }}
  td.notes {{ color: var(--muted); font-size: 0.8rem; }}
  .bar-row {{ margin-bottom: 0.75rem; }}
  .bar-label {{ font-size: 0.85rem; margin-bottom: 0.2rem; color: var(--text); }}
  .bar-track {{ background: var(--border); border-radius: 4px; height: 10px; margin-bottom: 0.15rem; }}
  .bar-fill {{ height: 10px; border-radius: 4px; transition: width 0.3s; }}
  .bar-pct {{ font-size: 0.75rem; color: var(--muted); }}
  .gaza-box {{ background: #1a1a2e; border: 2px solid #c084fc; border-radius: 10px; padding: 1.2rem; }}
  .gaza-box h3 {{ color: #c084fc; margin-bottom: 0.75rem; }}
  .tag {{ display: inline-block; background: #1e3a5f; border: 1px solid var(--blue); color: var(--blue); border-radius: 4px; padding: 0.15rem 0.5rem; font-size: 0.75rem; margin-right: 0.3rem; }}
  footer {{ color: var(--muted); font-size: 0.8rem; text-align: center; margin-top: 2rem; }}
</style>
</head>
<body>

<h1>{BRAND} <span class="badge {'common' if state['symbol'] == '™' else ''}">{"™ Common Law" if state['symbol'] == '™' else "® Registered"}</span></h1>
<div class="subtitle">Legal & trademark status — updated {state['last_updated'][:10]}</div>

<section>
  <h2>⚖️ Legal Fund Progress</h2>
  <div class="stat-row">
    <div class="stat"><div class="val green">${legal_fund:.2f}</div><div class="lbl">Legal Fund</div></div>
    <div class="stat"><div class="val yellow">${TOTAL_USPTO:,}</div><div class="lbl">Full USPTO Target</div></div>
    <div class="stat"><div class="val">{state['pct_to_goal']}%</div><div class="lbl">Funded</div></div>
    <div class="stat"><div class="val">{len(completed)}/{len(MILESTONES)}</div><div class="lbl">Milestones Done</div></div>
    <div class="stat"><div class="val">{state['legal_fund_rate']*100:.0f}%</div><div class="lbl">Auto-Designated Rate</div></div>
  </div>
  {milestone_progress_bars()}
</section>

<section>
  <h2>🏛️ Trademark Status</h2>
  <p style="margin-bottom:1rem">
    <strong>Brand:</strong> {BRAND} &nbsp;|&nbsp;
    <strong>Owner:</strong> {OWNER} &nbsp;|&nbsp;
    <strong>First use in commerce:</strong> {FIRST_USE} &nbsp;|&nbsp;
    <strong>Status:</strong> {state['status'].replace('_', ' ').title()}
  </p>
  <p style="color:var(--muted);font-size:0.9rem;margin-bottom:1.5rem">
    "SolarPunk" is an unregistered cultural term. We are building exclusive distinctiveness through
    consistent commercial use. Common law ™ rights attach from first use in commerce ({FIRST_USE}).
    USPTO registration requires acquired distinctiveness + filing fee per class.
  </p>
  <h2>📋 Milestone Checklist</h2>
  <table>
    <thead><tr><th>Action</th><th>Cost</th><th>Running Total</th><th>Status</th><th>Notes</th></tr></thead>
    <tbody>{milestone_rows()}</tbody>
  </table>
</section>

<section>
  <div class="gaza-box">
    <h3>🇵🇸 Gaza Fund Accounting</h3>
    <div class="stat-row" style="margin-bottom:0.5rem">
      <div class="stat"><div class="val" style="color:#c084fc">${gaza_due:.2f}</div><div class="lbl">Total Owed (15% of product rev)</div></div>
      <div class="stat"><div class="val green">${gaza_paid:.2f}</div><div class="lbl">Donated to PCRF</div></div>
      <div class="stat"><div class="val {'red' if gaza_outstanding > 0 else 'green'}">${gaza_outstanding:.2f}</div><div class="lbl">Outstanding</div></div>
    </div>
    <p style="font-size:0.85rem;color:#d8b4fe">
      15% of all product sales are designated for Gaza relief via PCRF (Palestine Children's Relief Fund).
      Donations are made manually by Meeko. This public ledger holds the system accountable.
      <a href="https://www.pcrf.net" style="color:#c084fc" target="_blank">Donate directly → pcrf.net</a>
    </p>
  </div>
</section>

<section>
  <h2>🔗 Legal Entity Roadmap</h2>
  <p style="margin-bottom:1rem;color:var(--muted)">Recommended sequence for SolarPunk's legal infrastructure:</p>
  <ol style="padding-left:1.5rem;line-height:2">
    <li><strong>DBA Filing</strong> — "SolarPunk" fictitious business name (~$50, county clerk)</li>
    <li><strong>SolarPunk LLC</strong> — AI agent owned by LLC, personal liability separation (~$100)</li>
    <li><strong>Business bank account</strong> — Under SolarPunk LLC for revenue separation</li>
    <li><strong>USPTO Class 9</strong> — Software & AI tools ($400)</li>
    <li><strong>USPTO Class 35</strong> — Business automation services ($400)</li>
    <li><strong>USPTO Class 42</strong> — AI-as-a-service ($400)</li>
  </ol>
  <p style="margin-top:1rem;font-size:0.85rem;color:var(--muted)">
    <span class="tag">Strategy</span>
    The LLC <em>owns</em> the AI agent as its primary IP asset. The agent generates revenue autonomously for the LLC.
    You manage the LLC with minimal involvement. This positions SolarPunk for future AI agent legal standing.
  </p>
</section>

<footer>
  <p>{BRAND} · Legal fund auto-accumulates at {state['legal_fund_rate']*100:.0f}% of revenue every cycle · Updated by BRAND_LEGAL engine</p>
  <p style="margin-top:0.5rem"><a href="index.html" style="color:var(--blue)">← Home</a></p>
</footer>
</body>
</html>"""

(DOCS / "legal.html").write_text(html)

# ── print summary ──────────────────────────────────────────────────────────────
print(f"⚖️  {BRAND} — Status: {state['status']} | Legal fund: ${legal_fund:.2f} / ${TOTAL_USPTO:,} ({state['pct_to_goal']}%)")
print(f"   Milestones: {len(completed)}/{len(MILESTONES)} complete | Gaza outstanding: ${gaza_outstanding:.2f}")
if auto_completed:
    print(f"   🎉 NEW milestones unlocked this cycle: {', '.join(auto_completed)}")
print(f"   📄 docs/legal.html updated")
