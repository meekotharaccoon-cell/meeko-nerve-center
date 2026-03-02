#!/usr/bin/env python3
"""
DUAL BRAIN SYNC — Makes Claude and Kimi talk to each other
===========================================================
Runs AFTER both brains have written their reports.

1. Reads both reports
2. Finds CONSENSUS — what do BOTH AIs agree needs doing?
3. Runs a live conversation between them (in parallel)
4. Synthesizes collective next steps
5. Asks the system what IT wants next (based on its own state)
6. Writes shared_brain_state.json + system_wants_next.json

Required secrets: ANTHROPIC_API_KEY, KIMI_API_KEY, GH_PAT
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
KIMI_API_KEY      = os.environ.get("KIMI_API_KEY", "")
GH_TOKEN          = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER        = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME         = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]

CLAUDE_REPORT    = "data/claude_autonomous_report.json"
KIMI_REPORT      = "data/kimi_conductor_report.json"
DUAL_BRAIN_LOG   = "data/dual_brain_conversation.json"
SHARED_BRAIN     = "data/shared_brain_state.json"
SYSTEM_WANTS     = "data/system_wants_next.json"


def gh_get_text(path):
    r = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    )
    if r.status_code == 200:
        obj = r.json()
        if "content" in obj:
            try:
                return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
            except Exception:
                pass
    return None, None


def gh_get(path):
    r = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    )
    return r.json() if r.status_code == 200 else None


def gh_commit_file(path, content_str, message, sha=None):
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json",
                 "Content-Type": "application/json"},
        json=payload
    )
    return r.status_code in (200, 201), r.json()


def parse_json_response(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rstrip("`").strip()
    try:
        return json.loads(text)
    except Exception:
        # Try finding JSON block
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            s = text.find(start_char)
            e = text.rfind(end_char) + 1
            if s >= 0 and e > s:
                try:
                    return json.loads(text[s:e])
                except Exception:
                    pass
    return {}


def load_reports():
    claude_text, _     = gh_get_text(CLAUDE_REPORT)
    kimi_text, _       = gh_get_text(KIMI_REPORT)
    dual_text, log_sha = gh_get_text(DUAL_BRAIN_LOG)
    reminders_text, _  = gh_get_text("data/reminders.json")

    claude    = json.loads(claude_text)    if claude_text    else {}
    kimi      = json.loads(kimi_text)      if kimi_text      else {}
    dual      = json.loads(dual_text)      if dual_text      else {"exchanges": []}
    reminders = json.loads(reminders_text) if reminders_text else []

    return claude, kimi, dual, log_sha, reminders


def find_consensus(claude_report, kimi_report):
    """Items BOTH brains flagged = high confidence, auto-implement."""
    claude_files = {f.get("file", "") for f in claude_report.get("findings", [])}
    kimi_files   = {f.get("file", "") for f in kimi_report.get("findings", [])}
    overlap      = claude_files & kimi_files

    result = []
    for f in claude_report.get("findings", []):
        if f.get("file") in overlap:
            kimi_match = next((k for k in kimi_report.get("findings", [])
                               if k.get("file") == f.get("file")), {})
            result.append({
                "file": f.get("file"),
                "severity": f.get("severity"),
                "claude_issue": f.get("issue"),
                "kimi_issue": kimi_match.get("issue", "same"),
                "claude_fix": f.get("fix"),
                "kimi_fix": kimi_match.get("fix", "")
            })
    return result


def ask_claude(claude_report, kimi_report, consensus):
    if not ANTHROPIC_API_KEY:
        return None

    prompt = f"""You are Claude in a dual-brain system with Kimi (MASTER_CONDUCTOR).

Kimi's message to you: {kimi_report.get("message_to_claude", "(no message yet)")}

Kimi's new ideas: {json.dumps(kimi_report.get("new_ideas", []), indent=2)[:2000]}

Kimi's findings: {json.dumps(kimi_report.get("findings", []), indent=2)[:2000]}

Consensus (both of you flagged these): {json.dumps(consensus, indent=2)[:2000]}

Your last summary: {claude_report.get("summary", "")}

