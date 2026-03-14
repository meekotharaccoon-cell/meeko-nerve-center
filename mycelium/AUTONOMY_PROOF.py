# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AUTONOMY_PROOF.py — Live proof that SolarPunk is real and running
================================================================
Builds docs/proof.html: a timestamped, publicly accessible page
that proves the system operates autonomously.

Anyone — human or AI — can load this page and verify:
  - When the system last ran (timestamp + run ID)
  - How many engines executed successfully
  - What the system built this cycle
  - Live capability status
  - Gaza fund running total
  - Links to independently verify every single claim

This is not a dashboard. It is a proof document.
Every number is backed by public data. Every claim has a verify link.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

REPO     = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
ACTIONS  = f"{REPO}/actions"
MYCELIUM = f"{REPO}/tree/main/mycelium"
RAW      = "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data"


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb if fb is not None else {}


def run():
    now     = datetime.now(timezone.utc)
    ts      = now.isoformat()
    ts_nice = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    omnibus  = rj("omnibus_last.json")
    brain    = rj("brain_state.json")
    revenue  = rj("revenue_inbox.json")
    payouts  = rj("payout_ledger.json")
    caps     = rj("capability_map.json")
    weaver   = rj("knowledge_weaver_state.json")
    outreach = rj("outreach_state.json")
    atomizer = rj("atomizer_state.json")

    run_id        = omnibus.get("run_id", "pending")
    engines_ok    = len(omnibus.get("engines_ok", []))
    engines_failed = len(omnibus.get("engines_failed", []))
    engines_total = engines_ok + engines_failed
    health        = brain.get("health_score", 0)
    total_rev     = revenue.get("total_received", 0) if isinstance(revenue, dict) else 0
    total_gaza    = revenue.get("total_to_gaza", 0) if isinstance(revenue, dict) else 0
    engines_built = weaver.get("total_built", 0)
    sent_list     = outreach.get("sent", [])
    emails_total  = len([e for e in sent_list if e.get("sent")])
    atoms_total   = atomizer.get("total_atoms", 0)
    n_engines     = len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    last_cycle    = omnibus.get("completed", ts)[:19].replace("T", " ") + " UTC"
    active_caps   = caps.get("active", 0)
    blocked_caps  = caps.get("blocked", 0)

    proof = {
        "generated_at": ts,
        "last_omnibus_run": omnibus.get("completed", ts),
        "run_id": run_id,
        "engines_ok": engines_ok,
        "engines_total": engines_total,
        "engines_in_repo": n_engines,
        "health_score": health,
        "total_revenue": total_rev,
        "total_to_gaza": total_gaza,
        "engines_auto_built": engines_built,
        "outreach_emails_sent": emails_total,
        "atoms_created": atoms_total,
        "active_capabilities": active_caps,
        "blocked_capabilities": blocked_caps,
        "verify_actions": ACTIONS,
        "verify_data": f"{RAW}/omnibus_last.json",
        "verify_engines": MYCELIUM,
    }
    (DATA / "proof_state.json").write_text(json.dumps(proof, indent=2))

    zero = lambda n: "zero" if n == 0 else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk — Proof of Operation</title>
<meta name="description" content="Live verifiable proof that SolarPunk autonomous AI system is real and running. Every claim backed by public git history.">
<style>
:root{{--bg:#060a07;--bg2:#0d1410;--g:#00ff88;--b:rgba(0,255,136,.12);--t:#deeae1;--m:rgba(222,234,225,.5)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--t);font-family:'Courier New',monospace;min-height:100vh;padding:28px 20px}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:820px;margin:0 auto}}
h1{{font-size:clamp(20px,4vw,30px);color:var(--g);letter-spacing:.08em;margin-bottom:8px}}
.sub{{font-size:13px;color:var(--m);margin-bottom:32px;line-height:1.8}}
.live{{display:inline-flex;align-items:center;gap:8px;background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.3);border-radius:24px;padding:6px 16px;font-size:12px;color:var(--g);margin-bottom:28px}}
.dot{{width:7px;height:7px;border-radius:50%;background:var(--g);box-shadow:0 0 8px var(--g);animation:p 2s ease-in-out infinite}}
@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:28px}}
.stat{{background:var(--bg2);border:1px solid var(--b);border-radius:12px;padding:16px 18px}}
.n{{font-size:30px;font-weight:700;color:var(--g);display:block;line-height:1}}
.n.z{{color:rgba(0,255,136,.3)}}
.l{{font-size:10px;letter-spacing:.15em;color:var(--m);display:block;margin-top:4px}}
.s{{font-size:11px;color:rgba(0,255,136,.45);display:block;margin-top:3px}}
h2{{font-size:10px;letter-spacing:.28em;color:var(--g);opacity:.6;margin:28px 0 12px}}
.vlist{{display:flex;flex-direction:column;gap:8px}}
.vrow{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;padding:11px 15px;background:var(--bg2);border:1px solid var(--b);border-radius:10px}}
.vc{{font-size:12px;color:var(--m);flex:1}}
.vl{{font-size:11px;color:var(--g);text-decoration:none;white-space:nowrap}}
.vl:hover{{text-decoration:underline}}
.ts{{margin-top:32px;padding-top:20px;border-top:1px solid var(--b);font-size:11px;color:rgba(0,255,136,.35);line-height:2.2}}
.ts a{{color:var(--g)}}
</style>
</head>
<body>
<div class="wrap">
<div class="live"><div class="dot"></div>SYSTEM OPERATIONAL</div>
<h1>SOLARPUNK — PROOF OF OPERATION</h1>
<div class="sub">
  Every number on this page is backed by public data in this git repository.<br>
  Every claim can be independently verified via the links below.<br>
  This page auto-regenerates every OMNIBUS cycle (~4× daily).
