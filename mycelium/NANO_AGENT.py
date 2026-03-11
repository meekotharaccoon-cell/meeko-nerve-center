#!/usr/bin/env python3
"""
NANO_AGENT.py — Base class for all SolarPunk nano-agents
=========================================================
Every agent IS SolarPunk in miniature. Each instance can:
  - Read/write data/ state files
  - Call Anthropic API (gracefully skips if key missing)
  - Send email via Gmail SMTP (skips if not configured)
  - Write HTML to docs/
  - Report status to OMNIBUS via JSON
  - Spawn child agents (write new .py files to mycelium/)
  - Self-heal (catch errors, log them, continue)

Usage:
  from NANO_AGENT import NanoAgent

  class MY_ENGINE(NanoAgent):
      def run(self):
          result = self.ask_claude("Do something useful")
          self.write_html("my_page.html", self.html_shell("My Page", result))
          return {"status": "ok", "summary": "built page"}

  if __name__ == "__main__":
      MY_ENGINE("MY_ENGINE").execute()
"""
import os, sys, json, time, smtplib, traceback
from pathlib  import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

DATA     = Path("data");     DATA.mkdir(exist_ok=True)
DOCS     = Path("docs");     DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
BASE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
REPO_URL = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"


class NanoAgent:
    def __init__(self, name: str):
        self.name       = name
        self.state_file = DATA / f"{name.lower()}_state.json"
        self.log        = []
        self._start     = time.time()

    # ── core interface ──────────────────────────────────────────────────────

    def run(self) -> dict:
        """Override this. Return dict with at minimum {'status': 'ok'|'error'}."""
        raise NotImplementedError(f"{self.name}.run() must be implemented")

    def execute(self):
        """Called from __main__. Runs, saves state, prints summary."""
        try:
            result = self.run()
        except Exception as e:
            self._log(f"FATAL: {e}")
            result = {"status": "error", "error": str(e), "tb": traceback.format_exc()}
        result.setdefault("status", "ok")
        result["agent"]   = self.name
        result["elapsed"] = round(time.time() - self._start, 2)
        result["ts"]      = datetime.now(timezone.utc).isoformat()
        result["log"]     = self.log
        self.state_file.write_text(json.dumps(result, indent=2, default=str))
        icon = "✅" if result["status"] == "ok" else "❌"
        print(f"{icon} {self.name} ({result['elapsed']}s) — {result.get('summary', result['status'])}")
        return result

    # ── data helpers ────────────────────────────────────────────────────────

    def load_state(self) -> dict:
        if self.state_file.exists():
            try: return json.loads(self.state_file.read_text())
            except: pass
        return {}

    def load_data(self, fname: str, fallback=None):
        f = DATA / fname
        if f.exists():
            try: return json.loads(f.read_text())
            except: pass
        return fallback if fallback is not None else {}

    def save_data(self, fname: str, data):
        (DATA / fname).write_text(json.dumps(data, indent=2, default=str))

    def load_context(self) -> dict:
        """Loads the full OMNIBUS context snapshot."""
        return self.load_data("ctx.json", {})

    # ── Anthropic API ────────────────────────────────────────────────────────

    def ask_claude(self, prompt: str, system: str = None, max_tokens: int = 2048) -> str:
        """
        Call Claude. Returns text or empty string if API key missing.
        Never crashes OMNIBUS — silently degrades.
        """
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            self._log("ANTHROPIC_API_KEY missing — skipping AI call")
            return ""
        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=key)
            msgs    = [{"role": "user", "content": prompt}]
            kwargs  = {"model": "claude-opus-4-5", "max_tokens": max_tokens, "messages": msgs}
            if system: kwargs["system"] = system
            resp    = client.messages.create(**kwargs)
            text    = resp.content[0].text if resp.content else ""
            self._log(f"Claude responded: {len(text)} chars")
            return text
        except Exception as e:
            self._log(f"Claude API error: {e}")
            return ""

    # ── email ────────────────────────────────────────────────────────────────

    def send_email(self, to: str, subject: str, body: str) -> bool:
        addr = os.environ.get("GMAIL_ADDRESS", "")
        pwd  = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not addr or not pwd:
            self._log("Gmail credentials missing — skipping email")
            return False
        try:
            msg            = MIMEText(body, "plain")
            msg["Subject"] = subject
            msg["From"]    = addr
            msg["To"]      = to
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(addr, pwd)
                s.send_message(msg)
            self._log(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            self._log(f"Email failed: {e}")
            return False

    # ── HTML deployment ──────────────────────────────────────────────────────

    def write_html(self, filename: str, content: str):
        """Write a page to docs/. filename can include subdirs like 'store/index.html'."""
        path = DOCS / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self._log(f"Wrote {filename} ({len(content)} bytes)")

    def html_shell(self, title: str, body: str, description: str = "") -> str:
        """Returns a complete HTML page with SolarPunk dark styling."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — SolarPunk</title>
<meta name="description" content="{description or title}">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c10;color:#dde;font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:860px;margin:0 auto;padding:40px 20px}}
h1{{color:#00ff88;font-size:clamp(1.5rem,5vw,2.5rem);margin-bottom:12px}}
h2{{color:#ffd700;font-size:1.2rem;margin:28px 0 10px}}
p{{color:rgba(255,255,255,.65);line-height:1.8;margin-bottom:14px}}
a{{color:#00ff88;text-decoration:none}}
.pill{{display:inline-block;background:rgba(255,45,107,.1);border:1px solid rgba(255,45,107,.25);border-radius:20px;padding:4px 12px;color:#ff2d6b;font-size:.75rem;margin-bottom:20px}}
.card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:20px;margin-bottom:16px}}
.btn{{display:inline-block;background:#00ff88;color:#080c10;font-weight:800;padding:14px 32px;border-radius:8px;text-decoration:none;margin:8px 0}}
footer{{margin-top:48px;padding-top:20px;border-top:1px solid rgba(255,255,255,.06);color:rgba(255,255,255,.2);font-size:.75rem;text-align:center}}
</style>
</head>
<body>
{body}
<footer>Built by <a href="{BASE_URL}">SolarPunk</a> · <a href="{REPO_URL}">Fork on GitHub</a> · 15% to Gaza · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}</footer>
</body>
</html>"""

    # ── spawning ─────────────────────────────────────────────────────────────

    def spawn_agent(self, agent_name: str, code: str) -> bool:
        """
        Write a new agent to mycelium/. Registered with OMNIBUS for next cycle.
        Only writes if file doesn't exist (safe to call repeatedly).
        """
        target = MYCELIUM / f"{agent_name}.py"
        if target.exists():
            self._log(f"{agent_name} already exists — skipping spawn")
            return False
        target.write_text(code)
        self._log(f"Spawned new agent: {agent_name}")
        weaver = self.load_data("knowledge_weaver_state.json", {"engines_built": []})
        if agent_name not in weaver.get("engines_built", []):
            weaver.setdefault("engines_built", []).append(agent_name)
            self.save_data("knowledge_weaver_state.json", weaver)
        return True

    # ── internal ──────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        entry = f"[{self.name}] {msg}"
        self.log.append(entry)
        print(f"  {entry}")
