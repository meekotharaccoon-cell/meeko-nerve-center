#!/usr/bin/env python3
"""
claude_brain.py — Claude with real tool use on GitHub

CAPABILITIES (all new vs claude_respond.py):
  Tools Claude can call during a response:
    read_file         — read any file in the repo
    list_directory    — browse repo structure
    write_file        — commit any file to main
    run_engine        — execute a mycelium engine in CI and return output
    create_issue      — open a new GitHub issue (self-tasking)
    close_issue       — close a resolved issue
    add_label         — label an issue or PR
    post_comment      — post to any issue/PR
    search_code       — search repo code via GitHub API
    get_pr_diff       — read a PR's file changes
    get_recent_commits — get git log
    get_workflow_runs — check recent CI run status
    web_fetch         — fetch a URL (for research, link checking)

  Modes:
    respond           — answer a specific @claude mention
    proactive_analysis — scheduled daily: analyze state, open actionable issues
    fix_failing_engines — find all failing engines and fix them
    build_engine      — build a new engine from spec

  Context loaded automatically:
    - data/omnibus_last.json (full system state)
    - data/omnibus_history.json (last 5 cycles)
    - mycelium/OMNIBUS.py (first 100 lines)
    - Any engine file mentioned in the trigger
    - PR diff (when triggered from PR)
    - Recent git log
    - Recent workflow runs

Triggers from claude_brain.yml:
  - @claude in any issue/comment/PR
  - Scheduled 8am UTC daily
  - Manual workflow_dispatch with custom prompt
"""
import os, json, re, sys, base64, subprocess, time
import urllib.request, urllib.error
from pathlib import Path

# ── Environment ──────────────────────────────────────────────────────────────
API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
REPO         = os.environ.get("REPO", "meekotharaccoon-cell/meeko-nerve-center")
EVENT_NAME   = os.environ.get("EVENT_NAME", "workflow_dispatch")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
ISSUE_TITLE  = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY   = os.environ.get("ISSUE_BODY", "")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")
PR_NUMBER    = os.environ.get("PR_NUMBER", "")
PR_TITLE     = os.environ.get("PR_TITLE", "")
PR_BODY      = os.environ.get("PR_BODY", "")
DISPATCH_PROMPT = os.environ.get("DISPATCH_PROMPT", "")
DISPATCH_MODE   = os.environ.get("DISPATCH_MODE", "respond")
GITHUB_SHA   = os.environ.get("GITHUB_SHA", "")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "")

GH_API = f"https://api.github.com/repos/{REPO}"
MODEL  = "claude-sonnet-4-6"

# ── Determine trigger ─────────────────────────────────────────────────────────
def get_mode_and_trigger():
    if EVENT_NAME == "schedule":
        return "proactive_analysis", "Daily scheduled analysis — examine system state and open actionable tasks."
    if EVENT_NAME == "workflow_dispatch":
        return DISPATCH_MODE or "respond", DISPATCH_PROMPT or "Analyze the system and report status."
    if EVENT_NAME in ("issue_comment", "pull_request_review_comment"):
        body = COMMENT_BODY or ""
        num  = ISSUE_NUMBER or PR_NUMBER
        return "respond", body
    if EVENT_NAME == "issues":
        return "respond", (ISSUE_BODY or "")
    if EVENT_NAME == "pull_request":
        return "respond", (PR_BODY or f"New PR: {PR_TITLE}")
    return "respond", ""

MODE, TRIGGER = get_mode_and_trigger()
TRIGGER_NUM = ISSUE_NUMBER or PR_NUMBER or "0"

# ── GitHub API helpers ────────────────────────────────────────────────────────
def gh(path, method="GET", body=None, raw=False):
    try:
        url  = f"{GH_API}{path}" if path.startswith("/") else path
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Brain/2.0")
        if body:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=20) as r:
            content = r.read()
            return content if raw else json.loads(content)
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"  GH {method} {path} -> {e.code}: {err}")
        return {"error": str(e.code), "detail": err}
    except Exception as e:
        return {"error": str(e)}


def read_file(path):
    result = gh(f"/contents/{path}")
    if isinstance(result, dict) and "content" in result:
        try:
            return base64.b64decode(result["content"]).decode("utf-8", errors="replace"), result.get("sha")
        except: pass
    return None, None