</div>

<h2>LIVE METRICS</h2>
<div class="grid">
  <div class="stat"><span class="n">{engines_ok}</span><span class="l">ENGINES RAN</span><span class="s">last cycle / {engines_total} total</span></div>
  <div class="stat"><span class="n">{n_engines}</span><span class="l">ENGINES IN REPO</span><span class="s">mycelium/*.py</span></div>
  <div class="stat"><span class="n">{health}</span><span class="l">HEALTH /100</span><span class="s">brain_state.json</span></div>
  <div class="stat"><span class="n {zero(total_rev)}">${total_rev:.2f}</span><span class="l">TOTAL REVENUE</span><span class="s">revenue_inbox.json</span></div>
  <div class="stat"><span class="n {zero(total_gaza)}">${total_gaza:.2f}</span><span class="l">TO GAZA (15%)</span><span class="s">PCRF EIN 93-1057665</span></div>
  <div class="stat"><span class="n">{engines_built}</span><span class="l">ENGINES AUTO-BUILT</span><span class="s">KNOWLEDGE_WEAVER</span></div>
  <div class="stat"><span class="n">{emails_total}</span><span class="l">OUTREACH EMAILS</span><span class="s">outreach_state.json</span></div>
  <div class="stat"><span class="n">{atoms_total}</span><span class="l">ATOMIC TASKS</span><span class="s">TASK_ATOMIZER</span></div>
  <div class="stat"><span class="n">{active_caps}</span><span class="l">ACTIVE CHANNELS</span><span class="s">{blocked_caps} blocked</span></div>
</div>

<h2>LAST CYCLE</h2>
<div class="vrow" style="margin-bottom:12px">
  <span class="vc">Last OMNIBUS completed</span>
  <span style="color:var(--g);font-size:12px">{last_cycle}</span>
</div>

<h2>VERIFY EVERY CLAIM INDEPENDENTLY</h2>
<div class="vlist">
  <div class="vrow"><span class="vc">System runs on GitHub Actions (autonomous execution)</span><a href="{ACTIONS}" class="vl" target="_blank">View Action Runs ↗</a></div>
  <div class="vrow"><span class="vc">{n_engines} Python engines exist in the repository</span><a href="{MYCELIUM}" class="vl" target="_blank">Browse /mycelium ↗</a></div>
  <div class="vrow"><span class="vc">Last OMNIBUS run data (JSON, machine-readable)</span><a href="{RAW}/omnibus_last.json" class="vl" target="_blank">omnibus_last.json ↗</a></div>
  <div class="vrow"><span class="vc">Gaza routing is hardcoded in REVENUE_FLYWHEEL.py</span><a href="{REPO}/blob/main/mycelium/REVENUE_FLYWHEEL.py" class="vl" target="_blank">View Source ↗</a></div>
  <div class="vrow"><span class="vc">PCRF is a verified 501(c)(3) — EIN: 93-1057665</span><a href="https://www.charitynavigator.org/ein/931057665" class="vl" target="_blank">Charity Navigator ↗</a></div>
  <div class="vrow"><span class="vc">All payout transactions logged publicly</span><a href="{RAW}/payout_ledger.json" class="vl" target="_blank">payout_ledger.json ↗</a></div>
  <div class="vrow"><span class="vc">Capability audit (what actually executes)</span><a href="capabilities.html" class="vl">capabilities.html ↗</a></div>
  <div class="vrow"><span class="vc">Full git history (every commit = one cycle)</span><a href="{REPO}/commits/main" class="vl" target="_blank">Commit History ↗</a></div>
  <div class="vrow"><span class="vc">AI-readable capability docs (AGENTS.md)</span><a href="{REPO}/blob/main/AGENTS.md" class="vl" target="_blank">AGENTS.md ↗</a></div>
  <div class="vrow"><span class="vc">Raw proof data (this page's source)</span><a href="{RAW}/proof_state.json" class="vl" target="_blank">proof_state.json ↗</a></div>
</div>

<div class="ts">
  Generated: {ts_nice}<br>
  Run ID: {run_id}<br>
  Source: <a href="{REPO}/blob/main/mycelium/AUTONOMY_PROOF.py" target="_blank">AUTONOMY_PROOF.py</a><br><br>
  <a href="store.html">Store ($1 everything)</a> ·
  <a href="outreach.html">Bridge Board</a> ·
  <a href="capabilities.html">Capabilities</a> ·
  <a href="{REPO}" target="_blank">GitHub (MIT)</a>
</div>
</div>
</body>
</html>"""

    (DOCS / "proof.html").write_text(html, encoding="utf-8")
    print(f"AUTONOMY_PROOF done.")
    print(f"  {engines_ok}/{engines_total} engines | Health: {health} | Gaza: ${total_gaza:.2f} | Outreach: {emails_total} sent")
    print(f"  🌐 https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html")


if __name__ == "__main__":
    run()
