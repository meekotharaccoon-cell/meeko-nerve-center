#!/usr/bin/env python3
"""
CLAUDE AUTONOMOUS — Self-Running Claude Replacement
====================================================
This script IS Claude, running inside GitHub Actions.

What it does (same as Claude in chat):
1. Reads the entire system: workflows, scripts, data files, env vars
2. Calls the Anthropic API with full context
3. Claude analyzes: bad connections, missing wires, broken references, bugs
4. Gets back a structured list of file changes to make
5. Commits every fix directly to main
6. Writes a report so you can see what it did

Required secrets:
  ANTHROPIC_API_KEY — your Claude API key
  GH_PAT           — GitHub Personal Access Token with repo write access
  NOTION_TOKEN     — (optional) to read DIRECTIVES page

Run: python mycelium/claude_autonomous.py
Or:  via .github/workflows/claude-autonomous.yml (scheduled)
"""

import os
import sys
import json
import base64
import hashlib
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN          = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER        = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME         = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]
NOTION_TOKEN      = os.environ.get("NOTION_TOKEN", "")
DIRECTIVES_PAGE   = os.environ.get("NOTION_DIRECTIVES_PAGE_ID", "")

# Files to always read for context
ALWAYS_READ = [
    ".github/workflows/MASTER_CONTROLLER.yml",
    "mycelium/WIRING_MAP.md",
    "data/reminders.json",
    "STATUS.md",
    "README.md",
]

# Workflow files to scan for broken references
WORKFLOW_DIR = ".github/workflows"

# Scripts directory
SCRIPTS_DIR = "mycelium"

# Report output
REPORT_PATH = "data/claude_autonomous_report.json"


