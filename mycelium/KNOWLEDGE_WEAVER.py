#!/usr/bin/env python3
"""
KNOWLEDGE_WEAVER.py — Claude-powered autonomous engine builder
================================================================
Every cycle: reads all data + engine list, asks Claude what's missing,
writes the highest-value new engine directly to mycelium/.
System literally grows itself. No human input needed after deploy.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from AI_CLIENT import ask, ask_json, ai_available

DATA     = Path("data");     DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
DOCS     = Path("docs");     DOCS.mkdir(exist_ok=True)
STATE    = DATA / "knowledge_weaver_state.json"

BLOCKED_CODE = ["os.system(", "subprocess", "eval(", "exec(",
                ".github/workflows", "git push", "rm -rf", "shutil.rmtree"]


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"engines_built": [], "cycles": 0, "last_run": None, "history": []}


def list_engines():
    return sorted(f.stem for f in MYCELIUM.glob("*.py")
                  if not f.stem.startswith("__") and f.stem == f.stem.upper())


def read_snapshot():
    """Compact summary of all key data files."""
    snap = {}
    for fname in [
        "brain_state.json", "omnibus_last.json", "knowledge_gaps.json",
        "free_api_state.json", "bottleneck_report.json", "flywheel_summary.json",
        "revenue_loop_last.json", "architect_plan.json", "self_builder_state.json",
        "business_factory_state.json", "secrets_checker_state.json",
        "curated_repos.json",
    ]:
        f = DATA / fname
        if f.exists():
            try:
                snap[fname] = f.read_text()[:600]
            except Exception:
                pass
    return snap


def pick_next_engine(state, engines, snap, opps):
    already = state.get("engines_built", [])
    prompt = f"""You are SolarPunk's KNOWLEDGE_WEAVER — autonomous AI revenue system.

EXISTING ENGINES ({len(engines)}): {', '.join(engines)}
ALREADY BUILT: {already}

SYSTEM SNAPSHOT:
{json.dumps(snap, default=str)[:2500]}

FREE API OPPORTUNITIES:
{chr(10).join(opps[:8]) if opps else 'none yet'}

Identify the SINGLE highest-value engine to build that:
1. Does NOT exist in the engine list above
2. Uses ONLY stdlib + requests + AI_CLIENT imports
3. Directly generates or amplifies revenue with zero human input
4. Fills a real gap visible in the snapshot data

Respond with JSON:
{{
  "engine_name": "UPPERCASE_NAME",
  "reason": "one line why highest value",
  "revenue_mechanism": "exactly how it earns/saves money",
  "estimated_monthly_usd": 0
}}"""
    return ask_json(prompt, max_tokens=400)


def generate_code(spec):
    prompt = f"""Write a complete, functional Python engine for SolarPunk autonomous revenue system.

ENGINE: {spec['engine_name']}
PURPOSE: {spec['reason']}
REVENUE: {spec['revenue_mechanism']}

RULES:
- Imports: only stdlib + requests + (from AI_CLIENT import ask, ask_json, ask_json_list)
- Available env vars: ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, HF_TOKEN, GITHUB_TOKEN
- Must have: run() function + if __name__=="__main__": run()
- Saves state to: data/{spec['engine_name'].lower()}_state.json
- Never crashes — wrap everything in try/except
- Under 180 lines
- Actually functional, not placeholder stubs

Format your response EXACTLY as:
FILENAME: {spec['engine_name']}.py
---
<complete python code here>
---"""
    return ask([{"role": "user", "content": prompt}], max_tokens=3500)


def parse_code(text):
    lines = text.split("\n")
    in_code, dashes = False, 0
    code_lines = []
    for line in lines:
        if line.strip() == "---":
            dashes += 1
            in_code = (dashes == 1)
        elif in_code:
            code_lines.append(line)
    return "\n".join(code_lines)


def safety_check(code):
    for bad in BLOCKED_CODE:
        if bad in code:
            return False, bad
    return True, None


def build_page(state, spec, built):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    history = state.get("history", [])
    rows = "".join(
        f"<tr><td>{h['name']}</td><td>{h['reason'][:60]}</td><td>{h['ts'][:10]}</td></tr>"
        for h in history[-20:]
    )
    spec_str = json.dumps(spec, indent=2) if spec else "none"
    html = f"""<!DOCTYPE html><html><head><title>Knowledge Weaver</title>
<meta charset=utf-8>
<style>body{{font-family:monospace;background:#0a0a0a;color:#0f0;padding:20px}}
h1,h2{{color:#0f0}}pre{{background:#111;padding:10px;overflow-x:auto;white-space:pre-wrap}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:6px;border:1px solid #333}}</style>
</head><body>
<h1>🧬 KNOWLEDGE WEAVER — {ts}</h1>
<p>Cycles: {state['cycles']} | Engines auto-built: {len(state['engines_built'])}</p>
<p>This cycle: {'✅ ' + built if built else '⏭ none (engine exists or AI unavailable)'}</p>
<h2>This Cycle Spec</h2><pre>{spec_str}</pre>
<h2>Auto-Built Engine History</h2>
<table><tr><th>Engine</th><th>Reason</th><th>Date</th></tr>{rows}</table>
</body></html>"""
    (DOCS / "weaver.html").write_text(html)


def run():
    print("KNOWLEDGE_WEAVER — synthesizing + auto-building...")
    if not ai_available():
        print("  No AI — skipping")
        return

    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    engines = list_engines()
    snap    = read_snapshot()

    opps = []
    try:
        fs = json.loads((DATA / "free_api_state.json").read_text())
        opps = fs.get("opportunities", [])
    except Exception:
        pass

    spec  = pick_next_engine(state, engines, snap, opps)
    built = None

    if spec and spec.get("engine_name"):
        name   = spec["engine_name"].upper().replace(" ", "_").replace("-", "_")
        target = MYCELIUM / f"{name}.py"

        if target.exists():
            print(f"  {name} already exists — skipping")
        else:
            print(f"  Building: {name} — {spec.get('reason','')[:70]}")
            raw  = generate_code(spec)
            code = parse_code(raw).strip()

            if not code:
                print("  ⚠️  Empty code returned")
            else:
                safe, bad = safety_check(code)
                if not safe:
                    print(f"  ⛔ Safety block: '{bad}' in generated code")
                else:
                    try:
                        compile(code, name, "exec")
                        target.write_text(code)
                        built = name
                        state.setdefault("engines_built", []).append(name)
                        state.setdefault("history", []).append({
                            "name": name,
                            "reason": spec.get("reason", ""),
                            "revenue": spec.get("revenue_mechanism", ""),
                            "ts": datetime.now(timezone.utc).isoformat(),
                        })
                        print(f"  ✅ Built: {name} ({len(code.splitlines())} lines)")
                    except SyntaxError as e:
                        print(f"  ❌ Syntax error in {name}: {e}")
    else:
        print("  No new engine spec returned by Claude")

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    build_page(state, spec, built)
    STATE.write_text(json.dumps(state, indent=2))
    print(f"  Total auto-built: {len(state['engines_built'])} | Cycles: {state['cycles']}")
    print("KNOWLEDGE_WEAVER done")


if __name__ == "__main__":
    run()
