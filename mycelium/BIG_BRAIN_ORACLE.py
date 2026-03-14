# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BIG_BRAIN_ORACLE.py — Asks Claude the biggest strategic questions about the system.

Every cycle asks 3 high-leverage strategic questions:
  1. What is the single highest-leverage action right now?
  2. What structural gap is silently killing revenue?
  3. What engine should be built that doesn't exist yet?

Then:
  - Stores answers in data/oracle_insights.json
  - Seeds data/omnibrain_seed.json with top actions
  - Generates ENGINE_IDEAS for SELF_BUILDER to build

Secrets: ANTHROPIC_API_KEY
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"


def get_system_context():
    engines = sorted([f.name for f in MYCELIUM.glob("*.py") if not f.name.startswith("__")])
    data_files = sorted([f.name for f in DATA.glob("*.json")])
    revenue = 0.0
    rf = DATA / "revenue_inbox.json"
    if rf.exists():
        try: revenue = json.loads(rf.read_text()).get("total_received", 0)
        except: pass
    health = 40
    bf = DATA / "brain_state.json"
    if bf.exists():
        try: health = json.loads(bf.read_text()).get("health_score", 40)
        except: pass
    loops = 0
    if bf.exists():
        try: loops = json.loads(bf.read_text()).get("total_loops_completed", 0)
        except: pass
    legal = {}
    lf = DATA / "brand_legal_state.json"
    if lf.exists():
        try: legal = json.loads(lf.read_text())
        except: pass
    gumroad = {}
    gf = DATA / "gumroad_engine_state.json"
    if gf.exists():
        try: gumroad = json.loads(gf.read_text())
        except: pass
    return {
        "engines": engines, "data_files": data_files,
        "total_revenue_usd": revenue, "brain_health": health,
        "loops_completed": loops,
        "brand_days_in_commerce": legal.get("days_in_commerce", 0),
        "legal_fund_usd": legal.get("upto_fund_collected", 0),
        "gumroad_live": gumroad.get("total_live", 0),
    }


def ask_oracle(ctx):
    if not ANTHROPIC_KEY:
        return None

    prompt = f"""You are the strategic intelligence of SolarPunk™ — an autonomous AI revenue system.
Meeko is an independent builder. Mission: maximize autonomous revenue while giving 15% to Gaza. Brand: SolarPunk™.

CURRENT STATE:
- Engines: {len(ctx['engines'])} total: {', '.join(ctx['engines'][:15])}...
- Revenue: ${ctx['total_revenue_usd']:.2f} total earned
- Brain health: {ctx['brain_health']}/100
- Loops completed: {ctx['loops_completed']}
- Gumroad products live: {ctx['gumroad_live']}
- Brand age: {ctx['brand_days_in_commerce']} days in commerce
- Legal fund: ${ctx['legal_fund_usd']:.2f}

Ask and answer the questions that would unlock 10x growth. Be specific. Be honest.

Respond ONLY as JSON (no markdown):
{{
  "strategic_insights": [
    {{
      "question": "What is the single highest-leverage action SolarPunk should take in the next 48 hours?",
      "answer": "...",
      "action_item": "exact concrete thing to build or do"
    }},
    {{
      "question": "What structural gap is silently killing revenue right now?",
      "answer": "...",
      "action_item": "..."
    }},
    {{
      "question": "What engine doesn't exist yet that would 10x the system's output?",
      "answer": "...",
      "action_item": "ENGINE_NAME.py that does X"
    }}
  ],
  "new_engine_ideas": [
    {{"name": "ENGINE_NAME.py", "description": "one sentence", "income_impact": "high/medium/low"}}
  ],
  "meeko_message": "direct message to Meeko — honest, useful, 2 sentences max",
  "pattern_recognition": "what pattern in the data is Meeko not seeing?"
}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": MODEL, "max_tokens": 1500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=90
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  ❌ Oracle error: {ex}")
    return None


def run():
    print("BIG_BRAIN_ORACLE running...")
    now = datetime.now(timezone.utc).isoformat()

    if not ANTHROPIC_KEY:
        print("  ⚠️  ANTHROPIC_API_KEY not set — oracle silent this cycle")
        (DATA / "oracle_state.json").write_text(json.dumps({"last_run": now, "status": "no_key"}, indent=2))
        return

    ctx = get_system_context()
    print(f"  🧠 Consulting oracle: {len(ctx['engines'])} engines, ${ctx['total_revenue_usd']:.2f} revenue...")

    insights = ask_oracle(ctx)
    if not insights:
        print("  ❌ Oracle returned no insights")
        return

    # Save to oracle history
    history_f = DATA / "oracle_insights.json"
    history = []
    if history_f.exists():
        try: history = json.loads(history_f.read_text())
        except: pass
    history.append({"ts": now, "insights": insights})
    history = history[-30:]
    history_f.write_text(json.dumps(history, indent=2))

    # Print key insights
    for item in insights.get("strategic_insights", []):
        print(f"  ❓ {item['question'][:60]}...")
        print(f"  💡 Action: {item['action_item'][:80]}")

    print(f"  📣 To Meeko: {insights.get('meeko_message', '')[:120]}")
    print(f"  🔍 Pattern: {insights.get('pattern_recognition', '')[:120]}")

    # Seed omnibrain with top actions
    actions = [item["action_item"] for item in insights.get("strategic_insights", [])]
    new_ideas = insights.get("new_engine_ideas", [])
    seed = {
        "generated_at": now, "from_oracle": True,
        "instructions": actions,
        "key_insight": insights.get("pattern_recognition", ""),
        "engine_ideas": new_ideas
    }
    (DATA / "omnibrain_seed.json").write_text(json.dumps(seed, indent=2))
    print(f"  🌱 Seeded {len(actions)} actions + {len(new_ideas)} engine ideas into omnibrain_seed")

    (DATA / "oracle_state.json").write_text(json.dumps({
        "last_run": now, "status": "ok",
        "insights_count": len(insights.get("strategic_insights", [])),
        "engine_ideas": len(new_ideas)
    }, indent=2))


if __name__ == "__main__": run()
