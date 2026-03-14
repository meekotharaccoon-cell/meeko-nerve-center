# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
CLAUDE_BRIDGE — send tasks to Claude running in Brave browser via CDP

How it works:
  1. Brave must be running with --remote-debugging-port=9222
     (MASTER_CONNECT.ps1 handles this automatically on your desktop)
  2. This engine finds the claude.ai tab (or opens one)
  3. Uses playwright + CDP to type a task prompt and wait for the response
  4. Returns the response text — free AI inference, no API credits burned

Use cases:
  - Local long-form tasks (writing, analysis, code review)
  - Tasks that need Claude's full context window
  - Batch work dispatched from other engines via data/claude_tasks_queue.json
  - Desktop automation instructions back to the SolarPunk system

Requires: pip install playwright && python -m playwright install chromium
CDP port: localhost:9222 (opened by MASTER_CONNECT.ps1)
Outputs:  data/claude_bridge_state.json
          data/claude_task_results.json
"""
import os, sys, json, time
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

STATE_FILE  = DATA / "claude_bridge_state.json"
QUEUE_FILE  = DATA / "claude_tasks_queue.json"
RESULTS_FILE = DATA / "claude_task_results.json"

CDP_URL = "http://localhost:9222"
CLAUDE_URL = "https://claude.ai/new"


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"tasks_completed": 0, "last_run": None, "bridge_status": "never_run"}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_queue():
    if QUEUE_FILE.exists():
        try:
            data = json.loads(QUEUE_FILE.read_text())
            return data if isinstance(data, list) else []
        except:
            pass
    return []


def check_cdp_alive():
    """Check if Brave debug port is open."""
    try:
        import urllib.request
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
        return True
    except:
        return False


def get_playwright():
    """Import playwright — graceful fail if not installed."""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


def send_task_via_cdp(task_text, timeout_seconds=120):
    """
    Send a task to Claude in Brave and wait for the response.
    Uses playwright connected to the existing Brave CDP session.
    """
    sync_playwright = get_playwright()
    if not sync_playwright:
        return None, "playwright not installed — run: pip install playwright && python -m playwright install chromium"

    result_text = None
    error = None

    with sync_playwright() as p:
        try:
            # Connect to existing Brave instance via CDP
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            # Find or open claude.ai tab
            claude_page = None
            for page in context.pages:
                if "claude.ai" in page.url:
                    claude_page = page
                    break

            if not claude_page:
                claude_page = context.new_page()
                claude_page.goto(CLAUDE_URL, wait_until="networkidle", timeout=30000)
                time.sleep(2)

            # Navigate to new chat
            if "/new" not in claude_page.url and "/chat/" not in claude_page.url:
                claude_page.goto(CLAUDE_URL, wait_until="networkidle", timeout=15000)
                time.sleep(2)

            # Find the input field
            selectors = [
                'div[contenteditable="true"]',
                'textarea[placeholder]',
                '[data-testid="chat-input"]',
                '.ProseMirror',
            ]
            input_field = None
            for sel in selectors:
                try:
                    input_field = claude_page.wait_for_selector(sel, timeout=5000)
                    if input_field:
                        break
                except:
                    continue

            if not input_field:
                return None, "Could not find Claude input field — is claude.ai loaded?"

            # Type the task
            input_field.click()
            time.sleep(0.5)
            input_field.fill(task_text)
            time.sleep(0.5)

            # Submit
            input_field.press("Enter")
            time.sleep(2)

            # Wait for response to complete (stop button disappears = done)
            print(f"  Waiting for Claude response (max {timeout_seconds}s)...")
            deadline = time.time() + timeout_seconds
            while time.time() < deadline:
                # Check if still generating (stop button visible)
                stop_visible = False
                for stop_sel in ['button[aria-label*="Stop"]', 'button[data-testid="stop-button"]']:
                    try:
                        btn = claude_page.query_selector(stop_sel)
                        if btn and btn.is_visible():
                            stop_visible = True
                            break
                    except:
                        pass

                if not stop_visible and time.time() > (deadline - timeout_seconds + 5):
                    # Give it a few seconds after submission before declaring done
                    time.sleep(3)
                    break

                time.sleep(2)

            # Extract the latest response
            response_selectors = [
                '[data-testid="assistant-message"] .prose',
                '.claude-message:last-child',
                '[data-is-streaming="false"]:last-child',
                'div.prose:last-of-type',
            ]
            for sel in response_selectors:
                try:
                    el = claude_page.query_selector_all(sel)
                    if el:
                        result_text = el[-1].inner_text()
                        if result_text and len(result_text) > 10:
                            break
                except:
                    pass

            if not result_text:
                # Fallback: get all message text
                try:
                    result_text = claude_page.evaluate("""
                        () => {
                            const msgs = document.querySelectorAll('[data-testid="assistant-message"]');
                            return msgs.length > 0 ? msgs[msgs.length-1].innerText : '';
                        }
                    """)
                except:
                    pass

            browser.close()

        except Exception as e:
            error = str(e)

    return result_text, error


def process_queue():
    """Process all pending tasks from the queue file."""
    queue = load_queue()
    if not queue:
        return 0

    pending = [t for t in queue if t.get("status") == "pending"]
    if not pending:
        print(f"  No pending tasks in queue ({len(queue)} total)")
        return 0

    results = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else []
    completed = 0

    for task in pending:
        task_id   = task.get("id", f"task_{int(time.time())}")
        task_text = task.get("prompt", "")
        if not task_text:
            continue

        print(f"  Processing task: {task_id}")
        print(f"  Prompt: {task_text[:80]}...")

        result, error = send_task_via_cdp(task_text)

        task["status"]     = "completed" if result else "failed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["error"]      = error

        results.append({
            "id":      task_id,
            "prompt":  task_text,
            "result":  result or error,
            "status":  task["status"],
            "ts":      datetime.now(timezone.utc).isoformat()
        })
        completed += 1
        print(f"  {'OK' if result else 'FAIL'} task {task_id}")

    # Save updated queue and results
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))
    RESULTS_FILE.write_text(json.dumps(results[-50:], indent=2))  # keep last 50
    return completed


def run():
    print("CLAUDE_BRIDGE starting...")
    state = load_state()

    # Check if we're running locally with Brave available
    if not check_cdp_alive():
        print("  SKIP: Brave debug port 9222 not available")
        print("  This engine only runs when MASTER_CONNECT.ps1 has opened Brave locally")
        print("  Run MASTER_CONNECT.ps1 on your desktop to activate")
        state["bridge_status"] = "offline_cdp_unavailable"
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    print("  OK: Brave CDP port 9222 is live")
    state["bridge_status"] = "online"

    # Process any queued tasks
    completed = process_queue()
    state["tasks_completed"] = state.get("tasks_completed", 0) + completed
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    if completed:
        print(f"  Processed {completed} tasks from queue")
    else:
        print(f"  No tasks queued. Total completed all-time: {state['tasks_completed']}")
        print(f"  To queue a task: add to data/claude_tasks_queue.json")
        print(f"  Format: [{{\"id\": \"t1\", \"prompt\": \"your task\", \"status\": \"pending\"}}]")

    save_state(state)
    print(f"  Bridge status: {state['bridge_status']}")


# ── DIRECT CALL HELPER ─────────────────────────────────────────────────────
# Other engines can import and call this directly:
#   from CLAUDE_BRIDGE import ask_claude_in_brave
#   result = ask_claude_in_brave("Analyze this revenue data: ...")
def ask_claude_in_brave(prompt, timeout=120):
    """Public API for other engines to call Claude in Brave."""
    if not check_cdp_alive():
        return None
    result, error = send_task_via_cdp(prompt, timeout)
    return result


if __name__ == "__main__":
    run()
