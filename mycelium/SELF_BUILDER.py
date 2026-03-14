# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SELF_BUILDER.py v3 — Infinite engine generator
===============================================
PREVIOUS BUG: Fixed list of 10 engine ideas. After building all 10,
engine ran every cycle doing nothing.

FIX: Reads architect_plan.json for AI-suggested engine priorities.
After seed list, uses AI to generate new engine ideas from scratch.
Infinite loop. Always builds something new.

ALSO: validate_code() now uses compile() instead of forbidden patterns
to properly check Python syntax before pushing.
"""
import os, json, sys, requests, re, base64
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GH_REPO  = "meekotharaccoon-cell/meeko-nerve-center"
GMAIL    = os.environ.get("GMAIL_ADDRESS", "")
GPWD     = os.environ.get("GMAIL_APP_PASSWORD", "")

sys.path.insert(0, str(MYCELIUM))
try:
    from AI_CLIENT import ask
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("  AI_CLIENT not found")

# Seed ideas — first cycles
SEED_IDEAS = [
    ("REDDIT_POSTER",       "Posts SolarPunk and Gaza Rose content to relevant subreddits on schedule, tracks karma and engagement"),
    ("REVENUE_FORECASTER",  "Projects monthly revenue from all streams using historical data, emails weekly forecast to Meeko"),
    ("REDBUBBLE_ENGINE",    "Generates Redbubble product upload checklists and descriptions for Gaza Rose art"),
    ("OPPORTUNITY_SCOUT",   "Scans email and web for collaboration and partnership opportunities, scores them, surfaces best ones"),
    ("LOOP_DASHBOARD",      "Rebuilds the live GitHub Pages dashboard with real-time cycle stats every run"),
    ("AFFILIATE_TRACKER",   "Tracks all affiliate link performance across Amazon, Gumroad, Notion, Canva, reports clicks and estimates"),
    ("KNOWLEDGE_UPDATER",   "Pulls latest AI and grant news via public RSS feeds, stores key insights in memory_palace"),
    ("PITCH_GENERATOR",     "Creates one-page investor and grantor pitches for SolarPunk and Gaza Rose Gallery"),
    ("COMMUNITY_BUILDER",   "Finds aligned creators and builders via public GitHub and social profiles, drafts outreach emails"),
    ("PRODUCT_OPTIMIZER",   "Reads sales data from all products, suggests price and copy changes to improve conversions"),
    ("NEWSLETTER_ENGINE",   "Drafts weekly newsletter content from system activity, prepares for Substack/Beehiiv publish"),
    ("CONTENT_SCHEDULER",   "Takes queued social posts, schedules them for optimal times, reports engagement metrics"),
    ("GRANT_TRACKER",       "Tracks all grant applications submitted, follows up on deadlines, reports pipeline status"),
    ("SEO_OPTIMIZER",       "Analyzes all landing pages, suggests SEO improvements, rewrites meta tags for top traffic"),
    ("TESTIMONIAL_ENGINE",  "Generates authentic-sounding case study frameworks for each product, prepares social proof copy"),
]

SYSTEM_PROMPT = """You write Python engines for SolarPunk — an autonomous AI income system on GitHub Actions.
Rules: 100% legal, ethical, Gaza-mission aligned. No unauthorized access, no scraping without permission.
Tech available: requests, pathlib, smtplib, json, os, datetime, re (stdlib).
Secrets via os.environ: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GITHUB_TOKEN, HF_TOKEN, KOFI_USERNAME.
Every engine must:
- Load/save JSON state in data/
- Print progress clearly
- Handle ALL exceptions gracefully (never crash)
- Have: load(), save(), run(), and if __name__=="__main__": run()
- Start with #!/usr/bin/env python3 and a docstring
Keep it under 200 lines. Make it actually work."""


def load():
    f = DATA / "self_builder_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "built": [], "total_built": 0, "ai_generated_ideas": []}


def save(state):
    (DATA / "self_builder_state.json").write_text(json.dumps(state, indent=2))


def get_existing_engines():
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/contents/mycelium",
            headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=15
        )
        if r.status_code == 200:
            return {f["name"].replace(".py", "").upper() for f in r.json() if f["name"].endswith(".py")}
    except:
        pass
    # Fallback: scan local mycelium/
    return {f.stem.upper() for f in MYCELIUM.glob("*.py")}


def get_next_idea(existing_engines, state):
    built_names = {b["name"] for b in state.get("built", [])}

    # Try seed ideas first
    for name, desc in SEED_IDEAS:
        if name not in existing_engines and name not in built_names:
            return name, desc

    # Try ARCHITECT plan
    plan_file = DATA / "architect_plan.json"
    if plan_file.exists():
        try:
            plan = json.loads(plan_file.read_text())
            for idea in plan.get("engine_ideas", []):
                n = idea.get("name", "").upper().replace(" ", "_")
                d = idea.get("purpose", "")
                if n and n not in existing_engines and n not in built_names:
                    print(f"  Using ARCHITECT idea: {n}")
                    return n, d
        except:
            pass

    # AI generates a fresh idea — infinite supply
    if not AI_AVAILABLE:
        cycle = state.get("cycles", 1)
        return f"REVENUE_AMPLIFIER_V{cycle}", f"Amplifies revenue stream #{cycle} by optimizing outreach and conversion"

    already = list(existing_engines)[:30]
    prompt = f"""SolarPunk needs a new Python engine. Already built: {already}