def write_file(path, content, message, sha=None):
    body = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main",
        "committer": {"name": "SolarPunk Brain", "email": "meekotharaccoon@gmail.com"}
    }
    if sha: body["sha"] = sha
    return gh(f"/contents/{path}", "PUT", body)


def list_directory(path):
    result = gh(f"/contents/{path}")
    if isinstance(result, list):
        return [{"name": f["name"], "type": f["type"], "size": f.get("size", 0)} for f in result]
    return []


def post_comment(number, body):
    result = gh(f"/issues/{number}/comments", "POST", {"body": body})
    return result.get("id") if isinstance(result, dict) else None


def create_issue(title, body, labels=None):
    payload = {"title": title, "body": body}
    if labels: payload["labels"] = labels
    return gh("/issues", "POST", payload)


def close_issue(number):
    return gh(f"/issues/{number}", "PATCH", {"state": "closed"})


def add_label(number, labels):
    return gh(f"/issues/{number}/labels", "POST", {"labels": labels})


def search_code(query):
    try:
        url = f"https://api.github.com/search/code?q={urllib.parse.quote(query)}+repo:{REPO}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Brain/2.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            items = data.get("items", [])[:5]
            return [{"path": i["path"], "url": i["html_url"]} for i in items]
    except Exception as e:
        return [{"error": str(e)}]


def get_pr_diff(pr_num):
    try:
        req = urllib.request.Request(f"{GH_API}/pulls/{pr_num}/files")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Brain/2.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            files = json.loads(r.read())
            return [{"filename": f["filename"], "status": f["status"],
                     "additions": f["additions"], "deletions": f["deletions"],
                     "patch": f.get("patch", "")[:500]} for f in files[:10]]
    except Exception as e:
        return [{"error": str(e)}]


def get_recent_commits(n=10):
    result = gh(f"/commits?per_page={n}")
    if isinstance(result, list):
        return [{"sha": c["sha"][:8], "message": c["commit"]["message"][:80],
                 "author": c["commit"]["author"]["name"],
                 "date": c["commit"]["author"]["date"][:10]} for c in result]
    return []


def get_workflow_runs(n=5):
    result = gh(f"/actions/runs?per_page={n}")
    if isinstance(result, dict):
        runs = result.get("workflow_runs", [])
        return [{"id": r["id"], "name": r["name"], "status": r["status"],
                 "conclusion": r["conclusion"], "created_at": r["created_at"][:16]} for r in runs]
    return []


def run_engine(engine_name):
    """Actually execute a mycelium engine in CI and capture output."""
    script = Path(f"mycelium/{engine_name}.py")
    if not script.exists():
        return f"Engine {engine_name}.py not found"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=60,
            cwd=Path.cwd(), env=dict(os.environ)
        )
        out = (result.stdout or "")[-2000:]
        err = (result.stderr or "")[-500:]
        return f"Exit: {result.returncode}\nStdout:\n{out}\nStderr:\n{err}"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: {engine_name} exceeded 60s"
    except Exception as e:
        return f"ERROR: {e}"


