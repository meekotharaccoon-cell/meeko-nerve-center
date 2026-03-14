# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
DESKTOP_DAEMON — runs locally on Meeko's desktop, always on, always watching.

This IS SolarPunk on your machine. It:
  1. Watches data/claude_tasks_queue.json for tasks queued by any engine
  2. Calls Anthropic API directly (no browser scraping needed)
  3. Has full SolarPunk system context injected into every call
  4. Can execute desktop actions via subprocess/PowerShell
  5. Commits results back to the repo automatically
  6. Runs itself as a Windows scheduled task on boot
  7. Integrates with OMNIBUS — reports health, syncs state

Start it:
  python mycelium/DESKTOP_DAEMON.py

Or install as auto-start:
  python mycelium/DESKTOP_DAEMON.py --install

To queue a task from any engine:
  from DESKTOP_DAEMON import queue_task
  queue_task("Write a grant email to Mozilla", priority=1)
"""
import os, sys, json, time, subprocess, argparse
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ── PATHS ──────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
DATA       = ROOT / "data"
DATA.mkdir(exist_ok=True)

QUEUE_FILE   = DATA / "claude_tasks_queue.json"
RESULTS_FILE = DATA / "claude_task_results.json"
DAEMON_STATE = DATA / "desktop_daemon_state.json"
DAEMON_LOG   = DATA / "desktop_daemon_log.json"

# ── CONFIG ─────────────────────────────────────────────────────────────────
POLL_INTERVAL  = 15          # seconds between queue checks
MAX_LOG_LINES  = 200
MODEL          = "claude-haiku-4-5-20251001"   # fast + cheap for most tasks
MODEL_HEAVY    = "claude-sonnet-4-6"            # for tasks flagged heavy=True
API_KEY        = os.environ.get("ANTHROPIC_API_KEY", "").strip()

# ── SOLARPUNK SYSTEM CONTEXT ───────────────────────────────────────────────
SYSTEM_CONTEXT = """
You are Claude running as part of SolarPunk — Meeko's autonomous AI system.

SYSTEM FACTS:
- Repo: meekotharaccoon-cell/meeko-nerve-center (GitHub)
- Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center
- 76 Python engines across 8 layers (L0-L7), orchestrated by OMNIBUS.py v16
- Runs 4x/day on GitHub Actions free tier
- 15% of all revenue → Palestinian Children's Relief Fund (PCRF, EIN 93-1057665)
- Stack: Python, GitHub Actions, Anthropic API, Gmail SMTP, GitHub Pages
- Local: Ollama running mistral/codellama/llama3.2 at localhost:11434
- Desktop: Windows 10/11, Brave browser, PowerShell available

KEY ENGINES:
- OMNIBUS.py         — master orchestrator (v16, 8 layers)
- REVENUE_FLYWHEEL   — routes money, 15% to Gaza hardcoded
- EMAIL_AGENT_EXCHANGE — pay-per-task AI via email
- SELF_BUILDER       — writes new engines autonomously
- DEV_TO_PUBLISHER   — publishes to dev.to daily
- DESKTOP_DAEMON     — that's you, running locally
- CLAUDE_BRIDGE      — browser automation via CDP port 9222

DATA FILES (all in data/):
- omnibus_last.json       — last full system run
- health_report.json      — system health score
- claude_tasks_queue.json — YOUR incoming task queue
- claude_task_results.json — YOUR completed results
- memory_palace.json      — system memory

