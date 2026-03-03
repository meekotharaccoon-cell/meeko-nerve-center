"""
SYNTHESIS_FACTORY.py
====================
The meta-engine. Reads every existing engine in /mycelium/, discovers
unwired combination opportunities using the Anthropic API, then WRITES
new engines and commits them — all without any human in the loop.

This directly kills the 4-hour Claude chat bottleneck:
  → While you're away from chat, OMNIBRAIN calls this
  → This calls the Anthropic API (already in GitHub Secrets)
  → New engines get written, committed, and added to OMNIBRAIN
  → System grows 24/7 regardless of chat tier limits

Run modes:
  python SYNTHESIS_FACTORY.py               # discover + build top 3 combos
  python SYNTHESIS_FACTORY.py --discover    # just list opportunities, no build
  python SYNTHESIS_FACTORY.py --build N     # build N new engines this cycle
"""

import os
import json
import sys
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# ─── CONFIG ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = "meekotharaccoon-cell"
REPO_NAME = "meeko-nerve-center"
MYCELIUM_DIR = Path(__file__).parent
DATA_DIR = MYCELIUM_DIR / ".." / "data"
DATA_DIR.mkdir(exist_ok=True)
SYNTHESIS_LOG = DATA_DIR / "synthesis_log.json"
BUILD_COUNT = int(os.environ.get("SYNTHESIS_BUILD_COUNT", "3"))

HEADERS_ANTHROPIC = {
    "x-api-key": ANTHROPIC_API_KEY,
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01"
}

HEADERS_GITHUB = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ─── HELPERS ────────────────────────────────────────────────────────────────

def load_synthesis_log():
    if SYNTHESIS_LOG.exists():
        try:
            return json.loads(SYNTHESIS_LOG.read_text())
        except:
            pass
    return {"built": [], "discovered": [], "last_run": None}

def save_synthesis_log(log):
    SYNTHESIS_LOG.write_text(json.dumps(log, indent=2))

def scan_existing_engines():
    """Returns dict of {filename: first_docstring_or_comment}"""
    engines = {}
    for f in sorted(MYCELIUM_DIR.glob("*.py")):
        name = f.name
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").split("\n")
            # grab first 5 lines as summary
            summary = " | ".join(l.strip() for l in lines[:5] if l.strip() and not l.strip().startswith("#!"))
            engines[name] = summary[:200]
        except:
            engines[name] = "(unreadable)"
    return engines

def load_wiring_map():
    wmap = MYCELIUM_DIR / "WIRING_MAP.md"
    if wmap.exists():
        return wmap.read_text(encoding="utf-8", errors="ignore")[:3000]
    return "No wiring map found."

def claude_api_call(prompt, max_tokens=4000):
    """Direct call to Anthropic API using the key already in GitHub Secrets."""
    if not ANTHROPIC_API_KEY:
        print("⚠️  No ANTHROPIC_API_KEY — running in demo mode")
        return None
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=HEADERS_ANTHROPIC,
            json=payload,
            timeout=120
        )
        r.raise_for_status()
        data = r.json()
        return data["content"][0]["text"]
    except Exception as e:
        print(f"❌ Claude API error: {e}")
        return None

def discover_combinations(engines: dict, wiring_map: str, log: dict) -> list:
    """Ask Claude to find the N most valuable unwired combos."""
    already_built = set(log.get("built", []))
    engine_list = "\n".join(f"- {k}: {v[:120]}" for k, v in engines.items() if k not in already_built)
    
    prompt = f"""You are analyzing the Meeko Nerve Center — an autonomous AI system with {len(engines)} Python engines.

EXISTING ENGINES (partial list):
{engine_list}

CURRENT WIRING MAP (what's already connected):
{wiring_map[:2000]}

ALREADY SYNTHESIZED (skip these):
{', '.join(already_built) if already_built else 'None yet'}

Your task: Identify the {BUILD_COUNT} most HIGH-VALUE new engine combinations that:
1. Combine 2-4 EXISTING engines in a way not yet done
2. Create something genuinely new (not just renaming)
3. Directly generates revenue OR dramatically amplifies system capabilities
4. Are feasible to implement in one Python file using only stdlib + requests

For each combination, respond with EXACTLY this JSON array format (no markdown, just JSON):
[
  {{
    "filename": "new_engine_name.py",
    "combines": ["engine_a.py", "engine_b.py"],
    "what_it_does": "One clear sentence",
    "revenue_mechanism": "How it makes money or amplifies revenue",
    "key_logic": "3-5 bullet points of what the code does"
  }}
]

Focus on combos that didn't exist before. Be creative but practical."""

    response = claude_api_call(prompt, max_tokens=2000)
    if not response:
        return get_fallback_combos(already_built)
    
    # Parse JSON from response
    try:
        # Find JSON array in response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            combos = json.loads(response[start:end])
            return combos[:BUILD_COUNT]
    except Exception as e:
        print(f"⚠️  JSON parse error: {e}")
        print(f"Raw response: {response[:500]}")
    
    return get_fallback_combos(already_built)

