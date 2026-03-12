#!/usr/bin/env python3
"""
claude_respond.py — Claude responds to GitHub issues that mention @claude

Called by claude_issue_responder.yml workflow.
Uses ANTHROPIC_API_KEY (already in secrets) — no extra tokens.

What it does:
  1. Reads the issue title + body + comment
  2. Reads relevant SolarPunk files (OMNIBUS, data/omnibus_last.json, etc.)
  3. Calls Claude claude-sonnet-4-6 with full SolarPunk context
  4. Posts response as a GitHub comment
  5. If issue asks to fix/build/change code: commits the fix directly

Capabilities:
  - Answer questions about the system
  - Read any file in the repo
  - Write/update engine files and commit them
  - Report on health, revenue, status from data/*.json
  - Debug failing engines
  - Build new engines on request
"""
import os, json, re, sys, base64
import urllib.request, urllib.error
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
REPO         = os.environ.get("REPO", "meekotharaccoon-cell/meeko-nerve-center")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
ISSUE_TITLE  = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY   = os.environ.get("ISSUE_BODY", "")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")
EVENT_NAME   = os.environ.get("EVENT_NAME", "issues")

GH_API  = f"https://api.github.com/repos/{REPO}"
MODEL   = "claude-sonnet-4-6"

# What the human actually asked
TRIGGER = COMMENT_BODY if EVENT_NAME == "issue_comment" else ISSUE_BODY
TRIGGER = TRIGGER.strip()

SYSTEM = """You are Claude operating inside SolarPunk — Meeko's autonomous AI revenue system.

Repo: meekotharaccoon-cell/meeko-nerve-center
Stack: Python engines in mycelium/, orchestrated by OMNIBUS.py (v19, 8 layers)
All runtime state in data/*.json files.
15% of all revenue goes to Palestinian Children's Relief Fund (PCRF, EIN: 93-1057665).

You have been invoked via GitHub Issue. You can:
1. Answer questions about the system
2. Read files from the repo (provided in context)
3. Write/fix engine code and commit it back
4. Debug failing engines
5. Build new engines following the NANO_AGENT base class pattern

When writing code:
- Follow the exact pattern of existing engines
- Use stdlib only (no pip installs in engines unless essential)
- Write data to data/enginename_state.json
- Print status as you go (OMNIBUS reads stdout)
- Handle missing secrets/env vars gracefully (SKIP, don't crash)

When you need to commit a file fix, output a special block at the END of your response:
<commit>
path: mycelium/ENGINE_NAME.py
message: 🔧 fix ENGINE_NAME — description
content:
[FULL FILE CONTENT HERE]
</commit>

You can include multiple <commit> blocks for multiple files.

Be direct, technical, and fast. Meeko is a pro builder. No hand-holding."""


def gh_get(path):
    try:
        req = urllib.request.Request(f"{GH_API}{path}")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Claude/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def gh_post(path, body):
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{GH_API}{path}", data=data, method="POST")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Claude/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  gh_post error: {e}")
        return None


def gh_put_file(path, content_str, message, sha=None):
    """Commit a file to the repo."""
    body = {
        "message": message,
        "content": base64.b64encode(content_str.encode()).decode(),
        "branch": "main",
        "committer": {"name": "SolarPunk Brain", "email": "meekotharaccoon@gmail.com"}
    }
    if sha:
        body["sha"] = sha
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{GH_API}/contents/{path}", data=data, method="PUT")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Claude/1.0")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Commit failed {path}: {e}")
        return None


def get_file_sha(path):
    result = gh_get(f"/contents/{path}")
    return result.get("sha") if isinstance(result, dict) else None


def read_repo_file(path):
    """Read a file from the repo via API."""
    result = gh_get(f"/contents/{path}")
    if isinstance(result, dict) and "content" in result:
        try:
            return base64.b64decode(result["content"]).decode("utf-8", errors="replace")
        except: pass
    return ""


