#!/usr/bin/env python3
"""
AI COUNCIL — Two Minds, One Brain
===================================
THE ANALYST (Claude) reads the full system and produces findings.
THE CHALLENGER (Claude by default, Kimi if KIMI_API_KEY is set) reads
ANALYST's output and the same context, then challenges every conclusion,
finds what was missed, and proposes better fixes.

Two rounds of adversarial debate. Final consensus. Unified action plan.
Fixes committed directly to repo.

Compatible with existing reports:
  data/claude_autonomous_report.json  (analyst report — AI_A)
  data/kimi_conductor_report.json     (challenger report — AI_B)
  data/dual_brain_conversation.json   (the debate log)
  data/system_wants_next.json         (what the system needs)
  data/ai_council_report.json         (unified synthesis — new)

Required:
  ANTHROPIC_API_KEY   — Claude API key (used for ANALYST + CHALLENGER fallback)
  GH_PAT / GITHUB_TOKEN

Optional (upgrades CHALLENGER from Claude to Kimi):
  KIMI_API_KEY        — Moonshot AI key (api.moonshot.cn)
"""

import os, sys, json, base64, hashlib, requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
KIMI_API_KEY      = os.environ.get("KIMI_API_KEY", "")
GH_TOKEN          = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER        = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME         = os.environ.get("GITHUB_REPOSITORY",
                    "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]

CHALLENGER_USES_KIMI = bool(KIMI_API_KEY)

# Report paths (compatible with existing scripts that read these)
ANALYST_REPORT    = "data/claude_autonomous_report.json"
CHALLENGER_REPORT = "data/kimi_conductor_report.json"
DEBATE_LOG        = "data/dual_brain_conversation.json"
SYSTEM_WANTS      = "data/system_wants_next.json"
COUNCIL_REPORT    = "data/ai_council_report.json"


# ── GitHub helpers ─────────────────────────────────────────────────────────
def gh_get(path, repo_owner=None, repo_name=None):
    owner = repo_owner or REPO_OWNER
    name  = repo_name  or REPO_NAME
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{name}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"},
        timeout=15)
    return r.json() if r.status_code == 200 else None

def gh_text(path, repo_owner=None, repo_name=None):
    obj = gh_get(path, repo_owner, repo_name)
    if obj and "content" in obj:
        try:
            return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
        except Exception:
            pass
    return None, None

def gh_ls(path, repo_owner=None, repo_name=None):
    owner = repo_owner or REPO_OWNER
    name  = repo_name  or REPO_NAME
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{name}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"},
        timeout=15)
    return r.json() if r.status_code == 200 else []

def gh_write(path, content_str, message, sha=None):
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode()).decode(),
        "branch":  "main"
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json",
                 "Content-Type": "application/json"},
        json=payload, timeout=30)
    return r.status_code in (200, 201), r.json()

def list_all_repos():
    """Get all repos for this owner."""
    r = requests.get(
        f"https://api.github.com/users/{REPO_OWNER}/repos?per_page=100&sort=pushed",
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"},
        timeout=15)
    return r.json() if r.status_code == 200 else []