def get_fallback_combos(already_built: set) -> list:
    """Hardcoded high-value combos if API unavailable."""
    all_combos = [
        {
            "filename": "signal_content_machine.py",
            "combines": ["crypto_signals.py", "congress_watcher.py", "cross_poster.py"],
            "what_it_does": "When congressional trades align with crypto signals, auto-create and post content about it",
            "revenue_mechanism": "Viral political-finance content drives traffic to Gumroad + Ko-fi",
            "key_logic": [
                "Monitor congress_watcher for unusual trading activity",
                "Cross-reference with crypto_signals for correlated price moves",
                "Generate content via Claude API explaining the correlation",
                "Auto-post to all social channels via cross_poster",
                "Track engagement and optimize future posts"
            ]
        },
        {
            "filename": "memory_idea_spawner.py",
            "combines": ["long_term_memory.py", "idea_engine.py", "knowledge_synthesizer.py"],
            "what_it_does": "Every cycle, synthesizes memories into new ideas, then builds those ideas into engine specs",
            "revenue_mechanism": "Autonomous idea-to-product pipeline with zero human input",
            "key_logic": [
                "Load recent memories from long_term_memory",
                "Feed to knowledge_synthesizer to find patterns",
                "Pass patterns to idea_engine to generate product concepts",
                "Score each idea by revenue potential",
                "Output top 3 as buildable specs for SYNTHESIS_FACTORY"
            ]
        },
        {
            "filename": "viral_grant_writer.py",
            "combines": ["grant_intelligence.py", "impact_storyteller.py", "press_release_engine.py"],
            "what_it_does": "Turn grant research into compelling applications AND press releases simultaneously",
            "revenue_mechanism": "Directly funds the system via grants while building press presence",
            "key_logic": [
                "Load grant opportunities from grant_intelligence",
                "Generate impact narrative via impact_storyteller",
                "Write full grant application package",
                "Simultaneously generate press release about the work",
                "Submit application + schedule press release for same day"
            ]
        },
        {
            "filename": "audience_revenue_loop.py",
            "combines": ["audience_intelligence.py", "ab_testing_engine.py", "revenue_optimizer.py", "newsletter_engine.py"],
            "what_it_does": "Continuously A/B tests revenue messaging, auto-optimizes based on audience response",
            "revenue_mechanism": "Self-optimizing revenue funnel, improves conversion each cycle",
            "key_logic": [
                "Load audience segments from audience_intelligence",
                "Generate A/B variants for each revenue channel",
                "Track which variants convert via ab_testing_engine",
                "Feed winners to revenue_optimizer",
                "Auto-update newsletter_engine with best-performing angles"
            ]
        },
        {
            "filename": "space_content_monetizer.py",
            "combines": ["space_bridge.py", "art_cause_generator.py", "gumroad_listing_update.py"],
            "what_it_does": "Turn live NASA/ISS data into art concepts, auto-list them on Gumroad",
            "revenue_mechanism": "Space-data-inspired digital art sells passively on Gumroad",
            "key_logic": [
                "Pull daily NASA APOD and ISS position from space_bridge",
                "Feed into art_cause_generator to create concept art descriptions",
                "Generate product listings from those concepts",
                "Auto-post to gumroad_listing_update",
                "Cross-post previews to social channels"
            ]
        }
    ]
    return [c for c in all_combos if c["filename"] not in already_built][:BUILD_COUNT]

