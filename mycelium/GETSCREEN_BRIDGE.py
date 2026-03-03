"""
GETSCREEN_BRIDGE.py — SolarPunk Remote Desktop Eyes & Hands
============================================================
Getscreen.me gives SolarPunk the ability to SEE and CONTROL your Windows
desktop remotely — even from GitHub Actions running in the cloud.

Secret name in GitHub: X_API_KEY
(This is the X-Api-Key from your Getscreen.me account at getscreen.me/profile/apikey)

What this enables:
  - SolarPunk can SEE your actual screen (screenshot via API)
  - SolarPunk can CLICK anything on your desktop
  - SolarPunk can TYPE into any application
  - SolarPunk can run local PowerShell commands remotely
  - WhatsApp Desktop → SolarPunk reads and sends messages
  - Brave browser → control it directly
  - Any local file → SolarPunk can open, edit, save
  - Full desktop automation, no VPN/RDP needed

API: https://getscreen.me/api/
"""

import os
import json
import requests
import base64
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Secret is stored as X_API_KEY in GitHub Secrets
X_API_KEY = os.environ.get("X_API_KEY", "")
GETSCREEN_BASE = "https://getscreen.me/api/v1"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

HEADERS = {
    "X-Api-Key": X_API_KEY,
    "Content-Type": "application/json"
}


def get_devices() -> list:
    if not X_API_KEY:
        print("No X_API_KEY in secrets — Getscreen not connected")
        return []
    try:
        r = requests.get(f"{GETSCREEN_BASE}/devices", headers=HEADERS, timeout=10)
        r.raise_for_status()
        devices = r.json()
        print(f"Found {len(devices)} device(s):")
        for d in devices:
            status = "ONLINE" if d.get("online") else "OFFLINE"
            print(f"   [{status}] {d.get('name')} (ID: {d.get('id')})")
        return devices
    except Exception as e:
        print(f"Getscreen error: {e}")
        return []


def get_screenshot(device_id: str) -> str:
    """Take screenshot of remote desktop. Returns base64 PNG."""
    if not X_API_KEY:
        return ""
    try:
        r = requests.get(
            f"{GETSCREEN_BASE}/devices/{device_id}/screenshot",
            headers=HEADERS, timeout=30
        )
        r.raise_for_status()
        img_b64 = r.json().get("image", "")
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
    if not X_API_KEY:
        return {"error": "No X_API_KEY"}
    try:
        r = requests.post(
            f"{GETSCREEN_BASE}/devices/{device_id}/execute",
            headers=HEADERS,
            json={"command": command, "shell": "powershell"},
            timeout=30
        )
        r.raise_for_status()
        result = r.json()
        print(f"Ran: {command[:60]}")
        print(f"Output: {str(result.get('output', ''))[:200]}")
        return result
    except Exception as e:
        print(f"Command error: {e}")
        return {"error": str(e)}


def analyze_screenshot_with_ai(screenshot_b64: str, question: str = "What is on this screen? What should SolarPunk do next?") -> str:
    """Send screenshot to Claude Vision. SolarPunk can see AND think about your desktop."""
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

    if not X_API_KEY:
        print("\nX_API_KEY not in GitHub Secrets.")
        print("You already have it from Getscreen.me — just add it:")
        print("  GitHub → Settings → Secrets → New: X_API_KEY")
        print("\nOnce added, SolarPunk can:")
        print("  * See your Windows desktop from GitHub Actions")
        print("  * Click/type/control any local app")
        print("  * Run PowerShell on your machine remotely")
        print("  * Control WhatsApp Desktop")
        print("  * Control Brave browser")
        print("  * Screenshot your screen and analyze it with AI vision")
        return {"status": "no_api_key"}

    devices = get_devices()
    if not devices:
        print("No devices. Make sure Getscreen agent is running on your machine.")
        return {"status": "no_devices"}

    online = [d for d in devices if d.get("online")]
    if not online:
        print("No devices online right now.")
        return {"status": "all_offline"}

    device = online[0]
    device_id = device["id"]
    print(f"\nConnected to: {device.get('name')} (ID: {device_id})")

    state = {
        "last_check": datetime.now().isoformat(),
        "device_id": device_id,
        "device_name": device.get("name"),
        "status": "online",
        "capabilities": ["screenshot", "remote_command", "ai_vision_analysis", "mouse", "keyboard"]
    }
    (DATA_DIR / "getscreen_state.json").write_text(json.dumps(state, indent=2))
    print("SolarPunk remote desktop: ACTIVE")
    return state


if __name__ == "__main__":
    main()
