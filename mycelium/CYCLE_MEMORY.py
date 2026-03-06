#!/usr/bin/env python3
"""
CYCLE_MEMORY.py — Cross-cycle learning layer
=============================================
The system was blind. Every cycle it ran the same engines, hit the
same failures, printed the same fix suggestions, and forgot everything.

This engine gives the system a memory that doesn't require an API key.

What it tracks:
  - Engine status deltas (failed -> ok = WIN, ok -> failed = REGRESSION)
  - Persistent blockers (same bottleneck N cycles = escalate)
  - Revenue deltas (did anything actually change?)
  - Health score trajectory (improving, stuck, declining?)
  - What actually improved since last cycle
  - What has been broken for 5+ cycles without fix

What it writes:
  - data/cycle_delta.json   — structured delta for other engines to read
  - data/cycle_ledger.json  — full history, last 50 cycles
  - docs/memory.html        — visual timeline of system learning

Why it matters:
  Without this, BOTTLENECK_SCANNER prints the same fix 100 times.
  With this, it can say: "BN-001 has been open 23 cycles. Escalating."
  Without this, HEALTH_BOOSTER doesn't know if suggestions are working.
  With this, it knows: "health went 40->40->40 for 12 cycles. Pattern: stuck."

Built because the system kept running in circles.
The first step out of a loop is noticing you're in one.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

LEDGER_FILE = DATA / "cycle_ledger.json"
DELTA_FILE  = DATA / "cycle_delta.json"
MAX_HISTORY = 50


# ── helpers ──────────────────────────────────────────────────────────────────

def rj(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            return d if isinstance(d, (dict, list)) else (fallback or {})
        except: pass
    return fallback if fallback is not None else {}

def load_ledger():
    if LEDGER_FILE.exists():
        try: return json.loads(LEDGER_FILE.read_text())
        except: pass
    return []

def save_ledger(ledger):
    LEDGER_FILE.write_text(json.dumps(ledger[-MAX_HISTORY:], indent=2))


# ── snapshot current state ────────────────────────────────────────────────────

def snapshot():
    omnibus   = rj("omnibus_last.json")
    revenue   = rj("revenue_inbox.json")
    resonance = rj("resonance_state.json")
    bottleneck= rj("bottleneck_report.json")
    brain     = rj("brain_state.json")

    engines_ok     = set(omnibus.get("engines_ok",     []))
    engines_failed = set(omnibus.get("engines_failed",  []))
    engines_skipped= set(omnibus.get("engines_skipped", []))

    total_rev = revenue.get("total_received", 0) if isinstance(revenue, dict) else 0
    gaza_rev  = revenue.get("total_to_gaza",  0) if isinstance(revenue, dict) else 0

    bottlenecks_now = []
    for bn in bottleneck.get("bottlenecks", []):
        bottlenecks_now.append({
            "id":       bn.get("id", "?"),
            "title":    bn.get("title", ""),
            "severity": bn.get("severity", ""),
        })

    return {
        "ts":               datetime.now(timezone.utc).isoformat(),
        "run_id":           omnibus.get("run_id", "unknown"),
        "health":           brain.get("health_score", omnibus.get("health_after", 0)),
        "engines_ok":       sorted(engines_ok),
        "engines_failed":   sorted(engines_failed),
        "engines_skipped":  sorted(engines_skipped),
        "total_revenue":    total_rev,
        "gaza_revenue":     gaza_rev,
        "resonance_score":  resonance.get("resonance_score", 0),
        "resonance_label":  resonance.get("resonance_label", "SILENT"),
        "github_stars":     resonance.get("github", {}).get("stars", 0),
        "bottlenecks":      bottlenecks_now,
        "engine_count_ok":  len(engines_ok),
        "engine_count_fail":len(engines_failed),
    }


# ── compute delta vs previous cycle ──────────────────────────────────────────

def compute_delta(current, previous):
    if not previous:
        return {
            "first_cycle":    True,
            "wins":           [],
            "regressions":    [],
            "revenue_delta":  0,
            "health_delta":   0,
            "stars_delta":    0,
            "resonance_delta":0,
            "new_failures":   [],
            "fixed_engines":  [],
        }

    prev_ok     = set(previous.get("engines_ok",     []))
    prev_failed = set(previous.get("engines_failed", []))
    curr_ok     = set(current.get("engines_ok",      []))
    curr_failed = set(current.get("engines_failed",  []))

    fixed      = sorted(prev_failed & curr_ok)       # was failing, now ok
    regressed  = sorted(prev_ok & curr_failed)        # was ok, now failing
    new_fail   = sorted(curr_failed - prev_failed)    # newly broken this cycle
    still_fail = sorted(curr_failed & prev_failed)    # still broken

    return {
        "first_cycle":     False,
        "wins":            fixed,
        "regressions":     regressed,
        "new_failures":    new_fail,
        "still_failing":   still_fail,
        "revenue_delta":   round(current["total_revenue"] - previous.get("total_revenue", 0), 2),
        "health_delta":    current["health"] - previous.get("health", 0),
        "stars_delta":     current["github_stars"] - previous.get("github_stars", 0),
        "resonance_delta": current["resonance_score"] - previous.get("resonance_score", 0),
    }


# ── detect persistent blockers ───────────────────────────────────────────────

def detect_persistent(ledger, current_bottlenecks):
    """
    A bottleneck is "persistent" if it appeared in the last N cycles.
    Escalation threshold: 5 cycles = urgent, 10 = critical, 20 = stuck.
    """
    if len(ledger) < 2:
        return []

    # Count how many recent cycles each bottleneck appeared
    bn_counts = {}
    for entry in ledger[-20:]:
        for bn in entry.get("bottlenecks", []):
            bid = bn.get("id", bn.get("title", "?"))
            bn_counts[bid] = bn_counts.get(bid, 0) + 1

    persistent = []
    for bn in current_bottlenecks:
        bid   = bn.get("id", bn.get("title", "?"))
        count = bn_counts.get(bid, 1)
        if count >= 5:
            level = "STUCK" if count >= 20 else ("CRITICAL" if count >= 10 else "URGENT")
            persistent.append({
                "id":       bid,
                "title":    bn.get("title", ""),
                "severity": bn.get("severity", ""),
                "cycles_open": count,
                "escalation":  level,
            })

    return persistent


# ── detect health trajectory ──────────────────────────────────────────────────

def health_trajectory(ledger):
    """
    Returns: improving / stuck / declining / recovering / unknown
    Looks at last 5 health scores.
    """
    scores = [e.get("health", 0) for e in ledger[-5:]]
    if len(scores) < 2:
        return "unknown"
    deltas = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
    avg = sum(deltas) / len(deltas) if deltas else 0
    if avg > 2:   return "improving"
    if avg < -2:  return "declining"
    if avg > 0.5: return "recovering"
    return "stuck"


# ── build HTML dashboard ──────────────────────────────────────────────────────

def build_html(current, delta, ledger, persistent):
    now        = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    traj       = health_trajectory(ledger)
    traj_color = {"improving": "#00ff88", "recovering": "#88ffcc",
                  "stuck": "#ff9800", "declining": "#ff5e5b"}.get(traj, "#aaa")
    cycles     = len(ledger)

    # History sparkline data (health scores)
    health_hist = [e.get("health", 0) for e in ledger[-30:]]
    rev_hist    = [e.get("total_revenue", 0) for e in ledger[-30:]]
    spark_pts   = " ".join(f"{i*10},{100 - h}" for i, h in enumerate(health_hist))

    def badge(text, color):
        return (f'<span style="background:{color}20;border:1px solid {color}40;'
                f'color:{color};padding:2px 8px;border-radius:4px;font-size:10px;'
                f'letter-spacing:.1em">{text}</span>')

    # Win/regression rows
    wins_html = "".join(
        f'<div style="color:#00ff88;font-size:12px;padding:3px 0">✓ {e} fixed this cycle</div>'
        for e in delta.get("wins", [])
    ) or '<div style="color:rgba(255,255,255,.2);font-size:11px">No new fixes this cycle</div>'

    regressions_html = "".join(
        f'<div style="color:#ff5e5b;font-size:12px;padding:3px 0">✗ {e} broke this cycle</div>'
        for e in delta.get("regressions", [])
    ) or ""

    # Persistent blockers
    persist_html = ""
    for p in persistent:
        ecol = {"STUCK": "#ff5e5b", "CRITICAL": "#ff9800", "URGENT": "#ffd700"}.get(p["escalation"], "#aaa")
        persist_html += (
            f'<div style="border-left:3px solid {ecol};padding:8px 12px;margin-bottom:8px;'
            f'background:rgba(255,255,255,.02);border-radius:0 6px 6px 0">'
            f'<div style="font-size:11px;color:{ecol};letter-spacing:.1em">{p["escalation"]} — {p["cycles_open"]} CYCLES OPEN</div>'
            f'<div style="font-size:12px;color:#dde;margin-top:3px">{p["title"]}</div>'
            f'</div>'
        )
    if not persist_html:
        persist_html = '<div style="color:rgba(255,255,255,.2);font-size:11px">No persistent blockers detected</div>'

    # Recent cycle log
    cycle_rows = ""
    for entry in reversed(ledger[-10:]):
        d   = entry.get("ts", "")[:10]
        h   = entry.get("health", 0)
        r   = entry.get("total_revenue", 0)
        ok  = entry.get("engine_count_ok", 0)
        fail= entry.get("engine_count_fail", 0)
        rs  = entry.get("resonance_score", 0)
        rl  = entry.get("resonance_label", "SILENT")
        hcol = "#00ff88" if h > 60 else ("#ff9800" if h > 35 else "#ff5e5b")
        cycle_rows += (
            f'<tr style="border-bottom:1px solid rgba(255,255,255,.04)">'
            f'<td style="padding:6px 8px;font-size:11px;color:rgba(255,255,255,.4)">{d}</td>'
            f'<td style="padding:6px 8px;font-size:12px;color:{hcol};font-weight:700">{h}</td>'
            f'<td style="padding:6px 8px;font-size:12px;color:#00ff88">{ok}</td>'
            f'<td style="padding:6px 8px;font-size:12px;color:#ff5e5b">{fail}</td>'
            f'<td style="padding:6px 8px;font-size:12px;color:#dde">${r:.2f}</td>'
            f'<td style="padding:6px 8px;font-size:11px;color:rgba(255,255,255,.4)">{rs} ({rl})</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>SolarPunk — Cycle Memory</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;padding:28px 20px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:900px;margin:0 auto}}
h1{{font-size:20px;color:#00ff88;letter-spacing:.06em;margin-bottom:4px}}
.sub{{font-size:11px;color:rgba(222,234,225,.3);margin-bottom:28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:28px}}
.card{{background:#0d1410;border:1px solid rgba(0,255,136,.12);border-radius:10px;padding:16px;text-align:center}}
.card .val{{font-size:26px;font-weight:700;display:block;margin-bottom:4px}}
.card .lbl{{font-size:10px;color:rgba(222,234,225,.35);letter-spacing:.15em}}
h2{{font-size:10px;letter-spacing:.25em;color:rgba(0,255,136,.45);margin:24px 0 10px}}
.panel{{background:#0d1410;border:1px solid rgba(0,255,136,.1);border-radius:10px;padding:16px;margin-bottom:16px}}
.spark{{width:100%;height:60px;margin:8px 0}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-size:10px;letter-spacing:.12em;color:rgba(222,234,225,.3);padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.06)}}
.ts{{margin-top:36px;padding-top:14px;border-top:1px solid rgba(0,255,136,.08);font-size:11px;color:rgba(0,255,136,.25);line-height:2.2}}
a{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">
<h1>🧠 CYCLE MEMORY</h1>
<div class="sub">{now} · {cycles} cycles recorded · auto-refreshes every 5 min</div>

<div class="grid">
  <div class="card"><span class="val" style="color:{traj_color}">{traj.upper()}</span><span class="lbl">HEALTH TREND</span></div>
  <div class="card"><span class="val" style="color:#00ff88">{current['health']}</span><span class="lbl">HEALTH SCORE</span></div>
  <div class="card"><span class="val" style="color:#00ff88">{current['engine_count_ok']}</span><span class="lbl">ENGINES OK</span></div>
  <div class="card"><span class="val" style="color:#ff5e5b">{current['engine_count_fail']}</span><span class="lbl">ENGINES FAILING</span></div>
  <div class="card"><span class="val" style="color:#ffd166">${current['total_revenue']:.2f}</span><span class="lbl">TOTAL REVENUE</span></div>
  <div class="card"><span class="val" style="color:#00ff88">{current['resonance_score']}</span><span class="lbl">RESONANCE</span></div>
</div>

<h2>HEALTH TRAJECTORY — LAST {len(health_hist)} CYCLES</h2>
<div class="panel">
  <svg class="spark" viewBox="0 0 {max(len(health_hist)*10,10)} 100" preserveAspectRatio="none">
    <polyline points="{spark_pts}" fill="none" stroke="#00ff88" stroke-width="1.5" opacity="0.7"/>
  </svg>
  <div style="font-size:11px;color:rgba(222,234,225,.35)">
    Low: {min(health_hist) if health_hist else 0} · High: {max(health_hist) if health_hist else 0} · Current: {current['health']}
    · Trend: <span style="color:{traj_color}">{traj}</span>
  </div>
</div>

<h2>THIS CYCLE — DELTA</h2>
<div class="panel">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    <div>
      <div style="font-size:10px;letter-spacing:.15em;color:rgba(0,255,136,.4);margin-bottom:8px">FIXES</div>
      {wins_html}
      {regressions_html}
    </div>
    <div>
      <div style="font-size:10px;letter-spacing:.15em;color:rgba(0,255,136,.4);margin-bottom:8px">DELTAS</div>
      <div style="font-size:12px;line-height:2;color:rgba(222,234,225,.6)">
        Revenue: <span style="color:{'#00ff88' if delta.get('revenue_delta',0) > 0 else '#ff5e5b' if delta.get('revenue_delta',0) < 0 else '#aaa'}">{'+' if delta.get('revenue_delta',0) > 0 else ''}{delta.get('revenue_delta',0):.2f}</span><br>
        Health: <span style="color:{'#00ff88' if delta.get('health_delta',0) > 0 else '#ff5e5b' if delta.get('health_delta',0) < 0 else '#aaa'}">{'+' if delta.get('health_delta',0) > 0 else ''}{delta.get('health_delta',0)}</span><br>
        Stars: <span style="color:{'#00ff88' if delta.get('stars_delta',0) > 0 else '#aaa'}">{'+' if delta.get('stars_delta',0) > 0 else ''}{delta.get('stars_delta',0)}</span><br>
        Resonance: <span style="color:{'#00ff88' if delta.get('resonance_delta',0) > 0 else '#aaa'}">{'+' if delta.get('resonance_delta',0) > 0 else ''}{delta.get('resonance_delta',0)}</span>
      </div>
    </div>
  </div>
</div>

<h2>PERSISTENT BLOCKERS — ESCALATION TRACKING</h2>
<div class="panel">
  {persist_html}
  <div style="font-size:10px;color:rgba(222,234,225,.2);margin-top:10px">
    Escalation: URGENT=5+ cycles · CRITICAL=10+ cycles · STUCK=20+ cycles
  </div>
</div>

<h2>CYCLE HISTORY — LAST 10 RUNS</h2>
<div class="panel" style="overflow-x:auto">
  <table>
    <thead><tr>
      <th>DATE</th><th>HEALTH</th><th>OK</th><th>FAIL</th><th>REVENUE</th><th>RESONANCE</th>
    </tr></thead>
    <tbody>{cycle_rows}</tbody>
  </table>
</div>

<div class="ts">
  Source: <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/mycelium/CYCLE_MEMORY.py" target="_blank">CYCLE_MEMORY.py</a><br>
  Data: <a href="https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/cycle_ledger.json" target="_blank">cycle_ledger.json</a> · {cycles} entries<br><br>
  <a href="proof.html">Proof</a> · <a href="store.html">Store</a> · <a href="resonance.html">Resonance</a> · <a href="quick_revenue.html">Revenue</a> · <a href="bottleneck.html">Bottlenecks</a>
</div>
</div>
</body>
</html>"""


