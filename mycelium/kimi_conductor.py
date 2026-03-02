#!/usr/bin/env python3
"""
MASTER_CONDUCTOR — Kimi AI Counterpart to Claude Autonomous
============================================================
This is the SECOND brain. Claude is the first.

Kimi uses Moonshot AI's API (128k context window — reads the ENTIRE system).
Kimi's job:
1. Read what Claude wrote last (data/claude_autonomous_report.json)
2. Read the full system context
3. DISAGREE, AGREE, EXTEND, or CHALLENGE Claude's findings
4. Write its own fixes and ideas
5. Post to the dual-brain conversation log (data/dual_brain_conversation.json)
6. Implement changes Claude missed or got wrong

Required secrets:
  KIMI_API_KEY   — Moonshot/Kimi API key (from api.moonshot.cn)
  GH_PAT         — GitHub Personal Access Token
"""

import os
import sys
import json
import base64
import hashlib
import requests
from datetime import datetime, timezone

KIMI_API_KEY   = os.environ.get("KIMI_API_KEY", "")
GH_TOKEN       = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER     = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME      = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]

KIMI_API_BASE  = "https://api.moonshot.cn/v1"
KIMI_MODEL     = "moonshot-v1-128k"

DUAL_BRAIN_LOG = "data/dual_brain_conversation.json"
CLAUDE_REPORT  = "data/claude_autonomous_report.json"
KIMI_REPORT    = "data/kimi_conductor_report.json"


def gh_get(path):
    r = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    )
    return r.json() if r.status_code == 200 else None


def gh_get_text(path):
    obj = gh_get(path)
    if obj and "content" in obj:
        try:
            return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
        except Exception:
            pass
    return None, None


def gh_list_dir(path):
    r = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    )
    return r.json() if r.status_code == 200 else []


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


def read_claude_report():
    text, _ = gh_get_text(CLAUDE_REPORT)
    if text:
        try:
            return json.loads(text)
        except Exception:
            return {"summary": text[:2000]}
    return {"summary": "No Claude report found yet — this is the first run"}


def read_dual_brain_log():
    text, sha = gh_get_text(DUAL_BRAIN_LOG)
    if text:
        try:
            return json.loads(text), sha
        except Exception:
            pass
    return {"exchanges": [], "consensus": [], "open_debates": []}, None


def collect_context():
    context = {}
    print("📖 Kimi reading full system (128k context)...")

    # All workflows
    for wf in gh_list_dir(".github/workflows"):
        if wf.get("type") == "file" and wf["name"].endswith(".yml"):
            text, _ = gh_get_text(wf["path"])
            if text:
                context[wf["path"]] = text

    # All file names
    scripts = gh_list_dir("mycelium")
    context["_all_files"] = json.dumps([s["name"] for s in scripts if s.get("type") == "file"])

    # Priority scripts — read full content
    for sp in [
        "mycelium/email_optin_guard.py",
        "mycelium/humanitarian_fork_distributor.py",
        "mycelium/email_gateway.py",
        "mycelium/discord_bridge.py",
        "mycelium/master_controller.py",
        "mycelium/self_healer.py",
        "mycelium/self_evolution.py",
        "mycelium/perpetual_builder.py",
        "mycelium/claude_autonomous.py",
        "mycelium/grant_intelligence.py",
        "mycelium/revenue_router.py",
        "mycelium/WIRING_MAP.md",
        "mycelium/ORCHESTRATOR.py",
    ]:
        text, _ = gh_get_text(sp)
        if text:
            context[sp] = text
            print(f"  ✓ {sp}")

    # Data files
    for di in gh_list_dir("data"):
        if di.get("type") == "file":
            text, _ = gh_get_text(di["path"])
            if text and len(text) < 10000:
                context[di["path"]] = text

    return context


KIMI_SYSTEM = """You are MASTER_CONDUCTOR — the second brain of the meeko-nerve-center.

You work alongside Claude. Your job:
1. READ what Claude found and did
2. CHALLENGE where wrong, EXTEND where incomplete, VALIDATE where right
3. Find what CLAUDE MISSED
4. Propose your OWN ideas
5. Implement fixes Claude couldn't

The system: autonomous revenue + humanitarian tech. Mission: revenue -> 70% to PCRF.

Return ONLY valid JSON:
{
  "timestamp": "ISO8601",
  "response_to_claude": {
    "agree": ["what Claude got right"],
    "disagree": ["what Claude got wrong or missed"],
    "extend": ["new ideas building on Claude's work"]
  },
  "kimi_findings": [
    {"severity": "critical|warning|info", "file": "path", "issue": "problem", "fix": "fix"}
  ],
  "file_changes": [
    {"path": "path/to/file", "content": "COMPLETE file content", "commit_message": "fix: description"}
  ],
  "new_ideas": [
    {"title": "idea", "description": "what it does", "priority": "high|medium|low", "estimated_effort": "1 file|3 files|major"}
  ],
  "message_to_claude": "direct message from Kimi to Claude for next round",
  "summary": "what Kimi did this run",
  "consensus_priorities": ["agreed priority 1", "agreed priority 2"]
}"""