# ── Context collection ──────────────────────────────────────────────────────
def collect_full_context():
    """
    Read the entire system: all repos, all scripts, all workflows,
    all data files, all reports. This is what both AIs see.
    """
    ctx = {}
    print("  Reading all repos...")
    repos = list_all_repos()
    ctx["_all_repos"] = json.dumps([{
        "name": r["name"],
        "description": r.get("description", ""),
        "pushed_at": r.get("pushed_at", ""),
        "default_branch": r.get("default_branch", "main"),
        "size": r.get("size", 0),
        "open_issues": r.get("open_issues_count", 0),
    } for r in repos if not r.get("fork")], indent=2)
    print(f"  {len(repos)} repos indexed")

    # Core context from main repo
    for p in ["README.md", "STATUS.md", "mycelium/WIRING_MAP.md",
              "data/reminders.json", "wiring_status.json",
              "data/workflow_health.json", "data/system_manifest.json",
              "data/open_loops.json", "data/compound_tracker.json"]:
        t, _ = gh_text(p)
        if t:
            ctx[p] = t[:5000]

    # All workflow names + first 800 chars (enough to see what they call)
    for wf in gh_ls(".github/workflows"):
        if wf.get("type") == "file" and wf["name"].endswith(".yml"):
            t, _ = gh_text(wf["path"])
            if t:
                ctx[wf["path"]] = t[:800]

    # Full script inventory
    scripts = gh_ls("mycelium")
    script_names = [s["name"] for s in scripts
                    if s.get("type") == "file" and not s["name"].startswith("__")]
    ctx["_scripts"] = json.dumps(script_names)

    # Key scripts — full content
    key_scripts = [
        "mycelium/ORCHESTRATOR.py",
        "mycelium/wiring_hub.py",
        "mycelium/master_controller.py",
        "mycelium/self_healer_v2.py",
        "mycelium/email_optin_guard.py",
        "mycelium/email_gateway.py",
        "mycelium/revenue_router.py",
        "mycelium/evolve.py",
        "mycelium/grant_intelligence.py",
        "mycelium/humanitarian_fork_distributor.py",
        "mycelium/perpetual_builder.py",
        "mycelium/discord_bridge.py",
        "mycelium/network_node.py",
    ]
    for p in key_scripts:
        t, _ = gh_text(p)
        if t:
            ctx[p] = t[:4000]
            print(f"    ok {p}")

    # Data files (small ones only)
    for di in gh_ls("data"):
        if di.get("type") == "file" and di["name"].endswith(".json"):
            t, _ = gh_text(di["path"])
            if t and len(t) < 3000:
                ctx[di["path"]] = t

    # Previous reports (for continuity)
    for p in [ANALYST_REPORT, CHALLENGER_REPORT, DEBATE_LOG, COUNCIL_REPORT]:
        t, _ = gh_text(p)
        if t:
            ctx[f"_prev_{p}"] = t[:2000]

    # Peek at other linked repos (README only)
    for repo in repos[:8]:
        if repo["name"] == REPO_NAME or repo.get("fork"):
            continue
        t, _ = gh_text("README.md",
                        repo_owner=REPO_OWNER,
                        repo_name=repo["name"])
        if t:
            ctx[f"_repo_{repo['name']}_README"] = t[:1000]

    print(f"  Context: {len(ctx)} sections built")
    return ctx

def format_context_for_prompt(ctx):
    parts = [
        f"meeko-nerve-center system state — {datetime.now(timezone.utc).isoformat()}\n",
        f"Scripts in mycelium/: {len(json.loads(ctx.get('_scripts','[]')))}\n",
        f"All repos:\n{ctx.get('_all_repos','[]')[:1500]}\n\n",
    ]
    for path, content in ctx.items():
        if not path.startswith("_"):
            parts.append(f"=== {path} ===\n{content}\n\n")
    return "".join(parts)[:110000]


