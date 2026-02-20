# REDDIT POSTS — ready to copy-paste
# Post these manually or automate via pushshift-compatible API
# Each written for its specific community

---
## r/opensource
**Title:** I built a self-running humanitarian art gallery on GitHub. Zero servers. Zero cost. 70% of sales to Gaza.

I'm Meeko. I built Gaza Rose Gallery — 56 original digital flower artworks, $1 each, 70% to Palestine Children's Relief Fund (verified 4-star Charity Navigator).

The interesting part isn't the art. It's the architecture:

- GitHub Actions replaces a backend (free, runs twice daily)
- A private GitHub repo acts as persistent AI memory
- IMAP + OpenRouter reads and replies to all emails automatically  
- Lightning Network (Strike) handles payments at near-zero fees
- Total monthly cost: literally $0

The whole thing is open source and designed to be forkable. Any humanitarian cause could have this system running in an afternoon.

Code: https://github.com/meekotharaccoon-cell/meeko-nerve-center  
Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

Happy to answer questions about the architecture.

---
## r/selfhosted  
**Title:** Replaced a $50/month backend with GitHub Actions for a humanitarian art gallery — here's the architecture

Built a fully autonomous gallery that manages its own promotion, email responses, health checks, and payments without a single server.

Stack:
- GitHub Actions (cron schedules = heartbeat)
- GitHub Pages (hosting)
- OpenRouter API (AI content + email replies)
- SerpAPI (web monitoring)
- PayPal + Lightning Network (payments)
- Private GitHub repo (persistent memory across sessions)

Total cost: $0/month. 70% of sales go to PCRF (Palestine children's medical care).

Code: https://github.com/meekotharaccoon-cell/meeko-nerve-center

The architecture doc explains every component. Fork it for your own project.

---
## r/MachineLearning
**Title:** Built a system where a GitHub repo acts as persistent AI memory across sessions — running it for a humanitarian gallery

Short version: instead of a database, I use a private GitHub repo with markdown files (SYSTEM_STATE.md, CONNECTIONS.md, TODO.md) as the memory layer for an AI agent running via GitHub Actions.

At the start of every Action run, the Python script reads these files to know what's been done, what connections are live, what emails have been sent. At the end, it writes updated state back. The AI (OpenRouter/GPT-4o-mini) reads the context and makes decisions based on real current state rather than hallucinated state.

It's running a real humanitarian art gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

Architecture: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Interested if anyone's seen similar patterns or has thoughts on the memory architecture.

---
## r/webdev
**Title:** I made a Cloudflare Worker that creates Strike Lightning invoices and auto-delivers digital downloads on payment — here's the code

Built for Gaza Rose Gallery (humanitarian art, $1/piece, 70% to Gaza).

The Worker:
1. Receives POST with art name/file
2. Creates Strike invoice for $1 via API
3. Returns Lightning payment request string
4. Gallery JS shows QR + copy button
5. On Strike webhook (payment confirmed), delivers download

Near-zero fees on $1 transactions vs PayPal's 49 cents. Code is open source at:
https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/mycelium/lightning_checkout.js

Feedback welcome. Still needs STRIKE_API_KEY to go fully live.
