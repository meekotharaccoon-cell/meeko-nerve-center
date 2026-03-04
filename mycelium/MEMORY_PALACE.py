#!/usr/bin/env python3
"""
MEMORY_PALACE — Persistent Learning Engine
SolarPunk remembers every cycle. Learns what works. Forgets nothing.

Reads all data/ JSON files each cycle, distills:
  - What worked (revenue events, loops triggered)
  - What failed (errors, missed opportunities)
  - Growth trajectory (health score over time)
  - Pattern recognition (when things improve, why)

Writes: data/memory_palace.json  (ever-growing knowledge base, 365 cycles)
        data/lessons.json         (actionable lessons, top 20)
        data/growth_curve.json    (sparkline data for dashboard)
"""
import json
from pathlib import Path
from datetime import datetime, timezone

MEMORY_F  = Path("data/memory_palace.json")
LESSONS_F = Path("data/lessons.json")
GROWTH_F  = Path("data/growth_curve.json")

def load_memory():
    if MEMORY_F.exists():
        try:
            return json.loads(MEMORY_F.read_text())
        except:
            pass
    return {"cycles": [], "patterns": {}, "total_cycles": 0,
            "created": datetime.now(timezone.utc).isoformat()}

def snapshot_current_state():
    snap = {"timestamp": datetime.now(timezone.utc).isoformat()}
    reads = {
        "brain": "data/brain_state.json",
        "flywheel": "data/flywheel_state.json",
        "neuron_a": "data/neuron_a_report.json",
        "art_log": "data/art_log.json",
        "harvest": "data/content_harvest.json",
    }
    for key, path in reads.items():
        fp = Path(path)
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text())
            if key == "brain":
                snap["health_score"] = data.get("health_score", 0)
                snap["revenue"] = data.get("stats", {}).get("revenue", 0)
                snap["engines"] = data.get("stats", {}).get("engines_total", 0)
                snap["synth_built"] = data.get("stats", {}).get("synth_built", 0)
            elif key == "flywheel":
                snap["loop_balance"] = data.get("loop_balance", 0)
                snap["total_sales"] = data.get("total_sales", 0)
                snap["loop_cycles_count"] = data.get("loop_cycles", 0)
            elif key == "neuron_a":
                opps = data.get("opportunities", [])
                snap["top_opportunity"] = opps[0].get("name", "") if opps else ""
            elif key == "art_log":
                snap["art_pieces_made"] = len(data.get("pieces", []))
            elif key == "harvest":
                snap["trending_themes"] = [t["word"] for t in data.get("trending_themes", [])[:3]]
        except:
            pass
    return snap

def detect_patterns(cycles):
    if len(cycles) < 3:
        return {}
    patterns = {}
    scores = [c.get("health_score", 0) for c in cycles[-10:] if "health_score" in c]
    if len(scores) >= 2:
        delta = scores[-1] - scores[0]
        patterns["health_trend"] = "improving" if delta > 5 else ("declining" if delta < -5 else "stable")
        patterns["health_velocity"] = round(scores[-1] - scores[-2], 1)
    revenues = [c.get("revenue", 0) for c in cycles if "revenue" in c]
    if revenues:
        patterns["max_revenue"] = max(revenues)
        patterns["revenue_events"] = sum(1 for r in revenues if r > 0)
    loop_counts = [c.get("loop_cycles_count", 0) for c in cycles if "loop_cycles_count" in c]
    if loop_counts:
        patterns["total_loops_triggered"] = max(loop_counts)
    return patterns

def extract_lessons(cycles, patterns):
    lessons = []
    trend = patterns.get("health_trend", "")
    if trend == "improving":
        lessons.append({"lesson": "Health is rising — keep doing what we're doing",
            "priority": "low", "type": "positive"})
    elif trend == "declining":
        lessons.append({"lesson": "Health declining — check ANTHROPIC_API_KEY is set in GitHub Secrets",
            "priority": "critical", "type": "action",
            "action": "Settings -> Secrets -> ANTHROPIC_API_KEY"})
    if patterns.get("revenue_events", 0) == 0:
        lessons.append({"lesson": "Zero revenue yet — enable GitHub Pages to go live",
            "priority": "high", "type": "action",
            "action": "Settings -> Pages -> main branch -> /docs"})
    if cycles:
        ec = cycles[-1].get("engines", 0)
        if ec < 12:
            lessons.append({"lesson": f"Only {ec} engines — SYNTHESIS_FACTORY should build more",
                "priority": "medium", "type": "growth"})
    for c in cycles[-3:]:
        if c.get("health_score", 100) < 50:
            lessons.append({"lesson": "Sub-50 health — API key 401. Check ANTHROPIC_API_KEY.",
                "priority": "critical", "type": "action"})
            break
    return lessons[:20]

def build_growth_curve(cycles):
    return [{"ts": c.get("timestamp", "")[:10], "health": c.get("health_score", 0),
             "revenue": round(c.get("revenue", 0), 2), "engines": c.get("engines", 0),
             "loops": c.get("loop_cycles_count", 0)} for c in cycles[-30:]]

def main():
    print("MEMORY_PALACE awakening...")
    mem = load_memory()
    snap = snapshot_current_state()
    cycles = mem.get("cycles", [])
    today = snap["timestamp"][:10]
    cycles = [c for c in cycles if c.get("timestamp", "")[:10] != today]
    cycles.append(snap)
    cycles = cycles[-365:]
    patterns = detect_patterns(cycles)
    lessons = extract_lessons(cycles, patterns)
    curve = build_growth_curve(cycles)
    mem.update({"cycles": cycles, "patterns": patterns, "total_cycles": len(cycles),
                "last_updated": snap["timestamp"], "latest_snap": snap})
    MEMORY_F.write_text(json.dumps(mem, indent=2))
    LESSONS_F.write_text(json.dumps(lessons, indent=2))
    GROWTH_F.write_text(json.dumps(curve, indent=2))
    print(f"Memory: {len(cycles)} cycles | Health: {snap.get('health_score','?')} | Revenue: ${snap.get('revenue',0):.2f}")
    print(f"Pattern: {patterns.get('health_trend','unknown')}")
    crit = [l for l in lessons if l.get("priority") == "critical"]
    if crit:
        print(f"CRITICAL: {crit[0]['lesson']}")

if __name__ == "__main__":
    main()
