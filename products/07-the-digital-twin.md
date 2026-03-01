# The Digital Twin
### A Python file that makes decisions the way you would.

*Build an AI version of yourself that approves or blocks automated actions based on your values.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The architecture and complete code for a values-and-preferences file that any automated script can query before taking action. The ethical gating layer for any autonomous system.

This is the pattern behind `meeko_brain.py` — the decision engine in the Meeko Mycelium system.

---

## The Core Architecture

Save as `my_brain.py`:

```python
class DigitalTwin:
    def __init__(self):
        self.name = "[YOUR NAME]"
        self.voice = "warm and direct"
        
        self.values = [
            "always disclose when something is automated",
            "never contact someone without a reason they'd understand",
            "70% of revenue goes to Gaza relief",
            "would I be embarrassed if this had my name on it?"
        ]
        
        self.never_do = [
            "send bulk unsolicited email",
            "post the same content twice in 24 hours",
            "pretend to be human when asked directly",
        ]
    
    def would_i_approve(self, action: str, content: str = ""):
        """Returns (approved: bool, reason: str)"""
        for rule in self.never_do:
            if any(w in action.lower() for w in rule.split()[:3]):
                return False, f"Blocked: '{rule}'"
        
        clickbait = ["amazing", "incredible", "you won't believe", "secret hack"]
        for flag in clickbait:
            if flag in content.lower():
                return False, f"Blocked: sounds like clickbait ('{flag}')"
        
        return True, "Approved"
    
    def write_in_my_voice(self, prompt: str) -> str:
        import requests
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": f"Write as {self.name}. Voice: {self.voice}. Never use clickbait or empty hype.\n\n{prompt}",
            "stream": False
        })
        return r.json()["response"]

brain = DigitalTwin()

def would_i_approve(action, content=""):
    return brain.would_i_approve(action, content)
```

---

## One Import, Every Script

```python
from my_brain import would_i_approve

approved, reason = would_i_approve("send email", email_body)
if not approved:
    print(f"Blocked: {reason}")
else:
    send_email()
```

Every automated action now passes through your judgment.

---

## The Sync Pattern

Commit `my_brain.py` to GitHub. Every workflow importing it gets your updated values on next run. Change one file — the whole system updates.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