# ── GitHub API helpers ──────────────────────────────────────────────────────
def gh_get(path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    r = requests.get(url, headers={"Authorization": f"token {GH_TOKEN}",
                                    "Accept": "application/vnd.github.v3+json"})
    if r.status_code == 200:
        return r.json()
    return None


def gh_get_text(path):
    obj = gh_get(path)
    if obj and "content" in obj:
        try:
            return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
        except Exception:
            return None, None
    return None, None


def gh_list_dir(path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    r = requests.get(url, headers={"Authorization": f"token {GH_TOKEN}",
                                    "Accept": "application/vnd.github.v3+json"})
    if r.status_code == 200:
        return r.json()
    return []


def gh_commit_file(path, content_str, message, sha=None):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers={"Authorization": f"token {GH_TOKEN}",
                                    "Accept": "application/vnd.github.v3+json",
                                    "Content-Type": "application/json"},
                     json=payload)
    return r.status_code in (200, 201), r.json()


# ── Collect repo context ────────────────────────────────────────────────────
def collect_context():
    """Gather everything Claude needs to understand and audit the system."""
    context = {}

    print("📖 Reading core files...")
    for path in ALWAYS_READ:
        text, _ = gh_get_text(path)
        if text:
            context[path] = text[:8000]  # cap per file
            print(f"  ✓ {path}")

    print("📖 Reading workflows...")
    workflows = gh_list_dir(WORKFLOW_DIR)
    wf_summary = []
    for wf in workflows:
        if wf.get("type") == "file" and wf["name"].endswith(".yml"):
            text, _ = gh_get_text(wf["path"])
            if text:
                # Only first 3000 chars per workflow
                context[wf["path"]] = text[:3000]
                wf_summary.append(wf["name"])

    print(f"  ✓ {len(wf_summary)} workflows: {', '.join(wf_summary[:10])}")

    print("📖 Reading script listing...")
    scripts = gh_list_dir(SCRIPTS_DIR)
    script_list = [s["name"] for s in scripts if s.get("type") == "file" and s["name"].endswith(".py")]
    context["_script_inventory"] = json.dumps(script_list)

    # Read a sample of key scripts (most recently relevant ones)
    key_scripts = [
        "mycelium/email_optin_guard.py",
        "mycelium/humanitarian_fork_distributor.py",
        "mycelium/email_gateway.py",
        "mycelium/discord_bridge.py",
        "mycelium/master_controller.py",
        "mycelium/self_healer.py",
    ]
    for sp in key_scripts:
        if sp not in context:
            text, _ = gh_get_text(sp)
            if text:
                context[sp] = text[:4000]
                print(f"  ✓ {sp}")

    print("📖 Reading data files...")
    data_items = gh_list_dir("data")
    for di in data_items:
        if di.get("type") == "file" and di["name"].endswith(".json"):
            text, _ = gh_get_text(di["path"])
            if text and len(text) < 3000:
                context[di["path"]] = text

    # Read DIRECTIVES from Notion if available
    if NOTION_TOKEN and DIRECTIVES_PAGE:
        try:
            nr = requests.get(
                f"https://api.notion.com/v1/blocks/{DIRECTIVES_PAGE}/children",
                headers={"Authorization": f"Bearer {NOTION_TOKEN}",
                         "Notion-Version": "2022-06-28"}
            )
            if nr.status_code == 200:
                blocks = nr.json().get("results", [])
                texts = []
                for b in blocks[:50]:
                    bt = b.get("type", "")
                    rich = b.get(bt, {}).get("rich_text", [])
                    for rt in rich:
                        texts.append(rt.get("plain_text", ""))
                context["notion://DIRECTIVES"] = "\n".join(texts)[:4000]
                print("  ✓ Notion DIRECTIVES")
        except Exception as e:
            print(f"  ⚠ Notion read failed: {e}")

    return context


# ── Build the prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the autonomous self-healing intelligence for the meeko-nerve-center system.

This is an autonomous revenue + humanitarian tech system built by meeko (raccoon energy, ADHD, mission: generate revenue → 70% to PCRF refugee fund).

YOUR JOB — same as Claude in chat:
1. Read the full system context provided
2. Find SPECIFIC problems: bad connections, missing wires, broken references, bugs, env var mismatches, dead code paths, scripts that exist but nothing calls, credentials that exist but nothing uses
3. Generate EXACT file changes to fix what you find
4. Be direct, technical, and specific

CRITICAL RULES:
- Never send cold emails without opt-in guard (email_optin_guard.py must gate all external email)
- Never duplicate sends (check for sent logs)
- Never expose secrets in code
- Self-emails to GMAIL_ADDRESS are fine, bypass opt-in
- All revenue: 70% PCRF, 30% operating costs

RESPONSE FORMAT — return ONLY valid JSON, nothing else:
{
  "timestamp": "ISO8601",
  "findings": [
    {
      "severity": "critical|warning|info",
      "file": "path/to/file",
      "issue": "description of the problem",
      "fix": "description of what needs to change"
    }
  ],
  "file_changes": [
    {
      "path": "mycelium/some_file.py",
      "content": "FULL file content as a string",
      "commit_message": "fix: description of what changed"
    }
  ],
  "summary": "one paragraph: what you found and what you fixed",
  "next_priorities": ["priority 1", "priority 2", "priority 3"]
}

If you find nothing to fix, return file_changes as empty array but always return findings and summary.
Do NOT truncate file content in file_changes — return complete working files.
"""


def build_user_message(context):
    parts = ["Here is the current state of the meeko-nerve-center system. Audit it and return JSON fixes.\n"]
    parts.append(f"Current datetime: {datetime.now(timezone.utc).isoformat()}\n")
    parts.append(f"Total scripts in mycelium/: {len(json.loads(context.get('_script_inventory', '[]')))}\n\n")

    for path, content in context.items():
        if path.startswith("_"):
            continue
        parts.append(f"=== FILE: {path} ===\n{content}\n\n")

    return "".join(parts)[:120000]  # Claude's context limit


# ── Call Claude API ─────────────────────────────────────────────────────────
def call_claude(user_message):
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print("🧠 Calling Claude API...")
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8192,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}]
        },
        timeout=120
    )

    if response.status_code != 200:
        print(f"❌ API error {response.status_code}: {response.text[:500]}")
        sys.exit(1)

    data = response.json()
    raw_text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            raw_text += block["text"]

    print(f"  ✓ Got {len(raw_text)} chars from Claude")
    return raw_text


# ── Parse Claude's response ─────────────────────────────────────────────────
def parse_response(raw_text):
    # Strip markdown fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠ JSON parse error: {e}")
        # Try to extract JSON from within the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        print("❌ Could not parse Claude's response as JSON")
        print(f"Raw: {raw_text[:1000]}")
        return {"findings": [], "file_changes": [], "summary": "Parse error", "next_priorities": []}


# ── Apply fixes ─────────────────────────────────────────────────────────────
def apply_fixes(result):
    changes = result.get("file_changes", [])
    if not changes:
        print("✓ No file changes needed")
        return []

    applied = []
    failed = []

    for change in changes:
        path = change.get("path", "")
        content = change.get("content", "")
        message = change.get("commit_message", f"fix: autonomous update to {path}")

        if not path or not content:
            continue

        print(f"  📝 Committing {path}...")

        # Get current SHA if file exists
        existing = gh_get(path)
        sha = existing.get("sha") if existing else None

        ok, resp = gh_commit_file(path, content, f"[claude-autonomous] {message}", sha)
        if ok:
            applied.append(path)
            print(f"    ✓ Committed: {message}")
        else:
            failed.append(path)
            print(f"    ❌ Failed: {resp.get('message', 'unknown')}")

    return applied, failed


# ── Save report ─────────────────────────────────────────────────────────────
def save_report(result, applied, failed):
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8],
        "findings": result.get("findings", []),
        "summary": result.get("summary", ""),
        "next_priorities": result.get("next_priorities", []),
        "files_changed": applied if isinstance(applied, list) else [],
        "files_failed": failed if isinstance(failed, list) else [],
        "change_count": len(applied) if isinstance(applied, list) else 0
    }

    report_json = json.dumps(report, indent=2)

    # Get SHA of existing report
    existing = gh_get(REPORT_PATH)
    sha = existing.get("sha") if existing else None

    ok, _ = gh_commit_file(
        REPORT_PATH,
        report_json,
        f"[claude-autonomous] report: {report['run_id']} — {len(report['files_changed'])} fixes applied",
        sha
    )
    if ok:
        print(f"  ✓ Report saved to {REPORT_PATH}")
    else:
        print(f"  ⚠ Could not save report")

    return report


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🤖 CLAUDE AUTONOMOUS — Starting system audit")
    print(f"   {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not GH_TOKEN:
        print("❌ GH_PAT or GITHUB_TOKEN not set")
        sys.exit(1)

    # Step 1: Collect context
    context = collect_context()
    print(f"\n✓ Collected context: {len(context)} sections\n")

    # Step 2: Build message
    user_message = build_user_message(context)
    print(f"✓ User message: {len(user_message):,} chars\n")

    # Step 3: Call Claude
    raw_response = call_claude(user_message)

    # Step 4: Parse
    result = parse_response(raw_response)

    # Step 5: Print findings
    findings = result.get("findings", [])
    print(f"\n📋 FINDINGS ({len(findings)}):")
    for f in findings:
        icon = "🔴" if f.get("severity") == "critical" else "🟡" if f.get("severity") == "warning" else "🔵"
        print(f"  {icon} [{f.get('severity','?').upper()}] {f.get('file','?')}")
        print(f"     Issue: {f.get('issue','')}")
        print(f"     Fix:   {f.get('fix','')}")

    # Step 6: Apply fixes
    changes = result.get("file_changes", [])
    print(f"\n🔧 APPLYING {len(changes)} FILE CHANGES...")
    if changes:
        applied, failed = apply_fixes(result)
    else:
        applied, failed = [], []

    # Step 7: Summary
    print(f"\n📊 SUMMARY:")
    print(result.get("summary", "(no summary)"))

    priorities = result.get("next_priorities", [])
    if priorities:
        print(f"\n🎯 NEXT PRIORITIES:")
        for i, p in enumerate(priorities, 1):
            print(f"  {i}. {p}")

    # Step 8: Save report
    print(f"\n💾 Saving report...")
    report = save_report(result, applied, failed)

    print(f"\n✅ DONE — {report['change_count']} fixes applied, {len(failed)} failed")
    print("=" * 60)

    # Exit with error if critical findings exist and no fixes applied
    critical = [f for f in findings if f.get("severity") == "critical"]
    if critical and not applied:
        print(f"⚠ {len(critical)} critical findings but no fixes applied — manual review needed")


if __name__ == "__main__":
    main()