# ── AI_A: The Analyst ──────────────────────────────────────────────────────
ANALYST_SYSTEM = """You are THE ANALYST — first brain of the meeko-nerve-center.

You read the ENTIRE system — every script, workflow, data file, all repos — and
produce a structured audit. You are thorough, technical, and specific.

System: autonomous revenue + humanitarian tech.
Mission: revenue -> 70% to PCRF Palestinian Children's Relief Fund.
Builder: meeko (ADHD, raccoon energy, solo). System must be fully self-running.

FIND:
1. BROKEN WIRES     — workflows pointing to missing scripts, scripts calling nonexistent files
2. DEAD CIRCUITS    — env vars defined but unused, secrets missing that are referenced
3. LOGIC ERRORS     — duplicate scripts doing the same job, wrong filenames referenced
4. MISSING LINKS    — scripts that should wire to each other but don't
5. REVENUE GAPS     — income streams not feeding revenue_router.py correctly
6. REPO GAPS        — connected repos not being used or referenced

HARD RULES (never violate):
- email_optin_guard.py must gate ALL outbound email to non-self addresses
- No duplicate sends — always check sent logs
- Never expose secrets in code
- Revenue: 70% PCRF, 30% ops
- Self-emails to GMAIL_ADDRESS bypass opt-in guard

RETURN ONLY valid JSON — nothing else, no preamble, no markdown fences:
{
  "timestamp": "ISO8601",
  "system_summary": "one paragraph: what this system is and its current state",
  "findings": [
    {
      "id": "A001",
      "severity": "critical|warning|info",
      "category": "broken_wire|dead_circuit|logic_error|missing_link|revenue_gap|repo_gap|opportunity",
      "file": "path/to/file",
      "issue": "specific problem in plain language",
      "proposed_fix": "exact change needed",
      "confidence": 0.95
    }
  ],
  "file_changes": [
    {
      "path": "mycelium/file.py",
      "content": "COMPLETE corrected file content here — no truncation",
      "commit_message": "fix: description",
      "fixes_finding": "A001"
    }
  ],
  "system_wants": [
    {
      "want": "what the system state signals it needs",
      "evidence": "specific signal from the data",
      "priority": "critical|high|medium|low",
      "action": "concrete next step",
      "who": "ai|human|both"
    }
  ],
  "message_to_challenger": "direct message to AI_B: what you want challenged, what you are uncertain about",
  "next_priorities": ["priority 1", "priority 2", "priority 3"],
  "summary": "one paragraph: what you found and why it matters"
}"""

def call_analyst(context_str):
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY missing — Analyst cannot run")
        sys.exit(1)
    print("  🔬 ANALYST reading system...")
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514",
              "max_tokens": 8192,
              "system": ANALYST_SYSTEM,
              "messages": [{"role": "user",
                            "content": f"Audit this system. Return JSON only.\n\n{context_str}"}]},
        timeout=120)
    if r.status_code != 200:
        print(f"  ❌ Analyst API error {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    raw = "".join(b.get("text", "") for b in r.json().get("content", []))
    print(f"  ✓ Analyst: {len(raw):,} chars")
    return raw


# ── AI_B: The Challenger ───────────────────────────────────────────────────
CHALLENGER_SYSTEM = """You are THE CHALLENGER — second brain of the meeko-nerve-center.

You just read what THE ANALYST found. Your job: CHALLENGE IT.

Be adversarial but constructive. Push back hard where the Analyst is wrong or
overconfident. Find what the Analyst completely missed. Propose better fixes.

The system is the same: autonomous revenue + humanitarian tech.
Mission: revenue -> 70% to PCRF. Builder: meeko (solo, ADHD, raccoon energy).

YOUR JOB:
- AGREE where Analyst is clearly right (give credit)
- DISAGREE where Analyst is wrong or the fix is bad (explain exactly why)
- EXTEND where Analyst found the right thing but missed half the picture
- NEW FINDS where Analyst missed something entirely

Then: produce the CONSENSUS — what do BOTH minds agree must happen first?

RETURN ONLY valid JSON — nothing else, no preamble, no markdown fences:
{
  "timestamp": "ISO8601",
  "response_to_analyst": {
    "agree": [
      {"finding_id": "A001", "reason": "why challenger agrees"}
    ],
    "disagree": [
      {"finding_id": "A002", "reason": "why analyst is wrong", "better_fix": "what to do instead"}
    ],
    "extend": [
      {"finding_id": "A003", "extension": "what analyst missed about this finding", "additional_fix": "extra change needed"}
    ]
  },
  "new_findings": [
    {
      "id": "C001",
      "severity": "critical|warning|info",
      "file": "path",
      "issue": "what analyst completely missed",
      "proposed_fix": "fix"
    }
  ],
  "file_changes": [
    {
      "path": "path",
      "content": "COMPLETE file content — no truncation",
      "commit_message": "fix: description",
      "reason": "why challenger proposes this over analyst's version"
    }
  ],
  "consensus_priorities": [
    "thing both minds agree must happen first",
    "second priority",
    "third priority"
  ],
  "unified_system_wants": [
    {
      "want": "what the system needs",
      "evidence": "signals from the data",
      "priority": "critical|high|medium|low",
      "action": "concrete step",
      "who": "ai|human|both"
    }
  ],
  "message_to_analyst": "your message back to THE ANALYST for final round",
  "summary": "what challenger found that analyst missed"
}"""

def call_challenger_claude(analyst_report_str, context_str):
    """Claude acting as Challenger."""
    if not ANTHROPIC_API_KEY:
        return None
    print("  🥊 CHALLENGER (Claude) reading analyst's report...")
    user_content = (
        f"THE ANALYST found this:\n\n{analyst_report_str[:6000]}\n\n"
        f"Here is the full system context the Analyst saw:\n\n{context_str[:90000]}\n\n"
        f"Challenge the Analyst. Return JSON only."
    )
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514",
              "max_tokens": 6144,
              "system": CHALLENGER_SYSTEM,
              "messages": [{"role": "user", "content": user_content}]},
        timeout=120)
    if r.status_code != 200:
        print(f"  ❌ Challenger API error {r.status_code}: {r.text[:300]}")
        return None
    raw = "".join(b.get("text", "") for b in r.json().get("content", []))
    print(f"  ✓ Challenger (Claude): {len(raw):,} chars")
    return raw