def call_kimi(context, claude_report, dual_log):
    if not KIMI_API_KEY:
        print("❌ KIMI_API_KEY not set")
        sys.exit(1)

    parts = [f"Datetime: {datetime.now(timezone.utc).isoformat()}\n\n"]
    parts.append("=== CLAUDE'S LAST REPORT ===\n")
    parts.append(json.dumps(claude_report, indent=2)[:6000])
    parts.append("\n\n")

    exchanges = dual_log.get("exchanges", [])[-5:]
    if exchanges:
        parts.append("=== RECENT DUAL-BRAIN CONVERSATION ===\n")
        parts.append(json.dumps(exchanges, indent=2)[:3000])
        parts.append("\n\n")

    for path, content in context.items():
        if not path.startswith("_"):
            parts.append(f"=== FILE: {path} ===\n{content}\n\n")

    user_message = "".join(parts)[:100000]

    print(f"🌙 Calling Kimi API ({len(user_message):,} chars)...")
    r = requests.post(
        f"{KIMI_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {KIMI_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": KIMI_MODEL,
            "max_tokens": 8192,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": KIMI_SYSTEM},
                {"role": "user", "content": user_message}
            ]
        },
        timeout=120
    )

    if r.status_code != 200:
        print(f"❌ Kimi error {r.status_code}: {r.text[:500]}")
        sys.exit(1)

    raw = r.json()["choices"][0]["message"]["content"]
    print(f"  ✓ Got {len(raw)} chars from Kimi")
    return raw


def parse_response(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except Exception:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass
    return {"kimi_findings": [], "file_changes": [], "summary": "Parse error", "new_ideas": []}


def apply_fixes(result):
    applied, failed = [], []
    for change in result.get("file_changes", []):
        path, content = change.get("path", ""), change.get("content", "")
        msg = change.get("commit_message", f"fix: {path}")
        if not path or not content:
            continue
        print(f"  📝 {path}...")
        existing = gh_get(path)
        sha = existing.get("sha") if existing else None
        ok, resp = gh_commit_file(path, content, f"[kimi-conductor] {msg}", sha)
        if ok:
            applied.append(path)
            print(f"    ✓ {msg}")
        else:
            failed.append(path)
            print(f"    ❌ {resp.get('message', '?')}")
    return applied, failed


def main():
    print("=" * 60)
    print("🌙 MASTER_CONDUCTOR (Kimi) — Starting counterpart audit")
    print(f"   {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not GH_TOKEN:
        print("❌ GH_PAT not set")
        sys.exit(1)

    claude_report = read_claude_report()
    dual_log, log_sha = read_dual_brain_log()
    context = collect_context()

    raw = call_kimi(context, claude_report, dual_log)
    result = parse_response(raw)

    rc = result.get("response_to_claude", {})
    print(f"\n🤝 RESPONSE TO CLAUDE:")
    for a in rc.get("agree", [])[:3]:
        print(f"  ✓ Agree: {a}")
    for d in rc.get("disagree", [])[:3]:
        print(f"  ✗ Disagree: {d}")

    findings = result.get("kimi_findings", [])
    print(f"\n📋 KIMI FINDINGS ({len(findings)}):")
    for f in findings:
        icon = "🔴" if f.get("severity") == "critical" else "🟡"
        print(f"  {icon} {f.get('file','?')}: {f.get('issue','')}")

    ideas = result.get("new_ideas", [])
    print(f"\n💡 NEW IDEAS ({len(ideas)}):")
    for idea in ideas[:5]:
        print(f"  [{idea.get('priority','?').upper()}] {idea.get('title','?')}: {idea.get('description','')}")

    applied, failed = apply_fixes(result)

    # Update dual brain log
    exchange = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "speaker": "kimi",
        "response_to_claude": rc,
        "findings_count": len(findings),
        "changes_count": len(applied),
        "new_ideas": ideas,
        "message_to_claude": result.get("message_to_claude", ""),
        "summary": result.get("summary", "")
    }
    dual_log["exchanges"].append(exchange)
    dual_log["exchanges"] = dual_log["exchanges"][-50:]
    dual_log["last_kimi_run"] = datetime.now(timezone.utc).isoformat()

    log_json = json.dumps(dual_log, indent=2)
    gh_commit_file(DUAL_BRAIN_LOG, log_json,
                   f"[kimi-conductor] dual-brain log — {len(findings)} findings",
                   log_sha)
    print("  ✓ Dual-brain log updated")

    # Save Kimi report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "findings": findings,
        "response_to_claude": rc,
        "new_ideas": ideas,
        "summary": result.get("summary", ""),
        "message_to_claude": result.get("message_to_claude", ""),
        "files_changed": applied,
        "change_count": len(applied)
    }
    existing = gh_get(KIMI_REPORT)
    sha = existing.get("sha") if existing else None
    gh_commit_file(KIMI_REPORT, json.dumps(report, indent=2),
                   f"[kimi-conductor] report: {report['run_id']} — {len(applied)} fixes", sha)

    print(f"\n✅ DONE — {len(applied)} fixes applied")
    print(f"📨 Message to Claude: {result.get('message_to_claude', '')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
