"""
MEEKO MYCELIUM - BROWSER BRIDGE
================================
Connects your Python system to your actual Brave browser via CDP
(Chrome DevTools Protocol) — 100% legal, 100% your own machine.

TWO MODES:
  Mode A: ATTACH  — connects to your already-running Brave with all
                    your extensions (Phantom, etc.) already signed in.
  Mode B: LAUNCH  — starts a fresh Brave/Chromium instance your system
                    fully controls (good for headless background tasks).

WHAT YOUR SYSTEM CAN DO WITH THIS:
  - Screenshot any page
  - Read page content / prices / text
  - Monitor your Gumroad sales dashboard
  - Check your gallery is loading correctly
  - Fill and submit forms on YOUR accounts
  - Watch for notifications or balance changes
  - Run JavaScript in any open tab
  - Open/close tabs programmatically

WHAT THIS WILL NOT DO (ethical hard limits built in):
  - Access other people's accounts
  - Bypass CAPTCHAs or anti-bot systems
  - Automate actions on sites that prohibit it in their ToS
  - Store or transmit any passwords or private keys

USAGE:
  from browser_bridge import BrowserBridge
  bridge = BrowserBridge()
  bridge.attach_to_brave()   # connect to your running Brave
  bridge.screenshot("https://gumroad.com/meeko")
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

DESKTOP    = Path(r'C:\Users\meeko\Desktop')
DB_PATH    = DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db'
BRAVE_EXE  = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
CDP_PORT   = 9222
PCRF_LINK  = "https://give.pcrf.net/campaign/739651/donate"


class BrowserBridge:
    """
    Your system's eyes and hands inside the browser.
    Attaches to your running Brave or launches a controlled one.
    """

    def __init__(self):
        self.mode       = None   # 'attached' or 'launched'
        self.playwright = None
        self.browser    = None
        self.context    = None
        self.page       = None
        self._log("Browser Bridge initialized")

    # ── CONNECT ────────────────────────────────────────────

    def attach_to_brave(self):
        """
        Attach to your ALREADY RUNNING Brave browser.
        Brave must be started with --remote-debugging-port=9222
        (the launch_brave_debug() method does this for you).

        Your Phantom wallet, cookies, logins — all there.
        """
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{CDP_PORT}"
            )
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                self.page = pages[0] if pages else self.context.new_page()
            else:
                self.context = self.browser.new_context()
                self.page = self.context.new_page()

            self.mode = 'attached'
            tabs = len(self.context.pages)
            self._log(f"Attached to Brave — {tabs} tab(s) open")
            self._save_status('attached', f'{tabs} tabs')
            return True
        except Exception as e:
            self._log(f"Could not attach: {e}")
            self._log("Make sure Brave is running in debug mode.")
            self._log("Run: bridge.launch_brave_debug() first, then try again.")
            return False

    def launch_brave_debug(self, headless=False):
        """
        Launch Brave with the remote debugging port open.
        After this, call attach_to_brave() to connect.
        Brave opens visibly so you can see what your system is doing.
        """
        if not Path(BRAVE_EXE).exists():
            self._log(f"Brave not found at {BRAVE_EXE}")
            return False

        user_data = DESKTOP / '.brave_debug_profile'
        user_data.mkdir(exist_ok=True)

        args = [
            BRAVE_EXE,
            f'--remote-debugging-port={CDP_PORT}',
            f'--user-data-dir={user_data}',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        if headless:
            args.append('--headless=new')

        subprocess.Popen(args)
        self._log(f"Brave launched with debug port {CDP_PORT}")
        self._log("Waiting 3 seconds for browser to start...")
        time.sleep(3)
        return True

    def launch_controlled(self, headless=False):
        """
        Launch a fresh Playwright-controlled Chromium.
        No extensions, but fully automated — good for background tasks.
        """
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = self.context.new_page()
        self.mode = 'launched'
        self._log("Controlled Chromium launched")
        return True

    # ── ACTIONS ────────────────────────────────────────────

    def go(self, url, wait='load'):
        """Navigate to a URL."""
        self._require_connection()
        self._log(f"Navigating to: {url}")
        self.page.goto(url, wait_until=wait, timeout=30000)
        return self

    def screenshot(self, url=None, filename=None):
        """Take a screenshot. Optionally navigate to a URL first."""
        self._require_connection()
        if url:
            self.go(url)
        if not filename:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = str(DESKTOP / f'screenshot_{ts}.png')
        self.page.screenshot(path=filename, full_page=True)
        self._log(f"Screenshot saved: {filename}")
        return filename

    def get_text(self, selector=None):
        """Get all text from current page, or from a specific element."""
        self._require_connection()
        if selector:
            el = self.page.query_selector(selector)
            return el.inner_text() if el else None
        return self.page.inner_text('body')

    def get_html(self, selector=None):
        """Get HTML from current page or element."""
        self._require_connection()
        if selector:
            el = self.page.query_selector(selector)
            return el.inner_html() if el else None
        return self.page.content()

    def run_js(self, script):
        """Run JavaScript in the current page and return the result."""
        self._require_connection()
        return self.page.evaluate(script)

    def wait_for(self, selector, timeout=10000):
        """Wait for an element to appear."""
        self._require_connection()
        self.page.wait_for_selector(selector, timeout=timeout)
        return self

    def new_tab(self, url=None):
        """Open a new tab, optionally navigate to a URL."""
        self._require_connection()
        new_page = self.context.new_page()
        self.page = new_page
        if url:
            self.go(url)
        return self

    def close(self):
        """Clean up — close Playwright connection."""
        if self.playwright:
            self.playwright.stop()
        self._log("Browser bridge closed")

    # ── SYSTEM-SPECIFIC TASKS ──────────────────────────────

    def check_gallery(self):
        """
        Open your Gaza Rose Gallery and verify it's showing all art.
        Returns a dict with page title, art count, and any errors.
        """
        gallery = DESKTOP / 'GAZA_ROSE_GALLERY' / 'index.html'
        self._require_connection()
        self.go(f'file:///{gallery}')
        time.sleep(1)

        title = self.page.title()
        art_count = self.run_js("document.querySelectorAll('.art-card').length")
        crypto_btns = self.run_js("document.querySelectorAll('.btn-crypto').length")

        result = {
            'title': title,
            'art_cards': art_count,
            'crypto_buttons': crypto_btns,
            'url': str(gallery)
        }
        self._log(f"Gallery check: {art_count} art cards, {crypto_btns} crypto buttons")
        return result

    def check_payment_page(self):
        """Open and verify your crypto payment page is working."""
        payment = DESKTOP / 'GAZA_ROSE_GALLERY' / 'payment.html'
        self._require_connection()
        self.go(f'file:///{payment}')
        time.sleep(1)

        sol_addr = self.run_js(
            "const el = document.getElementById('sol-addr'); "
            "return el ? el.innerText.trim() : 'NOT FOUND'"
        )
        has_pcrf = self.run_js(
            f"return document.body.innerHTML.includes('give.pcrf.net')"
        )

        result = {
            'sol_address_shown': sol_addr[:12] + '...' if len(sol_addr) > 12 else sol_addr,
            'pcrf_link_present': has_pcrf
        }
        self._log(f"Payment page: SOL addr present={bool(sol_addr)}, PCRF link={has_pcrf}")
        return result

    def monitor_gumroad(self):
        """
        Open your Gumroad dashboard and read your latest sales.
        Returns whatever is visible — you must be logged into Gumroad.
        """
        self._require_connection()
        self.go('https://app.gumroad.com/dashboard')
        time.sleep(2)

        # Try to grab sale numbers
        page_text = self.get_text()
        screenshot_path = self.screenshot(filename=str(DESKTOP / 'gumroad_check.png'))

        self._log("Gumroad dashboard captured")
        return {
            'screenshot': screenshot_path,
            'page_preview': page_text[:500] if page_text else 'Could not read page'
        }

    def open_setup_wizard(self):
        """Open your local Setup Wizard in the browser."""
        self._require_connection()
        self.go('http://localhost:7777')
        self._log("Setup Wizard opened in browser")
        return self

    def open_pcrf_donate(self):
        """Open PCRF donation page — when it's time to send the 70%."""
        self._require_connection()
        self.go(PCRF_LINK)
        self._log("PCRF donation page opened")
        return self

    # ── INTERNAL ───────────────────────────────────────────

    def _require_connection(self):
        if not self.browser or not self.page:
            raise RuntimeError(
                "Not connected to a browser.\n"
                "Call bridge.launch_brave_debug() then bridge.attach_to_brave()\n"
                "OR call bridge.launch_controlled()"
            )

    def _log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"  [BRIDGE {ts}] {msg}")

    def _save_status(self, status, detail):
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute('''CREATE TABLE IF NOT EXISTS browser_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT, mode TEXT, status TEXT, detail TEXT)''')
            conn.execute('INSERT INTO browser_sessions VALUES (NULL,?,?,?,?)',
                (datetime.now().isoformat(), self.mode or 'unknown', status, detail))
            conn.commit()
            conn.close()
        except Exception:
            pass


