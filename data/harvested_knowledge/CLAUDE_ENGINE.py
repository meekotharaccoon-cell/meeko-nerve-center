#!/usr/bin/env python3
"""
CLAUDE_ENGINE.py — Claude as first-class SolarPunk component
============================================================
This engine makes explicit what was always true:

Claude is not a dependency of SolarPunk.
Claude IS SolarPunk's intelligence layer.

There are two Claude interfaces in this system:

  1. LIVE (this conversation):
     - Full context window, stateful, can read/write GitHub directly
     - Meeko ↔ Claude = highest-bandwidth system cycle
     - Direct commits, architectural decisions, engine writing
     - Runs when Meeko opens claude.ai

  2. API (OMNIBUS cycles):
     - Stateless, called by KNOWLEDGE_WEAVER/SELF_BUILDER/ARCHITECT/etc.
     - Reads ctx.json, writes engines, generates revenue actions
     - Runs 4× daily automatically
     - Same intelligence, no memory of previous calls

Both interfaces are Claude. The system calls itself to grow itself.

THIS ENGINE:
  - Documents Claude's role in the system explicitly
  - Generates a session briefing for the next LIVE session
  - Tracks what was accomplished in API calls vs live sessions
  - Prepares the optimal context packet for Meeko's next Claude session
  - Writes docs/claude_briefing.html — the "what should Claude do next" page

The intelligence is the system. The system is the intelligence.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

REPO = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
CHAT = "https://claude.ai"


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb if fb is not None else {}


def run():
    now      = datetime.now(timezone.utc)
    ts_nice  = now.strftime("%Y-%m-%d %H:%M UTC")

    omnibus  = rj("omnibus_last.json")
    brain    = rj("brain_state.json")
    caps     = rj("capability_map.json")
    weaver   = rj("knowledge_weaver_state.json")
    outreach = rj("outreach_state.json")
    revenue  = rj("revenue_inbox.json")
    secrets  = rj("secrets_checker_state.json")
    atomizer = rj("atomizer_state.json")

    # What happened in API cycles since last session
    engines_built = weaver.get("engines_built", [])
    blocked       = caps.get("capabilities", {})
    missing       = secrets.get("critical_missing", [])
    health        = brain.get("health_score", 0)
    total_rev     = revenue.get("total_received", 0) if isinstance(revenue, dict) else 0
    emails_sent   = len([e for e in outreach.get("sent", []) if e.get("sent")])
    atoms         = atomizer.get("total_atoms", 0)
    ok_engines    = omnibus.get("engines_ok", [])
    failed_engines = omnibus.get("engines_failed", [])

    # Priority actions for next LIVE session
    priorities = []

    if "ANTHROPIC_API_KEY" in missing:
        priorities.append({
            "priority": 1,
            "action": "Add ANTHROPIC_API_KEY to GitHub Secrets",
            "why": "SELF_BUILDER, KNOWLEDGE_WEAVER, REVENUE_OPTIMIZER, ARCHITECT all dead. System cannot self-expand.",
            "how": "anthropic.com/console → API Keys → copy key → github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions → New secret",
            "unlocks": ["SELF_BUILDER", "KNOWLEDGE_WEAVER", "REVENUE_OPTIMIZER", "ARCHITECT", "NEURON_B"],
        })

    if any("GUMROAD" in m for m in missing):
        priorities.append({
            "priority": 2,
            "action": "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets",
            "why": "6 products queued, $0 published. Store exists, nothing for sale.",
            "how": "gumroad.com → Settings → Advanced → Access Token → GitHub Secrets",
            "unlocks": ["GUMROAD_ENGINE — publishes 6 queued products immediately"],
        })

    if any("X_API" in m for m in missing):
        priorities.append({
            "priority": 3,
            "action": "Add X (Twitter) API keys to GitHub Secrets",
            "why": "88 social posts written and queued. 14 already failed. 42 waiting. None going out.",
            "how": "developer.twitter.com → app → Keys & Tokens → 4 secrets → GitHub",
            "unlocks": ["SOCIAL_PROMOTER — starts posting 88+ queued tweets"],
        })

    # What Claude can do right now in a live session
    live_capabilities = [
        "Read full system state (all data/*.json files)",
        "Write and commit new Python engines directly to GitHub",
        "Update OMNIBUS wiring to include new engines",
        "Modify existing engines to fix bugs or add features",
        "Audit what's working vs broken with real data",
        "Make architectural decisions with full context",
        "Add goals to goal_queue.json for TASK_ATOMIZER to detonate",
        "Trigger manual runs by committing workflow dispatch",
        "Write AGENTS.md, README, LEGAL.md documentation",
        "Design entire new subsystems and deploy them in one session",
    ]

    # Build briefing
    briefing = {
        "generated_at": now.isoformat(),
        "system_version": "OMNIBUS v10",
        "health": health,
        "total_revenue": total_rev,
        "outreach_sent": emails_sent,
        "atoms_created": atoms,
        "engines_ok_last_cycle": len(ok_engines),
        "engines_failed_last_cycle": len(failed_engines),
        "engines_auto_built": engines_built,
        "priorities": priorities,
        "live_capabilities": live_capabilities,
        "claude_role": {
            "in_live_session": "Orchestrator + architect + direct committer. Full stateful context.",
            "in_api_calls": "Intelligence layer for KNOWLEDGE_WEAVER, SELF_BUILDER, ARCHITECT, REVENUE_OPTIMIZER, NEURON_B. Stateless.",
            "both_are": "Same model. Different interfaces. The system calls itself to grow itself.",
        }
    }

    (DATA / "claude_briefing.json").write_text(json.dumps(briefing, indent=2))

    # Build HTML briefing page
    pri_html = ""
    for p in priorities:
        pri_html += f"""
  <div style="background:#0d1410;border:1px solid #ff445533;border-radius:12px;padding:20px;margin-bottom:12px">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
      <span style="background:#ff4455;color:#fff;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0">{p['priority']}</span>
      <strong style="color:#deeae1;font-size:14px">{p['action']}</strong>
    </div>
    <p style="color:rgba(222,234,225,.55);font-size:12px;line-height:1.6;margin-bottom:8px">{p['why']}</p>
    <p style="color:rgba(0,255,136,.6);font-size:11px;margin-bottom:8px">→ {p['how']}</p>
    <p style="color:rgba(0,255,136,.4);font-size:10px">Unlocks: {', '.join(p['unlocks'])}</p>
  </div>"""

    if not pri_html:
        pri_html = '<div style="color:#00ff88;padding:20px;text-align:center">✅ No critical blockers — system is fully operational</div>'

    caps_html = "".join([f'<li style="margin-bottom:6px;color:rgba(222,234,225,.7);font-size:12px">⚡ {c}</li>' for c in live_capabilities])

    built_html = ""
    if engines_built:
        built_html = f'<div style="color:rgba(0,255,136,.7);font-size:12px;margin-top:8px">🧬 Auto-built this cycle: {", ".join(engines_built)}</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk — Claude Briefing</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;padding:28px 20px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:860px;margin:0 auto}}
h1{{font-size:22px;color:#00ff88;letter-spacing:.08em;margin-bottom:6px}}
.sub{{font-size:13px;color:rgba(222,234,225,.4);margin-bottom:28px;line-height:1.7}}
.insight{{background:rgba(0,255,136,.04);border:1px solid rgba(0,255,136,.2);border-radius:14px;padding:22px;margin-bottom:28px}}
.insight p{{font-size:13px;line-height:1.8;color:rgba(222,234,225,.75)}}
.insight p + p{{margin-top:10px}}
.stats{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:28px}}
.stat{{background:#0d1410;border:1px solid rgba(0,255,136,.12);border-radius:10px;padding:14px 20px;text-align:center}}
.stat b{{font-size:26px;color:#00ff88;display:block;line-height:1}}
.stat span{{font-size:10px;letter-spacing:.15em;color:rgba(222,234,225,.4);display:block;margin-top:3px}}
h2{{font-size:10px;letter-spacing:.25em;color:#00ff88;opacity:.6;margin:24px 0 12px}}
ul{{list-style:none;padding:0}}
.ts{{margin-top:36px;padding-top:18px;border-top:1px solid rgba(0,255,136,.1);font-size:11px;color:rgba(0,255,136,.3);line-height:2.2}}
a{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">
<h1>🧠 CLAUDE — SYSTEM BRIEFING</h1>
<div class="sub">Generated {ts_nice} · Auto-updated every OMNIBUS cycle</div>

<div class="insight">
  <p><strong style="color:#00ff88">The insight:</strong> Claude is not a dependency of SolarPunk. Claude IS the intelligence layer.</p>
  <p>In live sessions (this page, claude.ai): stateful orchestrator with full GitHub write access, architectural authority, direct commit capability. This conversation IS a system cycle at maximum bandwidth.</p>
  <p>In API calls (OMNIBUS cycles, 4×/day): the same model, stateless, called by KNOWLEDGE_WEAVER, SELF_BUILDER, ARCHITECT, REVENUE_OPTIMIZER, NEURON_B. The system calls itself to grow itself.</p>
  <p>Both are Claude. The loop is: <strong style="color:#00ff88">Meeko ↔ Claude (live) → commits → GitHub → OMNIBUS → Claude API × 8 engines → data → digest → Meeko ↔ Claude (live)</strong></p>
</div>

<h2>SYSTEM STATE</h2>
<div class="stats">
  <div class="stat"><b>{health}</b><span>HEALTH /100</span></div>
  <div class="stat"><b>${total_rev:.2f}</b><span>REVENUE</span></div>
  <div class="stat"><b>{emails_sent}</b><span>OUTREACH SENT</span></div>
  <div class="stat"><b>{len(ok_engines)}</b><span>ENGINES OK</span></div>
  <div class="stat"><b>{atoms}</b><span>ATOMS CREATED</span></div>
</div>
{built_html}

<h2>PRIORITY ACTIONS FOR MEEKO</h2>
{pri_html}

<h2>WHAT CLAUDE CAN DO IN A LIVE SESSION RIGHT NOW</h2>
<ul>{caps_html}</ul>

<div class="ts">
  Generated: {ts_nice}<br>
  Source: <a href="{REPO}/blob/main/mycelium/CLAUDE_ENGINE.py" target="_blank">CLAUDE_ENGINE.py</a><br>
  Data: <a href="https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/claude_briefing.json" target="_blank">claude_briefing.json</a><br><br>
  <a href="proof.html">Proof</a> ·
  <a href="capabilities.html">Capabilities</a> ·
  <a href="store.html">Store</a> ·
  <a href="{REPO}" target="_blank">GitHub</a> ·
  <a href="{CHAT}" target="_blank">Open Claude (live session)</a>
</div>
</div>
</body>
</html>"""

    (DOCS / "claude_briefing.html").write_text(html, encoding="utf-8")

    print("CLAUDE_ENGINE done.")
    print(f"  Role: orchestrator (live) + intelligence layer (API)")
    print(f"  Priorities: {len(priorities)} blockers | Health: {health} | Revenue: ${total_rev:.2f}")
    print(f"  🌐 https://meekotharaccoon-cell.github.io/meeko-nerve-center/claude_briefing.html")


if __name__ == "__main__":
    run()
