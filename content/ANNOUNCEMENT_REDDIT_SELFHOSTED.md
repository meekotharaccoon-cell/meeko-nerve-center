# Reddit: r/selfhosted

**Title:**
Built a fully autonomous AI agent system on GitHub's free tier — 10 daily workflows, $0/month, forkable

**Body:**
Wanted to share what's possible with GitHub Actions as an automation backbone.

The system (running right now):
- 10 scheduled workflows daily
- Automated email outreach + response (reads inbox, replies to classified messages)
- Cross-platform posting (Mastodon, Bluesky, Discord, Dev.to) — one script, all platforms
- PDF generation from markdown, committed back to repo automatically
- Revenue tracking across Gumroad + PayPal
- YouTube description management (updates all videos with current links)
- Self-archiving to Internet Archive weekly
- Living README that updates itself with real stats

**The hardware:**
Intel Core i5-8500, 32GB RAM, Intel UHD 630 integrated graphics. No GPU. No dedicated server. The "cloud" is GitHub's free tier.

**Monthly cost:** $0

**The trick:** GitHub Actions gives 2,000 free compute minutes/month on public repos. That's more than enough for this entire workload. Unlimited on public repos actually.

All workflows commit their results back to the repo, so the repo IS the database. No external storage needed.

Full source: https://github.com/meekotharaccoon-cell/meeko-nerve-center
START_HERE.md walks anyone through forking and running their own.

Ask me anything about the architecture.