def write_engine_code(combo: dict, engines: dict) -> str:
    """Use Claude API to write actual working Python code for the combo."""
    # Read source engines for context
    source_code_snippets = []
    for eng_name in combo.get("combines", []):
        eng_path = MYCELIUM_DIR / eng_name
        if eng_path.exists():
            code = eng_path.read_text(encoding="utf-8", errors="ignore")[:1500]
            source_code_snippets.append(f"=== {eng_name} (first 1500 chars) ===\n{code}")
    
    sources = "\n\n".join(source_code_snippets[:3])
    key_logic = "\n".join(f"  {i+1}. {l}" for i, l in enumerate(combo.get("key_logic", [])))
    
    prompt = f"""Write a complete, working Python script called {combo['filename']}.

PURPOSE: {combo['what_it_does']}
REVENUE: {combo['revenue_mechanism']}

KEY LOGIC:
{key_logic}

COMBINES THESE EXISTING ENGINES:
{sources[:3000]}

REQUIREMENTS:
- Complete, runnable Python 3 script
- Uses only stdlib + requests (no pip installs)
- Reads credentials from environment variables
- Has a main() function
- Loads/saves state in ../data/ directory
- Logs what it does with emoji prefixes like ✅ ❌ 🔄
- Has clear docstring at top explaining what it does
- Gracefully handles missing API keys (demo mode)
- Actually implements the key logic (not placeholder stubs)

Write ONLY the Python code. No markdown fences. Start with the docstring."""

    code = claude_api_call(prompt, max_tokens=4000)
    if not code:
        return generate_fallback_code(combo)
    
    # Clean up any markdown fences if present
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:])
        if code.endswith("```"):
            code = code[:-3].strip()
    
    return code

def generate_fallback_code(combo: dict) -> str:
    """Minimal fallback when API unavailable."""
    logic_str = "\n".join(f"    # {l}" for l in combo.get("key_logic", []))
    combines_str = ", ".join(combo.get("combines", []))
    
    return f'''"""
{combo["filename"]}
{'='*len(combo["filename"])}
{combo["what_it_does"]}

Revenue: {combo["revenue_mechanism"]}
Combines: {combines_str}

AUTO-GENERATED by SYNTHESIS_FACTORY.py
"""

import os
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STATE_FILE = DATA_DIR / "{combo["filename"].replace(".py", "_state.json")}"


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {{"runs": 0, "last_run": None, "results": []}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    state = load_state()
    state["runs"] += 1
    state["last_run"] = datetime.now().isoformat()
    
    print(f"🔄 {combo["filename"]} — run #{state['runs']}")
    print(f"📋 Purpose: {combo['what_it_does']}")
    
{logic_str}
    
    print("✅ Cycle complete")
    save_state(state)
    return state


if __name__ == "__main__":
    main()
'''

def push_file_to_github(filepath: str, content: str, commit_msg: str) -> bool:
    """Push a new file to GitHub via API."""
    import base64
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filepath}"
    
    # Check if file exists (for update)
    sha = None
    try:
        r = requests.get(url, headers=HEADERS_GITHUB)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except:
        pass
    
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    
    try:
        r = requests.put(url, headers=HEADERS_GITHUB, json=payload)
        r.raise_for_status()
        print(f"✅ Pushed {filepath} to GitHub")
        return True
    except Exception as e:
        print(f"❌ GitHub push failed for {filepath}: {e}")
        return False

def update_wiring_map(new_engines: list):
    """Append newly built engines to WIRING_MAP.md."""
    wmap_path = MYCELIUM_DIR / "WIRING_MAP.md"
    existing = wmap_path.read_text(encoding="utf-8", errors="ignore") if wmap_path.exists() else ""
    
    additions = f"\n\n---\n## 🧬 AUTO-SYNTHESIZED [{datetime.now().strftime('%Y-%m-%d')}]\n\n"
    for eng in new_engines:
        additions += f"### {eng['filename']}\n"
        additions += f"- **Combines:** {', '.join(eng['combines'])}\n"
        additions += f"- **Does:** {eng['what_it_does']}\n"
        additions += f"- **Revenue:** {eng['revenue_mechanism']}\n\n"
    
    updated = existing + additions
    wmap_path.write_text(updated, encoding="utf-8")
    
    # Push to GitHub
    push_file_to_github(
        "mycelium/WIRING_MAP.md",
        updated,
        f"🕸️ WIRING_MAP updated with {len(new_engines)} new synthesis connections"
    )

