# The Digital Twin
### A Python file that makes decisions the way you would.

*Build an AI version of yourself that approves or blocks automated actions based on your values.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The architecture and complete code for a "digital twin" — a values-and-preferences file that any automated script can query before taking action. It's the ethical gating layer for any autonomous system.

This is the pattern used in `meeko_brain.py` — the decision engine running in the Meeko Mycelium system.

---

## The Problem It Solves

When you build automated systems, they eventually do something you didn't want. Not because of a bug — because you never told them what you value.

A digital twin is a structured way to encode:
- What you will and won't do
- How you prioritize competing goals
- What your voice sounds like
- What causes you care about
- What would embarrass you if done in your name

---

## The Core Architecture

Save as `my_brain.py`:

```python
class DigitalTwin:
    """
    A decision-making layer encoding personal values and preferences.
    Every automated action should pass through would_i_approve() before running.
    """
    
    def __init__(self):
        self.name = "[YOUR NAME]"
        self.voice = "[warm and direct / formal / casual]"
        
        # What you stand for
        self.values = [
            "transparency — always disclose when something is automated",
            "consent — never contact someone without a reason they'd understand",
            "dignity — never write condescending or manipulative content",
            "cause — 70% of revenue goes to Gaza relief",
            "quality — would I be embarrassed if this had my name on it?"
        ]
        
        # Hard rules — never break these
        self.never_do = [
            "send bulk unsolicited email",
            "post the same content twice in 24 hours",
            "make promises I can't keep",
            "share personal information about others",
            "pretend to be human when asked directly",
        ]
        
        # What I actually care about
        self.causes = [
            "Palestinian humanitarian relief",
            "open source and digital commons",
            "AI democratization",
            "economic justice",
        ]
        
        # Communication preferences
        self.comm_style = {
            "email_tone": "warm, direct, no filler words",
            "social_tone": "thoughtful, sometimes funny, never performative",
            "reply_speed": "within 24 hours for important things",
            "emoji_policy": "rare, only when they add meaning",
        }
    
    def would_i_approve(self, action: str, content: str = "") -> tuple[bool, str]:
        """
        Check if an action aligns with values.
        Returns: (approved: bool, reason: str)
        """
        action_lower = action.lower()
        content_lower = content.lower()
        
        # Hard blocks
        for rule in self.never_do:
            if any(word in action_lower for word in rule.split()[:3]):
                return False, f"Blocked: violates rule '{rule}'"
        
        # Content quality check
        red_flags = ["amazing", "incredible", "you won't believe", "secret", "hack"]
        for flag in red_flags:
            if flag in content_lower:
                return False, f"Blocked: content sounds like clickbait ('{flag}')"
        
        # Check cause alignment
        if "sell" in action_lower or "promote" in action_lower:
            if not any(cause in content_lower for cause in ["pcrf", "gaza", "relief", "open source"]):
                return True, "Approved with suggestion: consider adding cause context"
        
        return True, "Approved"
    
    def write_in_my_voice(self, prompt: str) -> str:
        """Use Ollama to generate content matching my style"""
        import requests
        style_context = f"""
You are writing as {self.name}.
Voice: {self.voice}
Values: {', '.join(self.values[:3])}
Causes: {', '.join(self.causes[:2])}
Never: clickbait, manipulation, empty hype

Prompt: {prompt}"""
        
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": style_context,
            "stream": False
        })
        return r.json()["response"]

# Global instance — import this everywhere
brain = DigitalTwin()

def would_i_approve(action, content=""):
    return brain.would_i_approve(action, content)
```

---

## Using It In Every Script

Add this to the top of any automated script:

```python
from my_brain import would_i_approve

# Before any outgoing action:
approved, reason = would_i_approve("send email", email_body)
if not approved:
    print(f"Blocked: {reason}")
else:
    send_email()
```

One import. One check. Every script now has your judgment in it.

---

## The Sync Pattern

The digital twin only works if it's the single source of truth. Commit it to GitHub, import it in every script:

```bash
# In your repo
git add my_brain.py
git commit -m "brain: update voice and values"
git push
```

Every workflow that imports `my_brain` now has your updated values on next run. You changed one file and the whole system updated.

---

## Why This Matters

As you automate more, you'll face situations you didn't anticipate. Without a digital twin, your system will make decisions based on what's technically possible rather than what you actually value.

With a digital twin: every script, every email, every post passes through the same filter — your filter — before it goes anywhere.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