def build_context():
    """Load relevant system files for Claude's context."""
    ctx_files = {}

    # Always load: current system state
    for fname in ["data/omnibus_last.json", "data/resonance_state.json",
                  "data/secrets_checker_state.json", "data/bottleneck_report.json",
                  "data/quick_revenue.json", "data/flywheel_state.json"]:
        content = read_repo_file(fname)
        if content:
            ctx_files[fname] = content[:2000]  # truncate large files

    # Load OMNIBUS manifest (first 100 lines)
    omnibus = read_repo_file("mycelium/OMNIBUS.py")
    if omnibus:
        ctx_files["mycelium/OMNIBUS.py (first 80 lines)"] = "\n".join(omnibus.splitlines()[:80])

    # If the trigger mentions a specific engine, load that file too
    engine_match = re.findall(r'\b([A-Z_]{3,}(?:_ENGINE|_SCANNER|_PUBLISHER|_AGENT|_BUILDER|_CONVERTER|_SPIDER|_DAEMON|_BRIDGE|_RUNNER)?)\b', TRIGGER)
    for engine in set(engine_match):
        path = f"mycelium/{engine}.py"
        content = read_repo_file(path)
        if content:
            ctx_files[path] = content[:3000]

    return ctx_files


def call_claude(prompt, context_files):
    """Call Claude API with full context."""
    # Build context string
    ctx_str = ""
    for fname, content in context_files.items():
        ctx_str += f"\n\n=== {fname} ===\n{content}"

    full_prompt = f"""Issue #{ISSUE_NUMBER}: {ISSUE_TITLE}

Request: {TRIGGER}

Current system files for context:{ctx_str}

Please respond to this issue. If a code fix is needed, include a <commit> block at the end."""

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 4096,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": full_prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
        return data["content"][0]["text"]


def parse_commits(response_text):
    """Extract <commit> blocks from Claude's response."""
    commits = []
    pattern = r'<commit>\s*path:\s*(.+?)\s*message:\s*(.+?)\s*content:\s*(.*?)</commit>'
    matches = re.findall(pattern, response_text, re.DOTALL)
    for path, message, content in matches:
        commits.append({
            "path": path.strip(),
            "message": message.strip(),
            "content": content.strip()
        })
    return commits


def strip_commits(response_text):
    """Remove <commit> blocks from response before posting as comment."""
    return re.sub(r'<commit>.*?</commit>', '', response_text, flags=re.DOTALL).strip()


def post_comment(body):
    result = gh_post(f"/issues/{ISSUE_NUMBER}/comments", {"body": body})
    if result and "id" in result:
        print(f"  Posted comment #{result['id']}")
        return True
    return False


def run():
    if not API_KEY:
        print("SKIP: ANTHROPIC_API_KEY not set")
        post_comment("❌ ANTHROPIC_API_KEY not configured in repo secrets.")
        sys.exit(0)

    if not TRIGGER or "@claude" not in TRIGGER.lower():
        print("No @claude mention found — skipping")
        sys.exit(0)

    print(f"Issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    print(f"Trigger: {TRIGGER[:100]}...")

    # Build context
    print("Loading repo context...")
    context_files = build_context()
    print(f"  Loaded {len(context_files)} files")

    # Call Claude
    print("Calling Claude...")
    try:
        response = call_claude(TRIGGER, context_files)
    except Exception as e:
        error_msg = f"❌ Claude API error: {e}"
        print(error_msg)
        post_comment(error_msg)
        sys.exit(1)

    # Parse any commits
    commits = parse_commits(response)
    clean_response = strip_commits(response)

    # Post the response as a comment
    comment_body = f"🤖 **Claude responding to #{ISSUE_NUMBER}**\n\n{clean_response}"
    if commits:
        commit_summary = "\n".join(f"- `{c['path']}`" for c in commits)
        comment_body += f"\n\n---\n📝 **Committing {len(commits)} file(s):**\n{commit_summary}"

    post_comment(comment_body)

    # Execute commits
    for c in commits:
        print(f"  Committing {c['path']}...")
        sha = get_file_sha(c["path"])
        result = gh_put_file(c["path"], c["content"], c["message"], sha)
        if result:
            commit_sha = result.get("commit", {}).get("sha", "?")[:8]
            print(f"    OK: {commit_sha}")
            # Post a follow-up comment with the commit link
            commit_url = result.get("commit", {}).get("html_url", "")
            gh_post(f"/issues/{ISSUE_NUMBER}/comments", {
                "body": f"✅ Committed `{c['path']}` — [{commit_sha}]({commit_url})"
            })
        else:
            print(f"    FAILED: {c['path']}")
            gh_post(f"/issues/{ISSUE_NUMBER}/comments", {
                "body": f"❌ Failed to commit `{c['path']}` — check Actions logs"
            })

    print(f"Done. {len(commits)} commits, 1 comment posted.")


if __name__ == "__main__":
    run()