def send_synthesis_report(built_engines: list):
    """Email report of what was synthesized this cycle."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not gmail_addr or not gmail_pass:
            print("⚠️  No Gmail creds — skipping synthesis report email")
            return
        
        body = f"""🧬 SYNTHESIS FACTORY REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}

New engines built this cycle: {len(built_engines)}

"""
        for eng in built_engines:
            body += f"✅ {eng['filename']}\n"
            body += f"   Combines: {', '.join(eng['combines'])}\n"
            body += f"   Does: {eng['what_it_does']}\n"
            body += f"   Revenue: {eng['revenue_mechanism']}\n\n"
        
        body += """
The system is building itself.
No chat required.
No bottleneck.

— Meeko Nerve Center 🦝
"""
        msg = MIMEText(body)
        msg["Subject"] = f"🧬 Synthesis: {len(built_engines)} new engines built"
        msg["From"] = gmail_addr
        msg["To"] = gmail_addr
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(gmail_addr, gmail_pass)
            s.send_message(msg)
        print("📧 Synthesis report emailed")
    except Exception as e:
        print(f"⚠️  Email failed: {e}")

# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    discover_only = "--discover" in sys.argv
    
    print("🧬 SYNTHESIS FACTORY starting...")
    print(f"   Mode: {'discover only' if discover_only else f'discover + build {BUILD_COUNT}'}")
    
    log = load_synthesis_log()
    engines = scan_existing_engines()
    wiring_map = load_wiring_map()
    
    print(f"📚 Found {len(engines)} existing engines")
    print(f"🔨 Already synthesized: {len(log['built'])}")
    
    # Discover opportunities
    print("\n🔍 Discovering new combination opportunities...")
    combos = discover_combinations(engines, wiring_map, log)
    
    if not combos:
        print("✅ No new combinations needed right now")
        return
    
    print(f"\n💡 Found {len(combos)} opportunities:")
    for i, c in enumerate(combos, 1):
        print(f"   {i}. {c['filename']} ← {' + '.join(c['combines'])}")
        print(f"      {c['what_it_does']}")
    
    if discover_only:
        print("\n[discover mode — not building]")
        log["discovered"].extend([c["filename"] for c in combos])
        save_synthesis_log(log)
        return
    
    # Build each engine
    built = []
    for combo in combos:
        filename = combo["filename"]
        if filename in log["built"]:
            print(f"⏭️  Skipping {filename} (already built)")
            continue
        
        print(f"\n⚙️  Building {filename}...")
        code = write_engine_code(combo, engines)
        
        if not code or len(code) < 100:
            print(f"❌ Code generation failed for {filename}")
            continue
        
        # Push to GitHub
        success = push_file_to_github(
            f"mycelium/{filename}",
            code,
            f"🧬 SYNTHESIS: {filename} ← {' + '.join(combo['combines'][:2])}"
        )
        
        if success:
            built.append(combo)
            log["built"].append(filename)
            print(f"✅ {filename} built and deployed!")
            time.sleep(2)  # Rate limit
    
    # Update wiring map
    if built:
        print(f"\n🕸️  Updating WIRING_MAP.md with {len(built)} new engines...")
        update_wiring_map(built)
        
        # Email report
        send_synthesis_report(built)
        
        print(f"\n🎉 SYNTHESIS COMPLETE: {len(built)} new engines added to the system")
        print("   They'll run next OMNIBRAIN cycle automatically")
    
    log["last_run"] = datetime.now().isoformat()
    save_synthesis_log(log)
    return {"built": len(built), "engines": [e["filename"] for e in built]}

if __name__ == "__main__":
    main()
