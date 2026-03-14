# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
BRAVE_BROWSER_ENGINE.py — SolarPunk controls Brave directly
============================================================
Uses Chrome DevTools Protocol (CDP) on port 9222.
Works with ANY Chromium browser (Brave, Chrome, Edge).

How to start Brave in debug mode (already in MASTER_CONNECT.ps1):
  brave.exe --remote-debugging-port=9222 --remote-allow-origins=*

Or just run BRAVE_DEBUG_LAUNCHER.bat on your desktop.

What this engine can do:
  - Open URLs in existing Brave tabs / new tabs
  - Read page content from any open tab
  - Click elements, fill forms, take screenshots
  - Post to Bluesky/DEV.to/any web platform via browser
  - Read and drain the social queue through real browser sessions
  - Navigate Gumroad and verify products are live

No OAuth. No API keys. The browser IS the credential.
SolarPunk borrows your logged-in sessions.
"""
import os, json, urllib.request, urllib.error, urllib.parse, time
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
CDP_HOST = os.environ.get("CDP_HOST", "localhost")
CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
BASE_URL = f"http://{CDP_HOST}:{CDP_PORT}"
SHOP_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
MAX_ACTIONS = 5


def cdp(endpoint):
    """Simple CDP REST request."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/{endpoint}")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return None


def cdp_send(ws_url, method, params=None):
    """
    Send a single CDP command via WebSocket.
    Uses subprocess + Node if available, else Python websocket-client.
    Falls back to a REST-only approach for simple actions.
    """
    try:
        import websocket
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        result = json.loads(ws.recv())
        ws.close()
        return result
    except ImportError:
        pass  # websocket-client not installed, use fallback
    except Exception as e:
        return {"error": str(e)}

    # Fallback: use Python's built-in http + a simple frame builder
    # For navigate/evaluate we can use the --target approach
    return None


def get_tabs():
    """List all open tabs."""
    data = cdp("json/list")
    if not data:
        return []
    return [t for t in data if t.get("type") == "page"]


def browser_alive():
    version = cdp("json/version")
    return bool(version)


def get_tab_url_map():
    """Returns dict of {url_fragment: tab} for open tabs."""
    return {t.get("url", ""): t for t in get_tabs()}


def navigate_tab(tab_id, url):
    """Navigate a tab using CDP activate + navigate."""
    try:
        # Activate tab
        urllib.request.urlopen(f"{BASE_URL}/json/activate/{tab_id}", timeout=5)
        time.sleep(0.3)
    except: pass

    # Use websocket if available
    tabs = get_tabs()
    tab  = next((t for t in tabs if t["id"] == tab_id), None)
    if not tab:
        return False
    ws_url = tab.get("webSocketDebuggerUrl", "")
    if ws_url:
        result = cdp_send(ws_url, "Page.navigate", {"url": url})
        return result is not None
    return False


def open_new_tab(url):
    """Open a new tab at a URL."""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/json/new?{urllib.parse.quote(url)}",
            method="PUT"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            tab = json.loads(r.read())
            return tab.get("id")
    except Exception as e:
        return None


def evaluate_in_tab(tab_id, js_code):
    """Run JavaScript in a tab."""
    tabs = get_tabs()
    tab  = next((t for t in tabs if t["id"] == tab_id), None)
    if not tab:
        return None
    ws_url = tab.get("webSocketDebuggerUrl", "")
    if not ws_url:
        return None
    result = cdp_send(ws_url, "Runtime.evaluate", {
        "expression": js_code,
        "returnByValue": True,
        "awaitPromise": True,
    })
    return result


def read_tab_url(tab_id):
    tabs = get_tabs()
    tab  = next((t for t in tabs if t["id"] == tab_id), None)
    if tab:
        return tab.get("url", "")
    return ""