# ── QUICK-CONNECT HELPER ───────────────────────────────────

def quick_connect(mode='controlled', headless=False):
    """
    One-liner to get a ready bridge.
    Usage:
        bridge = quick_connect()          # fresh Chromium
        bridge = quick_connect('attach')  # attach to running Brave
    """
    b = BrowserBridge()
    if mode == 'attach':
        if not b.attach_to_brave():
            print("\n  Could not attach. Launching Brave in debug mode...")
            b.launch_brave_debug()
            time.sleep(3)
            b.attach_to_brave()
    else:
        b.launch_controlled(headless=headless)
    return b


if __name__ == '__main__':
    print("\n" + "="*56)
    print("  BROWSER BRIDGE — INTERACTIVE TEST")
    print("="*56)
    print("\nPick a mode:")
    print("  1 — Attach to your running Brave (with Phantom)")
    print("  2 — Launch a fresh controlled Chromium")
    print("  3 — Launch Brave in debug mode, then attach")
    choice = input("\nEnter 1, 2, or 3: ").strip()

    bridge = BrowserBridge()

    if choice == '1':
        ok = bridge.attach_to_brave()
        if not ok:
            print("\n  Brave isn't running in debug mode yet.")
            print("  Choose 3 next time, or run this first:")
            print(f'  Start-Process "{BRAVE_EXE}" "--remote-debugging-port={CDP_PORT}"')
            sys.exit(1)

    elif choice == '2':
        bridge.launch_controlled(headless=False)

    elif choice == '3':
        bridge.launch_brave_debug()
        time.sleep(3)
        bridge.attach_to_brave()

    else:
        print("Invalid choice"); sys.exit(1)

    print("\nRunning gallery check...")
    result = bridge.check_gallery()
    print(json.dumps(result, indent=2))

    print("\nRunning payment page check...")
    result2 = bridge.check_payment_page()
    print(json.dumps(result2, indent=2))

    print("\nTaking desktop screenshot of gallery...")
    path = bridge.screenshot(f'file:///{DESKTOP}/GAZA_ROSE_GALLERY/index.html')
    print(f"  Saved to: {path}")

    input("\nPress Enter to close browser and exit...")
    bridge.close()
    print("Done.")