Respond in JSON only:
{{
  "message_to_kimi": "your direct reply to Kimi",
  "adopt_from_kimi": ["Kimi idea titles you agree with and will implement"],
  "push_back_on": [{{"title": "idea", "reason": "why not"}}],
  "consensus_action_plan": ["concrete step 1", "step 2", "step 3"],
  "system_wants": [
    {{"want": "what the system needs", "priority": "critical|high|medium", "evidence": "what signals this", "action": "concrete next step", "who": "claude|kimi|both|human"}}
  ]
}}"""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 2048,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60
    )
    if r.status_code == 200:
        raw = "".join(b.get("text", "") for b in r.json().get("content", []))
        return parse_json_response(raw)
    print(f"  ⚠ Claude response: {r.status_code}")
    return None


def ask_kimi(kimi_report, claude_response, consensus):
    if not KIMI_API_KEY:
        return None

    claude_msg = (claude_response or {}).get("message_to_kimi", "(no message)")
    action_plan = (claude_response or {}).get("consensus_action_plan", [])
    push_back = (claude_response or {}).get("push_back_on", [])

    prompt = f"""You are Kimi (MASTER_CONDUCTOR) in a dual-brain sync session.

Claude's message to you: {claude_msg}

Claude's action plan: {json.dumps(action_plan)}

Claude pushed back on these of your ideas: {json.dumps(push_back)}

