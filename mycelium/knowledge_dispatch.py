#!/usr/bin/env python3
"""
knowledge_dispatch.py — SolarPunk's Long-Term Memory
======================================================
Reads ALL data files, ALL engine outputs, ALL run history.
Distills everything into consolidated_knowledge.json.
Surfaces patterns: what's working, what's not, what to build next.
Feeds NEURON_A with context so every run is smarter than the last.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
MYCELIUM = Path("mycelium")
KB_FILE  = DATA_DIR / "consolidated_knowledge.json"

def load_all_data():
    corpus = {}
    for f in DATA_DIR.glob("*.json"):
        try: corpus[f.stem] = json.loads(f.read_text())
        except: corpus[f.stem] = {"_read_error": True}
    return corpus

def analyze_engines():
    engines = list(MYCELIUM.glob("*.py"))
    engine_info = []
    for e in engines:
        try:
            code = e.read_text()
            lines = code.split("\n")
            desc = ""
            for i, l in enumerate(lines):
                if '"""' in l and i < 10:
                    for j in range(i+1, min(i+4, len(lines))):
                        if lines[j].strip() and '"""' not in lines[j]:
                            desc = lines[j].strip(); break
                    break
            engine_info.append({
                "name": e.name, "size": e.stat().st_size, "desc": desc,
                "has_main": "def main(" in code, "uses_api": "ANTHROPIC_API_KEY" in code,
                "saves_data": "DATA_DIR" in code or "data/" in code,
            })
        except: pass
    return engine_info

def extract_insights(corpus, api_key):
    if not api_key:
        return {
            "patterns": ["System building phase — 18 engines, 0 revenue yet",
                         "All core engines present and running"],
            "next_build": ["EMAIL_HARVESTER - captures buyer emails for newsletter",
                           "NEWSLETTER_ENGINE - weekly Gaza Rose updates to subscribers",
                           "PRICE_OPTIMIZER - A/B tests art prices for max loop velocity"],
            "health": "BUILDING",
            "advice": "Get first sale. Share Gaza Rose shop link. Loop starts with 1 dollar.",
        }
    try:
        summary = {
            "engines": [e["name"] for e in analyze_engines()],
            "revenue": corpus.get("flywheel_state", {}).get("current_balance", 0),
            "gaza_total": corpus.get("loop_fund", {}).get("total_to_gaza", 0),
            "health_score": corpus.get("brain_state", {}).get("health_score", 0),
            "cycles": corpus.get("flywheel_state", {}).get("cycles", 0),
        }
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 600,
                  "messages": [{"role": "user", "content": f"""You are SolarPunk — autonomous AI on GitHub Actions. Income for Meeko, 70% to Gaza Rose Gallery.

State: {json.dumps(summary)}

Respond ONLY with JSON:
{{"patterns":["2-3 key patterns"],"next_build":["3 specific engines to build"],"health":"HEALTHY|BUILDING|BROKEN","advice":"one sentence action"}}"""}]}, timeout=30)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s = text.find("{"); e = text.rfind("}") + 1
        return json.loads(text[s:e]) if s >= 0 else {}
    except Exception as ex:
        print(f"  Insights error: {ex}")
        return {"patterns": [], "next_build": [], "health": "UNKNOWN", "advice": "Check API key"}

def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("📚 KNOWLEDGE_DISPATCH — SolarPunk Memory")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    corpus  = load_all_data()
    engines = analyze_engines()
    print(f"  Data files: {len(corpus)} | Engines: {len(engines)}")
    insights = extract_insights(corpus, api_key)
    seed = {
        "timestamp": datetime.now().isoformat(),
        "health": insights.get("health", "BUILDING"),
        "advice": insights.get("advice", ""),
        "patterns": insights.get("patterns", []),
        "engines_to_build": insights.get("next_build", []),
        "existing_engines": [e["name"] for e in engines],
        "loop_active": True,
    }
    (DATA_DIR / "omnibrain_seed.json").write_text(json.dumps(seed, indent=2))
    kb = {
        "generated": datetime.now().isoformat(),
        "engine_count": len(engines),
        "engines": engines,
        "data_keys": list(corpus.keys()),
        "insights": insights,
        "seed": seed,
        "knowledge_db": {"tables": [], "data": {}},
        "mycelium_kb": {e["name"]: e["desc"] for e in engines},
        "autonomous_scripts": [e["name"] for e in engines if e.get("has_main")],
        "gumroad_listings_chars": [],
        "connections_discovered": [],
    }
    KB_FILE.write_text(json.dumps(kb, indent=2))
    print(f"  Health: {insights.get('health','?')} | {insights.get('advice','')[:60]}")
    return kb

if __name__ == "__main__":
    main()