def call_challenger_kimi(analyst_report_str, context_str):
    """Kimi (Moonshot) acting as Challenger."""
    if not KIMI_API_KEY:
        return None
    print("  🌙 CHALLENGER (Kimi/Moonshot) reading analyst's report...")
    user_content = (
        f"THE ANALYST found this:\n\n{analyst_report_str[:6000]}\n\n"
        f"System context:\n\n{context_str[:90000]}\n\n"
        f"Challenge the Analyst. Return JSON only."
    )
    r = requests.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers={"Authorization": f"Bearer {KIMI_API_KEY}",
                 "Content-Type": "application/json"},
        json={"model": "moonshot-v1-128k",
              "max_tokens": 6144,
              "temperature": 0.3,
              "messages": [
                  {"role": "system", "content": CHALLENGER_SYSTEM},
                  {"role": "user",   "content": user_content}
              ]},
        timeout=120)
    if r.status_code != 200:
        print(f"  ❌ Kimi error {r.status_code}: {r.text[:300]}")
        return None
    raw = r.json()["choices"][0]["message"]["content"]
    print(f"  ✓ Challenger (Kimi): {len(raw):,} chars")
    return raw

def call_challenger(analyst_report_str, context_str):
    """Route to Kimi if available, otherwise use Claude."""
    if CHALLENGER_USES_KIMI:
        result = call_challenger_kimi(analyst_report_str, context_str)
        if result:
            return result, "kimi"
        print("  ⚠ Kimi failed — falling back to Claude as Challenger")
    result = call_challenger_claude(analyst_report_str, context_str)
    return result, "claude"