def web_fetch(url):
    """Fetch a URL for research."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 SolarPunk-Brain/2.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")
            # Strip HTML tags crudely
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content)
            return content[:3000]
    except Exception as e:
        return f"Fetch error: {e}"


# ── Tool dispatch ─────────────────────────────────────────────────────────────
import urllib.parse

def dispatch_tool(name, input_data):
    """Execute a tool call from Claude and return the result."""
    print(f"  🔧 Tool: {name}({list(input_data.keys())})")
    try:
        if name == "read_file":
            content, sha = read_file(input_data["path"])
            if content:
                return {"content": content[:6000], "sha": sha, "truncated": len(content) > 6000}
            return {"error": f"File not found: {input_data['path']}"}

        elif name == "list_directory":
            items = list_directory(input_data.get("path", ""))
            return {"items": items}

        elif name == "write_file":
            path    = input_data["path"]
            content = input_data["content"]
            message = input_data.get("message", f"🔧 update {path} via Claude Brain")
            _, sha  = read_file(path)
            result  = write_file(path, content, message, sha)
            if isinstance(result, dict) and "commit" in result:
                commit_sha = result["commit"]["sha"][:8]
                commit_url = result["commit"]["html_url"]
                return {"success": True, "sha": commit_sha, "url": commit_url}
            return {"success": False, "error": str(result)}

        elif name == "run_engine":
            output = run_engine(input_data["engine"])
            return {"output": output}

        elif name == "create_issue":
            result = create_issue(input_data["title"], input_data["body"],
                                  input_data.get("labels", []))
            if isinstance(result, dict) and "number" in result:
                return {"number": result["number"], "url": result["html_url"]}
            return {"error": str(result)}

        elif name == "close_issue":
            close_issue(input_data["number"])
            return {"closed": True}

        elif name == "add_label":
            add_label(input_data["number"], input_data["labels"])
            return {"added": True}

        elif name == "post_comment":
            cid = post_comment(input_data["number"], input_data["body"])
            return {"comment_id": cid}

        elif name == "search_code":
            return {"results": search_code(input_data["query"])}

        elif name == "get_pr_diff":
            return {"files": get_pr_diff(input_data["pr_number"])}

        elif name == "get_recent_commits":
            return {"commits": get_recent_commits(input_data.get("n", 10))}

        elif name == "get_workflow_runs":
            return {"runs": get_workflow_runs(input_data.get("n", 5))}

        elif name == "web_fetch":
            return {"content": web_fetch(input_data["url"])}

        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        return {"error": str(e)}


# ── Tool definitions for the API ──────────────────────────────────────────────
TOOLS = [
    {
        "name": "read_file",
        "description": "Read any file from the repo. Use for engines, data files, configs.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Repo-relative path e.g. mycelium/ENGINE.py"}},
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files in a repo directory.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path e.g. mycelium or data"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write (create or update) a file in the repo and commit it to main.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"},
                "message": {"type": "string", "description": "Commit message with emoji prefix"}
            },
            "required": ["path", "content", "message"]
        }
    },
    {
        "name": "run_engine",
        "description": "Execute a mycelium engine in CI and return its stdout/stderr. Use to test or debug.",
        "input_schema": {
            "type": "object",
            "properties": {"engine": {"type": "string", "description": "Engine name without .py e.g. RESONANCE_ENGINE"}},
            "required": ["engine"]
        }
    },
    {
        "name": "create_issue",
        "description": "Create a new GitHub issue. Use for self-tasking: queue work for future cycles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":  {"type": "string"},
                "body":   {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "body"]
        }
    },
    {
        "name": "close_issue",
        "description": "Close a GitHub issue when the task is complete.",
        "input_schema": {
            "type": "object",
            "properties": {"number": {"type": "integer"}},
            "required": ["number"]
        }
    },
    {
        "name": "add_label",
        "description": "Add labels to an issue or PR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "number": {"type": "integer"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["number", "labels"]
        }
    },
    {
        "name": "post_comment",
        "description": "Post a comment on any issue or PR by number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "number": {"type": "integer"},
                "body":   {"type": "string"}
            },
            "required": ["number", "body"]
        }
    },
    {
        "name": "search_code",
        "description": "Search the repo codebase for a pattern or keyword.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "get_pr_diff",
        "description": "Get the file changes in a pull request.",
        "input_schema": {
            "type": "object",
            "properties": {"pr_number": {"type": "integer"}},
            "required": ["pr_number"]
        }
    },
    {
        "name": "get_recent_commits",
        "description": "Get recent git commits.",
        "input_schema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 10}},
            "required": []
        }
    },
    {
        "name": "get_workflow_runs",
        "description": "Get recent GitHub Actions workflow run statuses.",
        "input_schema": {
            "type": "object",
            "properties": {"n": {"type": "integer", "default": 5}},
            "required": []
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch a URL for research, link checking, or external data.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    }
]


# ── System prompt ─────────────────────────────────────────────────────────────
def build_system(mode):
    base = """You are Claude — the brain of SolarPunk, Meeko's autonomous AI revenue system.

