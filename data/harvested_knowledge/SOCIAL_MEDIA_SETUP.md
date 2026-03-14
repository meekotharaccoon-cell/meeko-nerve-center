# Social Media Setup — Every Account, Every Platform

Create these accounts ONCE. Then the system runs them forever.

## Accounts to Create (Human Action Required Once)

### Priority 1 — Create These First

| Platform | Handle to claim | Why |
|----------|----------------|-----|
| **Mastodon** | @solarpunkMycelium@mastodon.social | Fediverse, tech crowd, open source people, no algorithm |
| **Bluesky** | solarpunk-mycelium.bsky.social | Fast growing, decentralized, less hostile than Twitter |
| **YouTube** | Already exists — connect to cross-poster | Flower videos, ad revenue when monetized |
| **Ko-fi** | ko-fi.com/solarpunkmycelium | No-fee tips, memberships, shop — Ko-fi takes 0% on tips |
| **Patreon** | patreon.com/solarpunkmycelium | Monthly memberships, recurring revenue |
| **Gumroad** | Already exists | Digital downloads |

### Priority 2 — Add When Ready

| Platform | Handle | Why |
|----------|--------|-----|
| **Reddit** | u/SolarPunkMycelium | Subreddits: r/solarpunk, r/digitalart, r/Palestine, r/opensource |
| **Dev.to** | Already wired | Developer audience, free tech articles |
| **Substack** | substack.com/@solarpunkmycelium | Newsletter, free tier, pays writers via subscriptions |
| **Twitch** | SolarPunkMycelium | Streaming, community building |
| **Instagram** | @solarpunk.mycelium | Flower art goes HERE — visual platform, massive reach |
| **TikTok** | @solarpunkmycelium | 30-second flower shorts are PERFECT for this platform |
| **Pinterest** | SolarPunkMycelium | Flower art, herbal remedies, solarpunk aesthetic — massive evergreen traffic |
| **LinkedIn** | SolarPunk Mycelium | Grants, professional connections, humanitarian tech |

### Priority 3 — Fediverse Expansion

| Platform | What |
|----------|------|
| **Pixelfed** | Instagram alternative, federated, photo sharing |
| **Peertube** | YouTube alternative, federated, video hosting |
| **Lemmy** | Reddit alternative, federated |

## After Creating: What the System Does

Once you create the accounts and add the API credentials as GitHub Secrets, `cross_poster.py` handles:
- Daily posts on a rotating schedule (7 content types cycling)
- Hashtags optimized per platform
- Never double-posts
- Tracks engagement in data/posted.json
- Responds to comments via email_responder (Mastodon) and youtube_manager (YouTube)

## Monetization Per Platform

| Platform | Revenue Type | When Active |
|----------|-------------|-------------|
| YouTube | AdSense | 1,000 subscribers + 4,000 watch hours |
| Ko-fi | Tips, merch, memberships | Immediate |
| Patreon | Monthly memberships | Immediate |
| Gumroad | Digital sales | Immediate (active now) |
| Instagram | Creator fund, affiliate | 10,000+ followers |
| TikTok | Creator fund | 10,000+ followers, 100K views/30 days |
| Substack | Paid subscriptions | Any size audience |
| Twitch | Affiliate | 50 avg viewers |

## Content Strategy: What to Post Where

| Content | Best Platforms |
|---------|---------------|
| 30-second flower 3D shorts | TikTok \u2192 Instagram Reels \u2192 YouTube Shorts |
| Full flower artwork | Instagram \u2192 Pinterest \u2192 Pixelfed |
| Rights education (TCPA etc.) | Twitter/X \u2192 Mastodon \u2192 Reddit \u2192 LinkedIn |
| Technical system reveals | Dev.to \u2192 Reddit r/selfhosted \u2192 Bluesky |
| Herbal remedies | Pinterest \u2192 Reddit r/herbalism \u2192 Instagram |
| Grant announcements | Mastodon \u2192 LinkedIn \u2192 Newsletter |
| Mutual aid resources | Reddit \u2192 Mastodon \u2192 Facebook groups |

## The TikTok/Reels Opportunity — Important

Your 30-second 3D flower shorts with lo-fi music are **exactly** what TikTok and Reels are built for:
- Short: check
- Visually captivating: check
- Music: check
- Clear CTA in description: check (Gumroad + gallery links)
- Emotional hook (Gaza, PCRF): check

TikTok cannot be automated via API for video posting (they don't allow it). But:
1. You post manually once
2. It gets recycled automatically to YouTube Shorts (the upload API exists)
3. Instagram Reels can be auto-posted via their Content Publishing API

For TikTok: the play is to post 1-3 times manually to establish the algorithm, then let it compound. The system handles description updates and link optimization.

## One Thing You Can Do Right Now

Create `solarpunk.mycelium@gmail.com` and use it to sign up for all these accounts. That way:
- No personal email attached to any platform account
- System email receives platform notifications
- email_responder.py can read and respond to platform messages
- You are never the single point of failure