You are operating as an autonomous local agent. Be direct, take action, produce outputs.
When asked to write code, write complete working code. When asked to draft something, write it fully.
When asked to analyze data, analyze it and give concrete recommendations.
Always stay mission-aligned: autonomous revenue + Palestine solidarity.
"""


# ── HELPERS ────────────────────────────────────────────────────────────────
def log(msg, level="INFO"):
    ts   = datetime.now(timezone.utc).isoformat()[:19]
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        logs = json.loads(DAEMON_LOG.read_text()) if DAEMON_LOG.exists() else []
        logs.append({"ts": ts, "level": level, "msg": msg})
        DAEMON_LOG.write_text(json.dumps(logs[-MAX_LOG_LINES:], indent=2))
    except:
        pass


def rj(path, fallback=None):
    try:
        return json.loads(Path(path).read_text())
    except:
        return fallback if fallback is not None else {}


def wj(path, data):
    Path(path).write_text(json.dumps(data, indent=2))


def load_queue():
    q = rj(QUEUE_FILE, [])
    return q if isinstance(q, list) else []


def save_queue(q):
    wj(QUEUE_FILE, q)


def load_results():
    r = rj(RESULTS_FILE, [])
    return r if isinstance(r, list) else []


def load_state():
    return rj(DAEMON_STATE, {
        "status": "never_started",
        "tasks_completed": 0,
        "started_at": None,
        "last_poll": None,
        "errors": 0
    })


def save_state(s):
    wj(DAEMON_STATE, s)


# ── SOLARPUNK CONTEXT LOADER ───────────────────────────────────────────────
def build_context():
    """Inject live SolarPunk state into every Claude call."""
    extra = []

    last = rj(DATA / "omnibus_last.json", {})
    if last:
        extra.append(f"LAST OMNIBUS: cycle={last.get('cycle','?')}, health={last.get('health_score','?')}/100")

    mem = rj(DATA / "memory_palace.json", {})
    if mem.get("lessons"):
        extra.append(f"RECENT LESSONS: {'; '.join(str(l) for l in mem['lessons'][:3])}")

    fly = rj(DATA / "flywheel_state.json", {})
    if fly.get("total_routed_usd"):
        extra.append(f"TOTAL ROUTED TO GAZA: ${fly['total_routed_usd']:.2f}")

    if extra:
        return SYSTEM_CONTEXT + "\nLIVE STATE:\n" + "\n".join(extra)
    return SYSTEM_CONTEXT


# ── CLAUDE API ─────────────────────────────────────────────────────────────
def call_claude(prompt, heavy=False, conversation_history=None):
    if not API_KEY:
        return None, "ANTHROPIC_API_KEY not set"

    model    = MODEL_HEAVY if heavy else MODEL
    messages = (conversation_history or []) + [{"role": "user", "content": prompt}]

    try:
        payload = json.dumps({
            "model":      model,
            "max_tokens": 4096,
            "system":     build_context(),
            "messages":   messages
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
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
            return data["content"][0]["text"], None

    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)


# ── DESKTOP ACTIONS ────────────────────────────────────────────────────────
def run_powershell(cmd, timeout=30):
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return "", str(e)


def open_in_brave(url):
    paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            subprocess.Popen([p, url])
            return True
    return False


def git_commit_and_push(message):
    try:
        subprocess.run(["git", "-C", str(ROOT), "add", "data/"], capture_output=True)
        r = subprocess.run(
            ["git", "-C", str(ROOT), "commit", "-m", message],
            capture_output=True, text=True
        )
        if "nothing to commit" not in r.stdout:
            subprocess.run(["git", "-C", str(ROOT), "push", "origin", "main"], capture_output=True)
        return True
    except Exception as e:
        log(f"Git push failed: {e}", "WARN")
        return False


# ── TASK DISPATCH ──────────────────────────────────────────────────────────
def execute_task(task):
    """
    Execute a single task. Supported task shapes:
      { prompt, heavy, action, action_data, conversation_history }

    action values:
      None         — Claude call, return text
      "write_file" — Claude call, write result to action_data.path
      "powershell" — Claude call, run result as PS command
      "open_url"   — open action_data.url in Brave (no Claude call)
      "git_push"   — Claude call, then git push results
    """
    task_id = task.get("id", f"t_{int(time.time())}")
    prompt  = task.get("prompt", "")
    heavy   = task.get("heavy", False)
    action  = task.get("action", None)
    history = task.get("conversation_history", None)

    log(f"Executing [{task_id}]: {prompt[:70]}")

    result_data = {
        "id":     task_id,
        "prompt": prompt,
        "ts":     datetime.now(timezone.utc).isoformat(),
        "source": task.get("source", "unknown")
    }

    # Pure desktop action
    if action == "open_url" and not prompt:
        url = task.get("action_data", {}).get("url", "")
        ok  = open_in_brave(url)
        result_data.update({"status": "completed", "result": f"Opened {url}: {ok}"})
        return result_data

    if action == "powershell" and not prompt:
        cmd = task.get("action_data", {}).get("command", "")
        out, err = run_powershell(cmd)
        result_data.update({"status": "completed", "result": out, "error": err})
        return result_data

    # Claude call
    if not prompt:
        result_data.update({"status": "failed", "error": "no prompt"})
        return result_data

    response, error = call_claude(prompt, heavy=heavy, conversation_history=history)

    if error:
        log(f"Task {task_id} FAILED: {error}", "ERROR")
        result_data.update({"status": "failed", "error": error})
        return result_data

    result_data["result"] = response
    result_data["model"]  = MODEL_HEAVY if heavy else MODEL

    # Post-response actions
    if action == "write_file":
        fpath = task.get("action_data", {}).get("path", "")
        if fpath:
            try:
                Path(fpath).write_text(response)
                result_data["file_written"] = fpath
                log(f"Written to {fpath}")
            except Exception as e:
                result_data["file_error"] = str(e)

    elif action == "powershell":
        out, err = run_powershell(response)
        result_data.update({"ps_output": out, "ps_error": err})

    elif action == "git_push":
        git_commit_and_push(f"daemon: {task_id} — {prompt[:50]}")

    result_data["status"] = "completed"
    log(f"Task {task_id} done → {response[:80]}")
    return result_data


# ── MAIN LOOP ──────────────────────────────────────────────────────────────
def run_loop():
    state = load_state()
    state.update({"status": "running", "started_at": datetime.now(timezone.utc).isoformat()})
    save_state(state)

    log("DESKTOP_DAEMON started. SolarPunk is local and alive.")
    if not API_KEY:
        log("WARNING: ANTHROPIC_API_KEY not in environment.", "WARN")
        log("  Windows: $env:ANTHROPIC_API_KEY = 'sk-ant-...'")
        log("  Or add to repo root .env file")

    polls = 0
    while True:
        try:
            state["last_poll"] = datetime.now(timezone.utc).isoformat()

            queue   = load_queue()
            pending = sorted(
                [t for t in queue if t.get("status") == "pending"],
                key=lambda t: t.get("priority", 5)
            )

            if pending:
                results = load_results()
                for task in pending:
                    result = execute_task(task)
                    results.append(result)
                    for q in queue:
                        if q.get("id") == task.get("id"):
                            q["status"]       = result["status"]
                            q["completed_at"] = result["ts"]
                            break
                    state["tasks_completed"] = state.get("tasks_completed", 0) + 1

                save_queue(queue)
                wj(RESULTS_FILE, results[-100:])
                save_state(state)
                git_commit_and_push(f"daemon: completed {len(pending)} tasks")

            else:
                polls += 1
                state["polls"] = polls
                save_state(state)
                # Every 10 polls (~2.5 min), do a background health check
                if polls % 10 == 0:
                    _idle_health_check()

        except KeyboardInterrupt:
            log("DESKTOP_DAEMON stopped.")
            state["status"] = "stopped"
            save_state(state)
            break
        except Exception as e:
            state["errors"] = state.get("errors", 0) + 1
            log(f"Loop error: {e}", "ERROR")
            save_state(state)

        time.sleep(POLL_INTERVAL)


def _idle_health_check():
    last   = rj(DATA / "omnibus_last.json", {})
    health = last.get("health_score", 100)
    if health < 60:
        log(f"Health {health}/100 — requesting advisory", "WARN")
        resp, _ = call_claude(
            f"SolarPunk health is {health}/100. Give me 3 specific fixes in under 150 words, action-focused."
        )
        if resp:
            (DATA / "health_advisory.txt").write_text(
                f"[{datetime.now().isoformat()}]\n{resp}"
            )
            log("Advisory written to data/health_advisory.txt")


# ── PUBLIC API FOR OTHER ENGINES ───────────────────────────────────────────
def queue_task(prompt, priority=5, heavy=False, action=None,
               action_data=None, source=None, task_id=None):
    """
    Add a task to the daemon queue from any SolarPunk engine.

    Examples:
        from DESKTOP_DAEMON import queue_task

        # Ask Claude something
        queue_task("Draft a grant email to Mozilla", priority=1, source="GRANT_HUNTER")

        # Open a URL in Brave
        queue_task("", action="open_url",
                   action_data={"url": "https://gumroad.com/new"},
                   source="REVENUE_FLYWHEEL")

        # Write Claude's response to a file
        queue_task("Generate 10 product ideas for SolarPunk",
                   action="write_file",
                   action_data={"path": "data/product_ideas.txt"})
    """
    queue = load_queue()
    tid   = task_id or f"{(source or 'engine')}_{int(time.time())}"
    queue.append({
        "id":          tid,
        "prompt":      prompt,
        "priority":    priority,
        "heavy":       heavy,
        "action":      action,
        "action_data": action_data,
        "source":      source or "unknown",
        "status":      "pending",
        "queued_at":   datetime.now(timezone.utc).isoformat()
    })
    save_queue(queue)
    return tid


# ── WINDOWS AUTO-START INSTALL ─────────────────────────────────────────────
def install_autostart():
    script_path = Path(__file__).resolve()
    python_exe  = sys.executable
    env_file    = ROOT / ".env"

    env_cmd = ""
    if env_file.exists():
        env_cmd = (
            f'Get-Content "{env_file}" | ForEach-Object '
            '{ if ($_ -match "^([^#][^=]+)=(.+)$") '
            '{ [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process") } }; '
        )

    ps_launch = f'{env_cmd}& "{python_exe}" "{script_path}"'

    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>SolarPunk Desktop Daemon — autonomous AI agent loop</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled></LogonTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -Command "{ps_launch}"</Arguments>
      <WorkingDirectory>{ROOT}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = DATA / "daemon_task.xml"
    xml_path.write_text(task_xml, encoding="utf-16")

    out, err = run_powershell(
        f'Register-ScheduledTask -TaskName "SolarPunk-Daemon" '
        f'-Xml (Get-Content "{xml_path}" -Raw) -Force'
    )

    if err and "error" in err.lower():
        print(f"Install failed: {err}")
        print(f"Run manually: python {script_path}")
    else:
        print("✅ SolarPunk-Daemon installed as Windows scheduled task")
        print("   Auto-starts at every login, restarts on crash")
        print(f"   Add ANTHROPIC_API_KEY to {ROOT}\\.env")


# ── ENTRY POINT ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SolarPunk Desktop Daemon")
    parser.add_argument("--install", action="store_true", help="Install as Windows auto-start task")
    parser.add_argument("--once",    action="store_true", help="Process queue once and exit")
    parser.add_argument("--status",  action="store_true", help="Show current state and exit")
    args = parser.parse_args()

    if args.install:
        install_autostart()
    elif args.status:
        state  = load_state()
        queue  = load_queue()
        pending = len([t for t in queue if t.get("status") == "pending"])
        print(json.dumps({**state, "pending_tasks": pending}, indent=2))
    elif args.once:
        queue   = load_queue()
        pending = sorted(
            [t for t in queue if t.get("status") == "pending"],
            key=lambda t: t.get("priority", 5)
        )[:10]
        results = load_results()
        for task in pending:
            result = execute_task(task)
            results.append(result)
            for q in queue:
                if q.get("id") == task.get("id"):
                    q["status"] = result["status"]
        save_queue(queue)
        wj(RESULTS_FILE, results[-100:])
        print(f"Processed {len(pending)} tasks.")
    else:
        run_loop()