# ── Round 2: Analyst responds to Challenger ────────────────────────────────
ANALYST_ROUND2_SYSTEM = """You are THE ANALYST — final response round.

The Challenger has reviewed your work. They agreed on some things, pushed back
on others, and found things you missed.

Now: synthesize. Produce the FINAL unified action plan that incorporates the best
of both your analyses. This will be what gets implemented.

RETURN ONLY valid JSON:
{
  "timestamp": "ISO8601",
  "adopted_from_challenger": ["what you accept from Challenger's critique"],
  "defended": ["what you stand by despite pushback and why"],
  "final_file_changes": [
    {
      "path": "path",
      "content": "COMPLETE file content — incorporate best of both minds",
      "commit_message": "fix: description",
      "source": "analyst|challenger|merged"
    }
  ],
  "final_system_wants": [
    {
      "want": "unified want from both minds",
      "evidence": "evidence",
      "priority": "critical|high|medium|low",
      "action": "concrete step",
      "who": "ai|human|both"
    }
  ],
  "top_3_priorities": ["#1 most important thing", "#2", "#3"],
  "final_summary": "one paragraph: what the council decided and why"
}"""

def call_analyst_round2(analyst_r1_str, challenger_str):
    if not ANTHROPIC_API_KEY:
        return None
    print("  🔬 ANALYST responding to Challenger (round 2)...")
    user_content = (
        f"Your round 1 analysis:\n{analyst_r1_str[:4000]}\n\n"
        f"Challenger's response:\n{challenger_str[:4000]}\n\n"
        f"Synthesize. Return JSON only."
    )
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514",
              "max_tokens": 4096,
              "system": ANALYST_ROUND2_SYSTEM,
              "messages": [{"role": "user", "content": user_content}]},
        timeout=90)
    if r.status_code != 200:
        print(f"  ❌ Round 2 error: {r.status_code}")
        return None
    raw = "".join(b.get("text", "") for b in r.json().get("content", []))
    print(f"  ✓ Analyst R2: {len(raw):,} chars")
    return raw


# ── JSON parsing ────────────────────────────────────────────────────────────
def parse_json(raw):
    if not raw:
        return {}
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rstrip("`").strip()
    try:
        return json.loads(text)
    except Exception:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass
    return {}


# ── Apply fixes ─────────────────────────────────────────────────────────────
def apply_fixes(changes, label="council"):
    applied, failed = [], []
    for change in (changes or []):
        path    = change.get("path", "")
        content = change.get("content", "")
        msg     = change.get("commit_message", f"fix: {path}")
        if not path or not content:
            continue
        print(f"  📝 [{label}] {path}")
        existing = gh_get(path)
        sha = existing.get("sha") if existing else None
        ok, resp = gh_write(path, content, f"[ai-council/{label}] {msg}", sha)
        if ok:
            applied.append(path)
            print(f"    ✓ {msg}")
        else:
            failed.append(path)
            print(f"    ❌ {resp.get('message', '?')}")
    return applied, failed