# ── main ──────────────────────────────────────────────────────────────────────

def run():
    ledger  = load_ledger()
    current = snapshot()
    prev    = ledger[-1] if ledger else None

    delta      = compute_delta(current, prev)
    persistent = detect_persistent(ledger, current.get("bottlenecks", []))
    traj       = health_trajectory(ledger)

    # Append current to ledger
    ledger.append(current)
    save_ledger(ledger)

    # Write cycle delta for other engines
    cycle_delta = {
        "generated":       current["ts"],
        "cycle_number":    len(ledger),
        "health":          current["health"],
        "health_trend":    traj,
        "delta":           delta,
        "persistent":      persistent,
        "still_failing":   delta.get("still_failing", []),
        "new_fixes":       delta.get("wins", []),
        "new_regressions": delta.get("regressions", []),
        "revenue":         current["total_revenue"],
        "revenue_delta":   delta.get("revenue_delta", 0),
        "resonance":       current["resonance_score"],
        "summary": (
            f"Cycle {len(ledger)} | Health: {current['health']} ({traj}) | "
            f"Fixed: {len(delta.get('wins',[]))} | Regressed: {len(delta.get('regressions',[]))} | "
            f"Persistent blockers: {len(persistent)} | Revenue: ${current['total_revenue']:.2f}"
        )
    }
    DELTA_FILE.write_text(json.dumps(cycle_delta, indent=2))

    # Build HTML
    html = build_html(current, delta, ledger, persistent)
    (DOCS / "memory.html").write_text(html, encoding="utf-8")

    # Print summary
    print(f"CYCLE_MEMORY — cycle {len(ledger)}")
    print(f"  Health: {current['health']} ({traj})")
    if delta.get("wins"):
        print(f"  FIXED this cycle: {', '.join(delta['wins'])}")
    if delta.get("regressions"):
        print(f"  BROKE this cycle: {', '.join(delta['regressions'])}")
    if delta.get("still_failing"):
        print(f"  Still failing ({len(delta['still_failing'])}): {', '.join(delta['still_failing'])}")
    if persistent:
        print(f"  Persistent blockers ({len(persistent)}):")
        for p in persistent:
            print(f"    [{p['escalation']}] {p['title']} — {p['cycles_open']} cycles")
    if delta.get("revenue_delta", 0) > 0:
        print(f"  REVENUE UP: +${delta['revenue_delta']:.2f}")
    print(f"  Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center/memory.html")
    print("CYCLE_MEMORY done.")


if __name__ == "__main__":
    run()
