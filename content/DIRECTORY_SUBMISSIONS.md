# Directory & Aggregator Submissions

Manual submissions to places that index open source projects.
Check off as done. These drive organic discovery for months.

## Open Source Directories

- [ ] **awesome-selfhosted** — github.com/awesome-selfhosted/awesome-selfhosted
  Submit PR adding to "Automation" section
  Entry: `- [SolarPunk Mycelium](https://github.com/meekotharaccoon-cell/meeko-nerve-center) - Autonomous humanitarian AI agent system. Runs on GitHub free tier. AGPL-3.0.`

- [ ] **awesome-AI-agents** — search GitHub for awesome AI agents lists, submit to top 3 by stars

- [ ] **Product Hunt**
  URL: producthunt.com/posts/new
  Tagline: "Autonomous humanitarian AI on GitHub's free tier — $0/month, forkable"
  Topics: Open Source, Artificial Intelligence, No-Code

- [ ] **AlternativeTo**
  URL: alternativeto.net/software/add/
  Name: SolarPunk Mycelium
  Category: Business & Commerce, Social Media Management
  License: AGPL

- [ ] **OpenSourceAlternative.to**
  URL: opensourcealternative.to/submit

- [ ] **Hacker News: Show HN**
  Use content from: content/ANNOUNCEMENT_HACKERNEWS.md
  Best time: Tuesday-Thursday, 9am-11am Eastern
  Rule: One submission. If it doesn't land, wait 6 months and reframe.

- [ ] **DevHunt.org** — devhunt.org/submit
  Developer-focused launch platform

- [ ] **GitHub Topics**
  Add these topics to all repos: solarpunk, autonomous-agent, humanitarian, open-source,
  self-hosted, github-actions, python, ethical-ai, mutual-aid
  How: Repo Settings → Topics (gear icon next to About)
  This makes repos discoverable in github.com/topics/solarpunk etc.

## Link Aggregators (Post the Dev.to article)

- [ ] **Lobste.rs** — lobste.rs (invite-only, get invite from someone)
  Tag: programming, open-source, ethics

- [ ] **Tildes.net** — tildes.net
  Tag: ~comp, ~life

- [ ] **dev.to** — Already automated via DEVTO_API_KEY

- [ ] **Hashnode** — hashnode.com (free, developer blogging)
  Cross-post the Dev.to article

## Communities to Post In Manually (One Time)

- [ ] Mastodon hashtags: #SolarPunk #OpenSource #Palestine #MutualAid #Fediverse
- [ ] Lemmy: !solarpunk@lemmy.ml, !opensource@lemmy.ml
- [ ] Matrix rooms: #solarpunk:matrix.org
- [ ] Discord servers: Solarpunk Discord, various open source Discords
- [ ] Facebook groups: Solarpunk groups, Palestine solidarity groups, mutual aid groups

## SEO: Add to All GitHub Pages Sites

Each site needs in its `<head>`:
```html
<meta name="description" content="[page description]">
<meta property="og:title" content="[title]">
<meta property="og:description" content="[description]">
<meta property="og:image" content="[preview image URL]">
<link rel="canonical" href="[full URL]">
```

This controls how the page appears when shared on social media.
The gallery already has this. Add to: spawn.html, board.html, all lesson pages.

## The Automated Part

`seo_submitter.py` handles:
- IndexNow ping (Bing, Yandex, DuckDuckGo notified immediately)
- Google sitemap ping
- Sitemap.xml generation
- Runs weekly via GitHub Actions

The manual list above is one-time. Do it once. Discovery compounds forever.
