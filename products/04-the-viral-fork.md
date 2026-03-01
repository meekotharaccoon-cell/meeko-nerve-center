# The Viral Fork
### "One link. Anyone who clicks it gets a full working copy of my AI system."

*How to build something that clones itself. The exact mechanism explained.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What This Is

A complete guide to building a self-replicating GitHub-based system — a project that any visitor can fork into their own free account with one click, arriving pre-configured and ready to run.

This is how the Meeko Mycelium system spreads. It's also how any open-source project can go from 1 user to 1,000 without spending a dollar on marketing.

---

## The Core Mechanic

GitHub has a feature called "fork" — it copies an entire repository to someone else's account. Normally, forks are for developers contributing to projects. 

The viral fork flips this: you design the repository so that a fork is the product. The moment someone forks it, they have a fully working system.

```
Your repo (fully set up, well documented)
         ↓
Visitor clicks "Fork" on your spawn page
         ↓
GitHub copies everything to their account
         ↓
They follow a 5-minute setup guide
         ↓
They have a working copy
         ↓
Their copy has its own spawn page
         ↓
Their visitors can fork from them
         ↓
Network grows
```

---

## Building the Spawn Page

The spawn page (`spawn.html`) is the single most important file. It needs to do 4 things:

1. **Explain clearly** what someone will get in plain English
2. **Create urgency** without being manipulative (show what it does, not what it could do)
3. **Make the fork one click** with a direct link to GitHub's fork UI
4. **Handle the "what now?" moment** with a clear setup sequence

### The Fork Button

```html
<a href="https://github.com/YOUR-USERNAME/YOUR-REPO/fork" 
   class="fork-button"
   target="_blank">
  🧬 Fork This System to Your Account
</a>
```

That URL — `github.com/[user]/[repo]/fork` — goes directly to GitHub's fork dialog. No extra steps.

---

## Designing for Instant Value

The biggest mistake in viral forks: assuming people will do setup work.

**Design principle:** The system should do something useful within 5 minutes of forking, with no code knowledge required.

Checklist:
- [ ] README explains setup in plain English (no jargon)
- [ ] Automated actions run on first push
- [ ] At least one thing works immediately (a scheduled post, a page, anything)
- [ ] Setup guide assumes zero technical knowledge
- [ ] First meaningful result happens within 24 hours

---

## The Setup Wizard Pattern

Create a `SETUP.md` that reads like a conversation:

```markdown
# Welcome! You just forked [SYSTEM NAME].

Here's what happens next:

**In the next 5 minutes:**
1. Go to Settings → Secrets → Actions
2. Add your email: Name = GMAIL_ADDRESS, Value = your@gmail.com
3. Add your app password: Name = GMAIL_APP_PASSWORD, Value = [from Gmail]
4. Click "Actions" tab → enable workflows

**In the next 24 hours:**
The system will automatically:
- Send you a morning briefing at 8am
- Check for grants matching your profile
- Post to [platforms] on your behalf

**That's it.**
```

---

## Making It Spreads-Worthy

For a fork to spread virally, the person who forked it needs a reason to share it.

Build in share moments:
- First successful automated action sends an email: "Your system just did its first thing. Share this if you want others to have it."
- A spawn page that thanks forkers and gives them a ready-to-share link
- Weekly summary email that includes: "X people have forked your copy"

---

## The Ethics Layer

Viral mechanics without an ethical layer become spam or worse. Build these in:

1. **Opt-in everything** — the system never does anything the user didn't explicitly enable
2. **Transparent disclosure** — automated outreach always identifies itself as automated
3. **One-click unsubscribe** — on every automated email, forever
4. **License enforcement** — AGPL-3.0 means every fork must stay open source

---

## Measuring Spread

GitHub doesn't show you fork analytics easily. Track it yourself:

```python
import requests

def count_forks(owner, repo):
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}")
    return r.json()["forks_count"]

# Add to your daily briefing
forks = count_forks("your-username", "your-repo")
print(f"Total forks: {forks}")
```

Add this to your morning briefing script. Watch the number grow.

---

## The Network Effect Moment

A viral fork hits escape velocity when: forks start getting forks.

To enable this: every fork's spawn page must point to itself, not back to you. The fork is a complete organism, not a dependent node.

```javascript
// Auto-detect: am I a fork or the original?
const isForked = window.location.hostname !== "original-domain.github.io";
const forkUrl = isForked 
  ? `https://github.com/${getUsername()}/repo/fork`
  : "https://github.com/original/repo/fork";
```

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