Generate ONE new engine idea that:
- Does NOT exist in the list above
- Generates or amplifies revenue (affiliate, product, email, social, SEO, etc.)
- Can run on GitHub Actions with no human input
- Uses only: requests, smtplib, json, os, pathlib, datetime, re

Respond ONLY with JSON: {{"name": "ENGINE_NAME_UPPERCASE", "purpose": "one sentence what it does and why it makes money"}}"""

    result = None
    try:
        import json as _json
        text = ask([{"role": "user", "content": prompt}], max_tokens=150)
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0:
            result = _json.loads(text[s:e])
    except:
        pass

    if result and result.get("name"):
        name = result["name"].upper().replace(" ", "_")
        desc = result.get("purpose", "Generates revenue autonomously")
        if name not in existing_engines and name not in built_names:
            return name, desc

    # Ultimate fallback
    cycle = state.get("cycles", 1)
    return f"REVENUE_ENGINE_V{cycle}", f"Revenue generation engine cycle {cycle}"


def generate_code(name, desc):
    if not AI_AVAILABLE:
        return None

    prompt = f"""Write a complete, production-ready Python engine:
NAME: {name}
PURPOSE: {desc}

Requirements:
- Starts with #!/usr/bin/env python3
- Has a docstring explaining what it does
- Imports: os, json from pathlib import Path from datetime import datetime, timezone
- Functions: load(), save(state), run()
- Saves state to data/{name.lower()}_state.json
- Handles all exceptions
- Prints progress: print(f"ENGINE_NAME cycle {{n}}")
- if __name__ == "__main__": run()
- Under 180 lines
- Works with zero human input

Write ONLY the Python code, no markdown fences."""

    try:
        code = ask([{"role": "user", "content": prompt}], max_tokens=3000, system=SYSTEM_PROMPT)
        # Strip markdown fences if present
        code = re.sub(r'^```python\s*', '', code.strip())
        code = re.sub(r'\s*```$', '', code.strip())
        return code.strip()
    except Exception as e:
        print(f"  Code generation error: {e}")
        return None


def validate(code, name):
    if not code or len(code) < 80:
        return False, "Too short"
    if "def run(" not in code and "def run(" not in code:
        return False, "Missing run()"
    # Compile check — catches syntax errors
    try:
        compile(code, f"{name}.py", "exec")
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    # Safety check
    for bad in ["os.system(", "subprocess.call(", "__import__(", "eval(", "exec("]:
        if bad in code:
            return False, f"Unsafe: {bad}"
    return True, "OK"


def push_to_github(name, code):
    if not GH_TOKEN:
        print("  No GITHUB_TOKEN — saving locally")
        (MYCELIUM / f"{name}.py").write_text(code)
        return False

    path = f"mycelium/{name}.py"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    # Get existing SHA if file exists
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=headers, timeout=10)
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": f"[SELF_BUILDER] Auto-generated: {name}",
        "content": base64.b64encode(code.encode()).decode(),
        "committer": {"name": "SolarPunk Brain", "email": "meekotharaccoon@gmail.com"}
    }
    if sha:
        payload["sha"] = sha

    r2 = requests.put(
        f"https://api.github.com/repos/{GH_REPO}/contents/{path}",
        headers=headers, json=payload, timeout=20
    )
    return r2.status_code in (200, 201)


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    total_built = state.get("total_built", 0)
    print(f"SELF_BUILDER v3 cycle {state['cycles']} | {total_built} engines built | AI={'on' if AI_AVAILABLE else 'off'}")

    if not AI_AVAILABLE:
        print("  No AI — skipping code generation this cycle")
        save(state)
        return state

    existing = get_existing_engines()
    name, desc = get_next_idea(existing, state)
    print(f"  Generating: {name}")
    print(f"  Purpose: {desc[:80]}")

    code = generate_code(name, desc)
    if not code:
        print("  Generation failed")
        save(state)
        return state

    ok, reason = validate(code, name)
    if not ok:
        print(f"  Validation failed: {reason}")
        # Save locally anyway for inspection
        (DATA / f"rejected_{name}.py").write_text(code)
        save(state)
        return state

    # Save locally first (picked up by git commit step)
    (MYCELIUM / f"{name}.py").write_text(code)

    # Also push via API for immediate availability
    pushed = push_to_github(name, code)

    state.setdefault("built", []).append({
        "name":   name,
        "desc":   desc,
        "ts":     datetime.now(timezone.utc).isoformat(),
        "pushed": pushed,
        "lines":  len(code.splitlines()),
    })
    state["total_built"] = total_built + 1

    print(f"  ✅ {name} ({len(code.splitlines())} lines) | {'pushed to GitHub' if pushed else 'saved locally'}")
    save(state)
    return state


if __name__ == "__main__":
    run()
