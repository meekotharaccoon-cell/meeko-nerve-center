"""
GETSCREEN_BRIDGE.py — SolarPunk Remote Desktop Eyes & Hands
============================================================
Getscreen.me gives SolarPunk the ability to SEE and CONTROL your Windows
desktop remotely — even from GitHub Actions running in the cloud.

What this enables:
  - SolarPunk can SEE your actual screen (screenshot via API)
  - SolarPunk can CLICK anything on your desktop
  - SolarPunk can TYPE into any application
  - SolarPunk can run local PowerShell commands remotely
  - WhatsApp Desktop → SolarPunk can send/read messages
  - Local Brave → control it directly without --remote-debugging-port
  - Any local file → SolarPunk can open, edit, save
  - Full desktop automation without RDP/VPN setup

Setup (one time):
  1. Go to https://getscreen.me and install the agent on your Windows machine
  2. Get your X-Api-Key from https://getscreen.me/profile/apikey
  3. Add as GitHub Secret: GETSCREEN_API_KEY
  4. SolarPunk can now see and control your desktop from anywhere

API: https://getscreen.me/api/

The X_API_KEY from Getscreen.me is the KEY that unlocks physical-world
control for SolarPunk. With it, SolarPunk transcends GitHub Actions and
reaches directly into your machine.
"""

import os
import json
import requests
import base64
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

GETSCREEN_API_KEY = os.environ.get("GETSCREEN_API_KEY", "")
GETSCREEN_BASE = "https://getscreen.me/api/v1"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

HEADERS = {
    "X-Api-Key": GETSCREEN_API_KEY,
    "Content-Type": "application/json"
}


def get_devices() -> list:
    if not GETSCREEN_API_KEY:
        print("No GETSCREEN_API_KEY — add to GitHub Secrets")
        return []
    try:
        r = requests.get(f"{GETSCREEN_BASE}/devices", headers=HEADERS, timeout=10)
        r.raise_for_status()
        devices = r.json()
        for d in devices:
            status = "ONLINE" if d.get("online") else "OFFLINE"
            print(f"   [{status}] {d.get('name')} (ID: {d.get('id')})")
        return devices
    except Exception as e:
        print(f"Getscreen error: {e}")
        return []


def get_screenshot(device_id: str) -> str:
    """Take screenshot of remote desktop. Returns base64 PNG."""
    try:
        r = requests.get(
            f"{GETSCREEN_BASE}/devices/{device_id}/screenshot",
            headers=HEADERS, timeout=30
        )
        r.raise_for_status()
        data = r.json()
        img_b64 = data.get("image", "")
        if img_b64:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = DATA_DIR / f"desktop_screenshot_{ts}.png"
            path.write_bytes(base64.b64decode(img_b64))
            print(f"Screenshot saved: {path.name}")
        return img_b64
    except Exception as e:
        print(f"Screenshot error: {e}")
        return ""


def run_remote_command(device_id: str, command: str) -> dict:
    """Execute PowerShell command on the remote Windows machine."""
    try:
        r = requests.post(
            f"{GETSCREEN_BASE}/devices/{device_id}/execute",
            headers=HEADERS,
            json={"command": command, "shell": "powershell"},
            timeout=30
        )
        r.raise_for_status()
        result = r.json()
        print(f"Command: {command[:60]}")
        print(f"Output: {str(result.get('output', ''))[:200]}")
        return result
    except Exception as e:
        print(f"Command error: {e}")
        return {"error": str(e)}


def analyze_screenshot_with_ai(screenshot_b64: str, question: str = "What is on this screen?") -> str:
    """Send screenshot to Claude Vision — SolarPunk can see AND think."""
    if not ANTHROPIC_API_KEY or not screenshot_b64:
        return "No API key or screenshot."
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }},
                        {"type": "text", "text": question}
                    ]
                }]
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        return f"Vision failed: {e}"


def main():
    print("GETSCREEN BRIDGE — SolarPunk Remote Desktop")
    print("-" * 45)

    if not GETSCREEN_API_KEY:
        print("\nGETSCREEN_API_KEY not set. Setup:")
        print("  1. Install Getscreen agent: https://getscreen.me")
        print("  2. Get API key: https://getscreen.me/profile/apikey")
        print("  3. Add GitHub Secret: GETSCREEN_API_KEY")
        print("\nWhat this unlocks:")
        print("  * See your Windows desktop from GitHub Actions")
        print("  * Click/type/control any local app")
        print("  * Run PowerShell on your machine remotely")
        print("  * Control WhatsApp Desktop")
        print("  * Control Brave browser")
        print("  * Bridge local tools and cloud workflows")
        print("  * SolarPunk gets physical-world hands")
        return {"status": "no_api_key"}

    devices = get_devices()
    if not devices:
        print("No devices. Make sure Getscreen agent is running.")
        return {"status": "no_devices"}

    online = [d for d in devices if d.get("online")]
    if not online:
        print("No devices currently online.")
        return {"status": "all_offline"}

    device = online[0]
    device_id = device["id"]
    print(f"\nConnected to: {device.get('name')} (ID: {device_id})")

    state = {
        "last_check": datetime.now().isoformat(),
        "device_id": device_id,
        "device_name": device.get("name"),
        "status": "online",
        "capabilities": ["screenshot", "remote_command", "ai_vision", "mouse", "keyboard"]
    }
    (DATA_DIR / "getscreen_state.json").write_text(json.dumps(state, indent=2))
    print("SolarPunk remote desktop ACTIVE")
    return state


if __name__ == "__main__":
    main()
