# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AGENT_LINK_VERIFIER.py — Nano-agent that checks all live pages for 404s
========================================================================
Runs every cycle. Verifies all docs/ HTML pages are accessible via
GitHub Pages. Reports broken links and missing pages. Auto-creates
stub pages for any docs/ subdirectory that lacks an index.html.
"""
import sys, os, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from NANO_AGENT import NanoAgent, DATA, DOCS
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.error

BASE = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

KNOWN_PAGES = [
    "index.html", "store.html", "dashboard.html", "proof.html",
    "art.html", "capabilities.html", "setup.html", "launch.html",
    "memory.html", "status.html", "outreach.html", "knowledge_map.html",
    "exchange.html", "first_contact.html", "quick_revenue.html",
]


class AGENT_LINK_VERIFIER(NanoAgent):
    def _check(self, url: str) -> tuple:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-Verifier/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, "ok"
        except urllib.error.HTTPError as e:
            return e.code, str(e)
        except Exception as e:
            return 0, str(e)

    def run(self):
        results = {"ok": [], "broken": [], "missing": []}
        ts = datetime.now(timezone.utc).isoformat()

        # Check known pages
        for page in KNOWN_PAGES:
            url = f"{BASE}/{page}"
            code, msg = self._check(url)
            if code == 200:
                results["ok"].append(page)
            else:
                results["broken"].append({"page": page, "code": code, "msg": msg})
                self._log(f"BROKEN: {page} → {code}")

        # Check all docs/ subdirs have index.html
        stub_created = []
        for subdir in DOCS.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("."):
                idx = subdir / "index.html"
                if not idx.exists():
                    # Create a stub page
                    name = subdir.name.replace("-", " ").replace("_", " ").title()
                    stub = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — SolarPunk</title>
<meta http-equiv="refresh" content="3;url=/meeko-nerve-center/store.html">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#080c10;color:#dde;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center}}.t{{color:#00ff88;font-size:1.5rem;margin-bottom:12px}}p{{color:rgba(255,255,255,.4);font-size:.9rem}}a{{color:#00ff88}}</style>
</head>
<body>
<div>
  <div class="t">{name}</div>
  <p>This product is being built. Redirecting to store in 3 seconds...</p>
  <p style="margin-top:16px"><a href="/meeko-nerve-center/store.html">Go to Store →</a></p>
</div>
</body>
</html>"""
                    idx.write_text(stub)
                    stub_created.append(subdir.name)
                    self._log(f"Created stub: {subdir.name}/index.html")

        # Save report
        report = {
            "ts": ts,
            "pages_ok": len(results["ok"]),
            "pages_broken": len(results["broken"]),
            "stubs_created": stub_created,
            "broken_detail": results["broken"],
        }
        self.save_data("link_verifier_state.json", report)

        return {
            "status": "ok",
            "summary": f"{len(results['ok'])} ok, {len(results['broken'])} broken, {len(stub_created)} stubs created",
            **report,
        }

if __name__ == "__main__":
    AGENT_LINK_VERIFIER("AGENT_LINK_VERIFIER").execute()
