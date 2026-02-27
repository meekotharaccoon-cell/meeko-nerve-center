# Outreach Guide — Grants + Press

> Nothing sends without your explicit approval. You are always in control.

## How to approve and send

1. Open `data/outreach_queue.json`
2. Find the entry you want to send
3. Change `"approved": false` to `"approved": true`
4. Save the file
5. `git add data/outreach_queue.json && git commit -m "approve: [name]" && git push`
6. The next daily cycle will send it automatically

OR run it immediately:
```powershell
$env:GMAIL_ADDRESS = "your@gmail.com"
$env:GMAIL_APP_PASSWORD = "yourapppassword"
python mycelium/outreach_sender.py
```

---

## ⚡ URGENT — Do This First (17 days left)

### Mozilla Foundation Democracy x AI Cohort 2026
- **Deadline: March 16, 2026**
- **Amount: Up to $50,000 (+ $250,000 follow-on)**
- **Apply at:** https://www.mozillafoundation.org/en/what-we-do/grantmaking/incubator/democracy-ai-cohort/
- This is not an email pitch — it's a form application on their website
- Your system qualifies on every criterion:
  - ✓ Working open source technology
  - ✓ AI that strengthens democracy (Congress watcher, transparency)
  - ✓ Open by design, forkable
  - ✓ Serves communities, not corporations
  - ✓ Privacy-first architecture
  - ✓ Early stage but functional with real momentum

**Apply at the link above. Do it this weekend.**

---

## Grants Queue

### 1. Tech for Palestine Incubator
- Rolling admission (no deadline)
- Free + $300/month + mentorship + volunteers + T4P network
- Apply at: https://techforpalestine.org/incubator
- **This is your community. Apply this week.**

### 2. Mozilla Fellows Program 2026
- Stipend + project fund
- Apply at: https://foundation.mozilla.org/en/fellowships/
- Good after Mozilla Incubator + T4P

---

## Press Queue

### 🔴 Highest Priority

**Tariq Kenney-Shawa** — Al-Shabaka / LA Times / Foreign Policy
- Literally wrote about open-source intelligence for Palestinian liberation
- Twitter: @tksshawa | Website: tkshawa.com
- DM him on Twitter first, then email
- Pitch: "Built an open-source AI that autonomously funds Palestinian children"

**Electronic Intifada**
- Palestinian-run publication, perfect audience
- Contact: https://electronicintifada.net/contact
- Pitch: Gaza Rose + PCRF + autonomous + forkable

**Stanford Social Innovation Review**
- Already published "Technology Against Genocide" about T4P
- Your system is a natural follow-up story
- Contact: https://ssir.org/about/contact

### 🟡 Secondary
- TechCrunch: https://techcrunch.com/about/contact-us/
- WIRED: https://www.wired.com/about/feedback/

---

## What makes your story unique

Every journalist will ask: why is this different?

**Your answer:**
- One person built it
- It costs $0/month to run (GitHub Actions free tier)
- It thinks for itself (generates + tests + builds its own ideas)
- It funds Palestinian children autonomously while you sleep
- Anyone can fork it for $5 and run their own cause
- It has a privacy scrubber that destroys data after use
- It watches Congress for you
- It's been running autonomously since yesterday

That's not a product pitch. That's a story.