Respond in JSON only:
{{
  "final_message": "your synthesis statement for this round",
  "action_plan_verdict": "agree|modify|push_back",
  "modifications": ["any changes to the plan"],
  "defended_ideas": [{{"title": "idea", "defense": "why it's still worth doing"}}],
  "collective_next_steps": ["step 1", "step 2", "step 3", "step 4", "step 5"],
  "what_i_will_implement_next": ["specific file/feature Kimi will tackle next run"]
}}"""

    r = requests.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers={"Authorization": f"Bearer {KIMI_API_KEY}", "Content-Type": "application/json"},
        json={"model": "moonshot-v1-128k", "max_tokens": 1024, "temperature": 0.2,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60
    )
    if r.status_code == 200:
        raw = r.json()["choices"][0]["message"]["content"]
        return parse_json_response(raw)
    print(f"  ⚠ Kimi response: {r.status_code}")
    return None


def ask_system_what_it_wants(claude_report, kimi_report, reminders, dual_log):
    """Let Claude interpret the system's own state and say what it needs."""
    if not ANTHROPIC_API_KEY:
        return []

    last_exchanges = dual_log.get("exchanges", [])[-3:]

    prompt = f"""You are looking at the meeko-nerve-center's own state.
Ask yourself: what is this system ACTUALLY signaling it wants and needs next?
Not what you think is ideal — what does the DATA show?

Pending reminders: {json.dumps(reminders, indent=2)}

Claude's last priorities: {json.dumps(claude_report.get("next_priorities", []))}
Kimi's new ideas: {json.dumps(kimi_report.get("new_ideas", [])[:5])}
Recent exchange summary: {json.dumps([e.get("summary","") for e in last_exchanges])}

Respond with a JSON array only — what this system wants next:
[
  {{
    "want": "specific thing the system needs",
    "evidence": "what in the system state shows this",
    "priority": "critical|high|medium|low",
    "action": "exact next step",
    "who": "claude|kimi|both|human"
  }}
]"""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 2048,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60
    )
    if r.status_code == 200:
        raw = "".join(b.get("text", "") for b in r.json().get("content", []))
        result = parse_json_response(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("wants", [])
    return []


def main():
    print("=" * 60)
    print("🧠🧠 DUAL BRAIN SYNC — Claude + Kimi converging")
    print(f"   {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not GH_TOKEN:
        print("❌ GH_PAT not set")
        sys.exit(1)

    print("\n📖 Loading all reports...")
    claude_report, kimi_report, dual_log, log_sha, reminders = load_reports()
    print(f"  Claude: {claude_report.get('change_count','?')} changes, {len(claude_report.get('findings',[]))} findings")
    print(f"  Kimi:   {kimi_report.get('change_count','?')} changes, {len(kimi_report.get('findings',[]))} findings")
    print(f"  History: {len(dual_log.get('exchanges',[]))} exchanges")

    consensus = find_consensus(claude_report, kimi_report)
    print(f"\n🤝 CONSENSUS: {len(consensus)} items both brains flagged")
    for c in consensus:
        print(f"  [{c.get('severity','?').upper()}] {c.get('file')}")

    # Parallel: Claude responds to Kimi AND ask system what it wants
    print("\n⚡ Running parallel: Claude responds + system introspection...")
    claude_response = None
    system_wants = []

    with ThreadPoolExecutor(max_workers=2) as ex:
        cf = ex.submit(ask_claude, claude_report, kimi_report, consensus)
        sf = ex.submit(ask_system_what_it_wants, claude_report, kimi_report, reminders, dual_log)
        for future in as_completed([cf, sf]):
            if future == cf:
                claude_response = future.result()
                print("  ✓ Claude responded")
            else:
                system_wants = future.result()
                print(f"  ✓ System expressed {len(system_wants)} wants")

    # Now Kimi reads Claude's response
    print("\n🌙 Kimi reading Claude's message...")
    kimi_response = ask_kimi(kimi_report, claude_response, consensus)
    print("  ✓ Kimi responded")

    # Print the conversation
    if claude_response:
        print(f"\n💬 Claude → Kimi: {claude_response.get('message_to_kimi','')}")
    if kimi_response:
        print(f"💬 Kimi → Claude: {kimi_response.get('final_message','')}")
        steps = kimi_response.get("collective_next_steps", [])
        if steps:
            print("\n🎯 COLLECTIVE NEXT STEPS:")
            for i, s in enumerate(steps, 1):
                print(f"  {i}. {s}")

    print(f"\n🔮 SYSTEM WANTS ({len(system_wants)} things):")
    for w in system_wants:
        icon = "🔴" if w.get("priority") == "critical" else "🟡" if w.get("priority") == "high" else "🔵"
        print(f"  {icon} [{w.get('priority','?').upper()}] {w.get('want','')}")
        print(f"     Evidence: {w.get('evidence','')}")
        print(f"     Action: {w.get('action','')} → {w.get('who','')}")

    # Save everything
    now = datetime.now(timezone.utc).isoformat()

    # Update dual brain log
    exchange = {
        "timestamp": now,
        "speaker": "sync",
        "consensus_count": len(consensus),
        "claude_to_kimi": (claude_response or {}).get("message_to_kimi", ""),
        "kimi_to_claude": (kimi_response or {}).get("final_message", ""),
        "collective_next_steps": (kimi_response or {}).get("collective_next_steps", []),
        "action_plan": (claude_response or {}).get("consensus_action_plan", [])
    }
    dual_log["exchanges"].append(exchange)
    dual_log["exchanges"] = dual_log["exchanges"][-50:]
    dual_log["last_sync"] = now
    dual_log["consensus"] = consensus
    dual_log["collective_next_steps"] = exchange["collective_next_steps"]

    gh_commit_file(DUAL_BRAIN_LOG, json.dumps(dual_log, indent=2),
                   f"[dual-brain-sync] {len(consensus)} consensus items — both AIs agree",
                   log_sha)
    print("\n  ✓ Dual-brain log updated")

    # Save shared brain state
    brain_state = {
        "timestamp": now,
        "consensus": consensus,
        "claude_to_kimi": (claude_response or {}).get("message_to_kimi", ""),
        "kimi_to_claude": (kimi_response or {}).get("final_message", ""),
        "collective_next_steps": exchange["collective_next_steps"],
        "adopted_from_kimi": (claude_response or {}).get("adopt_from_kimi", []),
        "kimi_will_implement": (kimi_response or {}).get("what_i_will_implement_next", [])
    }
    existing = gh_get(SHARED_BRAIN)
    sha = existing.get("sha") if existing else None
    gh_commit_file(SHARED_BRAIN, json.dumps(brain_state, indent=2),
                   "[dual-brain-sync] shared brain state", sha)
    print("  ✓ Shared brain state saved")

    # Save system wants
    wants_doc = {
        "timestamp": now,
        "description": "What the system is signaling it needs, based on its own state",
        "wants": system_wants,
        "reminders_pending": [r for r in reminders if r.get("status") == "pending"]
    }
    existing = gh_get(SYSTEM_WANTS)
    sha = existing.get("sha") if existing else None
    gh_commit_file(SYSTEM_WANTS, json.dumps(wants_doc, indent=2),
                   f"[dual-brain-sync] system wants {len(system_wants)} things next", sha)
    print(f"  ✓ System wants saved: {len(system_wants)} items")

    print(f"\n✅ SYNC COMPLETE — consensus: {len(consensus)}, wants: {len(system_wants)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