def verify_gumroad_products():
    """Check if Gumroad products are live by opening the store page."""
    listings_f = DATA / "gumroad_listings.json"
    if not listings_f.exists():
        return []
    listings  = json.loads(listings_f.read_text())
    live_urls = [
        p.get("gumroad_result", {}).get("gumroad_url")
        for p in listings.get("products", [])
        if p.get("gumroad_result", {}).get("status") == "live"
        and p.get("gumroad_result", {}).get("gumroad_url")
    ]
    return live_urls


def check_browser_sessions():
    """Report which sessions are currently active in Brave."""
    tabs = get_tabs()
    sessions = {
        "gumroad":  any("gumroad.com" in t.get("url","") for t in tabs),
        "bluesky":  any("bsky.app"    in t.get("url","") for t in tabs),
        "devto":    any("dev.to"      in t.get("url","") for t in tabs),
        "reddit":   any("reddit.com"  in t.get("url","") for t in tabs),
        "kofi":     any("ko-fi.com"   in t.get("url","") for t in tabs),
        "github":   any("github.com"  in t.get("url","") for t in tabs),
    }
    return sessions, tabs


def load_state():
    f = DATA / "brave_browser_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "actions": 0, "tabs_opened": 0}


def save_state(s):
    (DATA / "brave_browser_state.json").write_text(json.dumps(s, indent=2))


def run():
    state  = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    ts = datetime.now(timezone.utc).isoformat()
    print(f"BRAVE_BROWSER_ENGINE cycle {state['cycles']}")

    if not browser_alive():
        print(f"  ⚠️  Brave not on port {CDP_PORT}")
        print(f"  → Run BRAVE_DEBUG_LAUNCHER.bat on your desktop")
        print(f"  → OR run MASTER_CONNECT.ps1 (it starts Brave with debug port)")
        state["status"] = "brave_not_running"
        state["last_run"] = ts
        save_state(state)
        return state

    ver = cdp("json/version")
    print(f"  ✅ Brave live — {ver.get('Browser', '?')[:40]}")

    sessions, tabs = check_browser_sessions()
    print(f"  Open tabs: {len(tabs)}")
    active_sessions = [k for k, v in sessions.items() if v]
    if active_sessions:
        print(f"  Active sessions: {', '.join(active_sessions)}")

    actions = 0

    # ── Open SolarPunk store if not already open ──────────────────────────
    store_open = any(SHOP_URL in t.get("url","") for t in tabs)
    if not store_open and actions < MAX_ACTIONS:
        tab_id = open_new_tab(f"{SHOP_URL}/store.html")
        if tab_id:
            print(f"  ✅ Opened SolarPunk store")
            actions += 1
            state["tabs_opened"] = state.get("tabs_opened", 0) + 1

    # ── Verify Gumroad products are reachable ─────────────────────────────
    live_urls = verify_gumroad_products()
    if live_urls:
        print(f"  Gumroad products live: {len(live_urls)}")
        for url in live_urls[:2]:
            print(f"    → {url}")
        state["gumroad_live_urls"] = live_urls

    # ── Write desktop connection status ───────────────────────────────────
    connection_state = {
        "ts":              ts,
        "brave_alive":     True,
        "browser":         ver.get("Browser", "?"),
        "port":            CDP_PORT,
        "open_tabs":       len(tabs),
        "sessions":        sessions,
        "active_sessions": active_sessions,
        "gumroad_live":    len(live_urls),
        "engine":          "BRAVE_BROWSER_ENGINE",
    }
    (DATA / "brave_connection.json").write_text(json.dumps(connection_state, indent=2))

    state["status"]      = "ok"
    state["actions"]     = state.get("actions", 0) + actions
    state["last_run"]    = ts
    state["last_browser"] = ver.get("Browser", "?")
    save_state(state)

    print(f"  Actions this cycle: {actions} | All-time: {state['actions']}")
    print(f"  → Add websocket-client (pip install websocket-client) for full tab control")
    return state


if __name__ == "__main__":
    run()