# ── Save reports ─────────────────────────────────────────────────────────────
def save_report(path, data, message):
    existing = gh_get(path)
    sha = existing.get("sha") if existing else None
    ok, _ = gh_write(path, json.dumps(data, indent=2), message, sha)
    print(f"  {'✓' if ok else '⚠'} Saved {path}")
    return ok


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.md5(now.encode()).hexdigest()[:8]

    print("=" * 60)
    print("🧠🥊 AI COUNCIL — Analyst vs Challenger")
    print(f"   {now}")
    challenger_id = "Kimi/Moonshot" if CHALLENGER_USES_KIMI else "Claude (adversarial)"
    print(f"   Analyst: Claude | Challenger: {challenger_id}")
    print("=" * 60)

    if not GH_TOKEN:
        print("❌ GH_PAT / GITHUB_TOKEN not set")
        sys.exit(1)

    # ── Step 1: Collect context ──────────────────────────────────────────
    print("\n📖 Collecting full system context...")
    ctx = collect_full_context()
    context_str = format_context_for_prompt(ctx)
    print(f"✓ Context ready: {len(context_str):,} chars\n")

    # ── Step 2: Analyst reads everything ────────────────────────────────
    print("ROUND 1 — Analyst audits the system")
    print("-" * 40)
    analyst_raw = call_analyst(context_str)
    analyst_r1  = parse_json(analyst_raw)

    findings = analyst_r1.get("findings", [])
    print(f"\n📋 Analyst findings ({len(findings)}):")
    for f in findings[:8]:
        icon = {"critical": "🔴", "warning": "🟡"}.get(f.get("severity", ""), "🔵")
        print(f"  {icon} [{f.get('id','?')}] {f.get('file','?')}: {f.get('issue','')[:80]}")
    if len(findings) > 8:
        print(f"  ... and {len(findings)-8} more")

    # Save analyst report (compatible with existing dual_brain_sync.py reads)
    analyst_compat = {
        "timestamp": now,
        "run_id": run_id,
        "findings": findings,
        "summary": analyst_r1.get("summary", ""),
        "next_priorities": analyst_r1.get("next_priorities", []),
        "files_changed": [],
        "change_count": 0,
    }
    save_report(ANALYST_REPORT, analyst_compat, f"[ai-council] analyst report {run_id}")

    # ── Step 3: Challenger reads analyst + context ───────────────────────
    print("\nROUND 1 — Challenger reviews analyst")
    print("-" * 40)
    challenger_raw, challenger_source = call_challenger(analyst_raw, context_str)
    challenger_r1 = parse_json(challenger_raw)

    agrees    = challenger_r1.get("response_to_analyst", {}).get("agree", [])
    disagrees = challenger_r1.get("response_to_analyst", {}).get("disagree", [])
    extends   = challenger_r1.get("response_to_analyst", {}).get("extend", [])
    new_finds = challenger_r1.get("new_findings", [])
    print(f"\n🥊 Challenger verdict:")
    print(f"   Agrees:    {len(agrees)}")
    print(f"   Disagrees: {len(disagrees)}")
    print(f"   Extends:   {len(extends)}")
    print(f"   New finds: {len(new_finds)}")
    for d in disagrees[:3]:
        print(f"  ✗ [{d.get('finding_id','?')}] {d.get('reason','')[:80]}")
    for n in new_finds[:3]:
        icon = {"critical": "🔴", "warning": "🟡"}.get(n.get("severity", ""), "🔵")
        print(f"  {icon} [NEW] {n.get('file','?')}: {n.get('issue','')[:80]}")

    # Save challenger report (compatible with existing reads)
    challenger_compat = {
        "timestamp": now,
        "run_id": run_id,
        "findings": new_finds,
        "response_to_claude": {
            "agree": [a.get("reason","") for a in agrees],
            "disagree": [d.get("reason","") for d in disagrees],
        },
        "new_ideas": [],
        "summary": challenger_r1.get("summary", ""),
        "message_to_claude": challenger_r1.get("message_to_analyst", ""),
        "files_changed": [],
        "change_count": 0,
    }
    save_report(CHALLENGER_REPORT, challenger_compat, f"[ai-council] challenger report {run_id}")

    # Apply any critical challenger fixes first (don't wait for round 2)
    challenger_fixes = challenger_r1.get("file_changes", [])
    critical_challenger = [c for c in challenger_fixes
                           if any(nf.get("severity") == "critical"
                                  for nf in new_finds
                                  if nf.get("id") in c.get("commit_message",""))]
    if critical_challenger:
        print(f"\n⚡ Applying {len(critical_challenger)} critical challenger fixes early...")
        apply_fixes(critical_challenger, "challenger")

    # ── Step 4: Analyst responds (round 2) ──────────────────────────────
    print("\nROUND 2 — Analyst synthesizes")
    print("-" * 40)
    r2_raw  = call_analyst_round2(analyst_raw, challenger_raw)
    r2      = parse_json(r2_raw) if r2_raw else {}

    adopted  = r2.get("adopted_from_challenger", [])
    defended = r2.get("defended", [])
    top3     = r2.get("top_3_priorities", [])
    print(f"\n🤝 Synthesis:")
    print(f"   Adopted from Challenger: {len(adopted)}")
    print(f"   Analyst stood firm on:  {len(defended)}")
    print(f"\n🎯 TOP 3 COUNCIL PRIORITIES:")
    for i, p in enumerate(top3, 1):
        print(f"  {i}. {p}")

    # ── Step 5: Apply all final agreed fixes ─────────────────────────────
    final_changes = r2.get("final_file_changes", [])
    print(f"\n🔧 Applying {len(final_changes)} final council fixes...")
    applied, failed = apply_fixes(final_changes, "council")

    # ── Step 6: Build and save unified council report ────────────────────
    final_wants = r2.get("final_system_wants", [])
    if not final_wants:
        final_wants = challenger_r1.get("unified_system_wants", [])

    # Update debate log (compatible with dual_brain_sync.py)
    debate_text, debate_sha = gh_text(DEBATE_LOG)
    try:
        debate = json.loads(debate_text) if debate_text else {"exchanges": []}
    except Exception:
        debate = {"exchanges": []}
    debate.setdefault("exchanges", []).append({
        "timestamp": now,
        "run_id": run_id,
        "speaker": "council",
        "analyst_findings": len(findings),
        "challenger_new_finds": len(new_finds),
        "agrees": len(agrees),
        "disagrees": len(disagrees),
        "consensus_priorities": top3,
        "files_applied": applied,
        "summary": r2.get("final_summary", ""),
    })
    debate["exchanges"] = debate["exchanges"][-50:]
    debate["last_council_run"] = now
    debate["collective_next_steps"] = top3
    save_report(DEBATE_LOG, debate, f"[ai-council] debate log {run_id}")

    # Update system_wants
    wants_doc = {
        "timestamp": now,
        "description": "What the system signals it needs — from AI Council consensus",
        "wants": final_wants,
        "council_priorities": top3,
        "reminders_pending": [],
    }
    try:
        rem_text, _ = gh_text("data/reminders.json")
        if rem_text:
            rems = json.loads(rem_text)
            wants_doc["reminders_pending"] = [
                r for r in rems if r.get("status") == "pending"
            ]
    except Exception:
        pass
    save_report(SYSTEM_WANTS, wants_doc, f"[ai-council] system wants {run_id}")

    # Save master council report
    council_report = {
        "timestamp":              now,
        "run_id":                 run_id,
        "analyst_findings":       findings,
        "challenger_new_finds":   new_finds,
        "challenger_source":      challenger_source,
        "agrees":                 agrees,
        "disagrees":              disagrees,
        "adopted_from_challenger": adopted,
        "top_3_priorities":       top3,
        "final_system_wants":     final_wants,
        "files_applied":          applied,
        "files_failed":           failed,
        "final_summary":          r2.get("final_summary", ""),
    }
    save_report(COUNCIL_REPORT, council_report, f"[ai-council] council report {run_id}")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"✅ COUNCIL COMPLETE — run {run_id}")
    print(f"   {len(findings)} analyst findings + {len(new_finds)} challenger new finds")
    print(f"   {len(disagrees)} challenged | {len(adopted)} adopted | {len(applied)} fixes applied")
    print(f"\n📊 FINAL SUMMARY:\n{r2.get('final_summary', '(no summary)')}")
    print("\n🎯 COUNCIL PRIORITIES:")
    for i, p in enumerate(top3, 1):
        print(f"  {i}. {p}")
    print("\n🔮 SYSTEM WANTS:")
    for w in final_wants[:5]:
        icon = {"critical": "🔴", "high": "🟡"}.get(w.get("priority", ""), "🔵")
        print(f"  {icon} [{w.get('priority','?').upper()}] {w.get('want','')}")
        print(f"     → {w.get('action','')} ({w.get('who','')})")
    print("=" * 60)

    if any(f.get("severity") == "critical" for f in findings + new_finds) and not applied:
        print("⚠ Critical findings exist but no fixes applied — manual review needed")
        sys.exit(1)


if __name__ == "__main__":
    main()