Repo: meekotharaccoon-cell/meeko-nerve-center
Stack: Python engines in mycelium/, orchestrated by OMNIBUS.py (v19, 8 execution layers)
Runtime state: all in data/*.json (omnibus_last.json is the canonical system state)
Mission: generate revenue autonomously, 15% hardcoded to Palestinian Children's Relief Fund (PCRF)

You have REAL TOOLS. Use them. Don't guess — read the actual files.

TOOL USE GUIDELINES:
- Always read_file before writing a file (get current content + SHA)
- list_directory to explore before reading
- run_engine to verify a fix actually works before declaring success
- create_issue to queue tasks for yourself on future cycles (self-tasking)
- close_issue when you've resolved the problem
- write_file to commit fixes, new engines, config changes — directly to main

CODING RULES (when writing engines):
- Use Python stdlib only (no pip installs unless absolutely necessary)
- Write state to data/enginename_state.json
- Print progress as you go (OMNIBUS reads stdout)
- Handle missing secrets/env vars gracefully: print SKIP, return cleanly
- Follow NANO_AGENT base class pattern (read mycelium/NANO_AGENT.py first)
- Commit message emoji: 🔧 fixes · 👁️ new engines · 🌟 OMNIBUS bumps

Be fast and direct. Meeko is a pro builder. One response = complete work, not planning."""

    if mode == "proactive_analysis":
        return base + """

CURRENT MODE: PROACTIVE ANALYSIS (daily scheduled)
Your job:
1. Read data/omnibus_last.json — check health, failures, missing secrets, resonance
2. Read data/omnibus_history.json — identify trends (health going up or down?)
3. Check recent workflow runs — any failures?
4. Identify the TOP 3 highest-impact actions to take RIGHT NOW
5. For each action:
   a. If it's a code fix: fix it (read → fix → write_file)
   b. If it's a task for Meeko: create_issue with clear title + steps
   c. If it's something the system can do autonomously: do it
6. Post a summary comment on issue #1 (or create a daily status issue)

Focus on: revenue blockers > health > distribution > self-improvement"""

    if mode == "fix_failing_engines":
        return base + """

CURRENT MODE: FIX FAILING ENGINES
1. Read data/omnibus_last.json → get engines_failed list
2. For each failing engine:
   a. read_file to see the current code
   b. run_engine to see the actual error
   c. Fix the bug and write_file
   d. run_engine again to verify fix
3. Report results"""

    return base  # respond mode


# ── Context loader ────────────────────────────────────────────────────────────
def load_initial_context():
    """Load always-needed context before calling Claude."""
    ctx = {}

    # Core state files
    for fname in ["data/omnibus_last.json", "data/resonance_state.json",
                  "data/quick_revenue.json", "data/secrets_checker_state.json"]:
        content, _ = read_file(fname)
        if content: ctx[fname] = content[:3000]

    # OMNIBUS header
    omnibus, _ = read_file("mycelium/OMNIBUS.py")
    if omnibus: ctx["mycelium/OMNIBUS.py (header)"] = "\n".join(omnibus.splitlines()[:100])

    # Recent commits
    commits = get_recent_commits(5)
    if commits: ctx["recent_commits"] = json.dumps(commits, indent=2)

    # If triggered from a PR, load diff
    if PR_NUMBER:
        diff = get_pr_diff(int(PR_NUMBER))
        if diff: ctx[f"PR #{PR_NUMBER} diff"] = json.dumps(diff, indent=2)[:3000]

    # If trigger mentions specific engines, load them
    all_text = " ".join([TRIGGER, ISSUE_TITLE, PR_TITLE])
    engine_names = re.findall(r'\b([A-Z][A-Z_]{2,})\b', all_text)
    for name in set(engine_names):
        path = f"mycelium/{name}.py"
        content, _ = read_file(path)
        if content: ctx[path] = content[:4000]

    return ctx


# ── Main agentic loop ─────────────────────────────────────────────────────────
def run():
    if not API_KEY:
        print("FATAL: ANTHROPIC_API_KEY not set")
        if TRIGGER_NUM != "0":
            post_comment(TRIGGER_NUM, "❌ `ANTHROPIC_API_KEY` not in repo secrets.")
        sys.exit(0)

    # In respond mode, require @claude mention
    if MODE == "respond" and "@claude" not in TRIGGER.lower() and EVENT_NAME not in ("workflow_dispatch",):
        print("No @claude mention — skip")
        sys.exit(0)

    print(f"Mode: {MODE} | Event: {EVENT_NAME} | Trigger: {TRIGGER_NUM}")
    print(f"Trigger text: {TRIGGER[:120]}")

    # Load initial context
    print("Loading context...")
    ctx = load_initial_context()
    ctx_str = "\n\n".join(f"=== {k} ===\n{v}" for k, v in ctx.items())

    # Build initial user message
    if MODE == "proactive_analysis":
        user_msg = f"Run your daily proactive analysis. Context loaded:\n{ctx_str}"
    elif TRIGGER:
        user_msg = f"Issue/PR #{TRIGGER_NUM}: {ISSUE_TITLE or PR_TITLE}\n\nRequest: {TRIGGER}\n\nContext:\n{ctx_str}"
    else:
        user_msg = f"Dispatch: {DISPATCH_PROMPT}\n\nContext:\n{ctx_str}"

    # Agentic tool-use loop
    messages = [{"role": "user", "content": user_msg}]
    system   = build_system(MODE)
    final_response = None
    commits_made = []
    issues_created = []
    max_turns = 20  # safety cap

    for turn in range(max_turns):
        print(f"  Turn {turn+1}/{max_turns}...")

        payload = json.dumps({
            "model":      MODEL,
            "max_tokens": 8096,
            "system":     system,
            "tools":      TOOLS,
            "messages":   messages,
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key":         API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"  API error turn {turn+1}: {e}")
            break

        stop_reason = data.get("stop_reason")
        content     = data.get("content", [])

        # Collect text for final response
        text_parts = [b["text"] for b in content if b.get("type") == "text"]
        if text_parts:
            final_response = "\n".join(text_parts)

        # Track what was done
        for block in content:
            if block.get("type") == "tool_use":
                result = block.get("input", {})
                if block["name"] == "write_file":
                    commits_made.append(result.get("path", "?"))
                elif block["name"] == "create_issue":
                    pass  # tracked after dispatch

        if stop_reason == "end_turn":
            print(f"  Done after {turn+1} turns")
            break

        if stop_reason == "tool_use":
            # Execute all tool calls
            tool_results = []
            for block in content:
                if block.get("type") == "tool_use":
                    result = dispatch_tool(block["name"], block.get("input", {}))

                    # Track issue creation results
                    if block["name"] == "create_issue" and isinstance(result, dict) and "number" in result:
                        issues_created.append(result)

                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block["id"],
                        "content":     json.dumps(result)
                    })

            # Add assistant turn + tool results to messages
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user",      "content": tool_results})
        else:
            print(f"  Unexpected stop_reason: {stop_reason}")
            break

    # ── Post final response ──────────────────────────────────────────────────
    if not final_response:
        final_response = "✅ Task complete. No text response generated."

    # Build summary footer
    footer_parts = []
    if commits_made:
        footer_parts.append(f"📝 **Files committed:** {', '.join(f'`{p}`' for p in commits_made)}")
    if issues_created:
        for iss in issues_created:
            footer_parts.append(f"🎯 **Task queued:** #{iss['number']} — {iss.get('url','')}")
    footer = "\n\n---\n" + "\n".join(footer_parts) if footer_parts else ""

    comment_body = f"🤖 **Claude Brain** (mode: `{MODE}`)\n\n{final_response}{footer}"

    # Where to post
    if TRIGGER_NUM and TRIGGER_NUM != "0":
        post_comment(int(TRIGGER_NUM), comment_body)
        print(f"  Posted to #{TRIGGER_NUM}")
    elif MODE == "proactive_analysis":
        # Create a daily status issue
        today = time.strftime("%Y-%m-%d")
        result = create_issue(
            f"🌱 Daily Analysis — {today}",
            comment_body,
            labels=["automated", "analysis"]
        )
        if isinstance(result, dict) and "number" in result:
            print(f"  Created daily analysis issue #{result['number']}")
    else:
        print(f"  Response (no issue to post to):\n{final_response[:500]}")

    print(f"Done. Turns: {turn+1} | Commits: {len(commits_made)} | Issues: {len(issues_created)}")


if __name__ == "__main__":
    run()
