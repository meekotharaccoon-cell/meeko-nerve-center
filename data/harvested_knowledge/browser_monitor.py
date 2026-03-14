"""
BROWSER MONITOR — OMNI component
Runs alongside the other OMNI monitors.
Periodically checks your gallery, payment page, and Gumroad — takes screenshots.
"""
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.append(r'C:\Users\meeko\Desktop\UltimateAI_Master')
from browser_bridge import BrowserBridge

DESKTOP = Path(r'C:\Users\meeko\Desktop')
SHOTS   = DESKTOP / 'GAZA_ROSE_OMNI' / 'screenshots'
SHOTS.mkdir(exist_ok=True)

class BrowserMonitor:
    def __init__(self):
        self.bridge = None
        self.cycle  = 0
        self.log_file = DESKTOP / 'GAZA_ROSE_OMNI' / 'browser_log.json'

    def connect(self):
        try:
            self.bridge = BrowserBridge()
            # Try attaching to running Brave first, fall back to controlled
            if not self.bridge.attach_to_brave():
                print("  No debug Brave running — using controlled Chromium")
                self.bridge.launch_controlled(headless=True)
            return True
        except Exception as e:
            print(f"  Browser monitor offline: {e}")
            return False

    def run_checks(self):
        results = {}
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Check gallery
        try:
            r = self.bridge.check_gallery()
            results['gallery'] = r
            shot = self.bridge.screenshot(
                filename=str(SHOTS / f'gallery_{ts}.png')
            )
            results['gallery']['screenshot'] = shot
        except Exception as e:
            results['gallery'] = {'error': str(e)}

        # Check payment page
        try:
            r2 = self.bridge.check_payment_page()
            results['payment'] = r2
        except Exception as e:
            results['payment'] = {'error': str(e)}

        return results

    def run_forever(self):
        print("\n" + "="*50)
        print("  BROWSER MONITOR — starting")
        print("="*50)

        if not self.connect():
            print("  Could not connect to any browser. Exiting.")
            return

        while True:
            self.cycle += 1
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{ts}] Browser check #{self.cycle}")

            results = self.run_checks()

            gallery = results.get('gallery', {})
            payment = results.get('payment', {})
            print(f"  Gallery: {gallery.get('art_cards','?')} cards, {gallery.get('crypto_buttons','?')} crypto buttons")
            print(f"  Payment page: PCRF link={payment.get('pcrf_link_present','?')}")

            # Log to file
            entry = {'timestamp': datetime.now().isoformat(), 'cycle': self.cycle, 'results': results}
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            time.sleep(1800)  # check every 30 minutes

if __name__ == '__main__':
    m = BrowserMonitor()
    m.run_forever()
