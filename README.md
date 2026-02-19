# 🍄 Meeko Nerve Center

The autonomous nervous system for Gaza Rose Gallery.

**Artist:** Meeko  
**Mission:** $1 digital art, 70% to Palestine Children Relief Fund  
**Gallery:** https://meekotharaccoon-cell.github.io/gaza-rose-gallery

## Architecture

```
          MEEKO MYCELIUM
          
    [Brain: meeko-brain repo]
           ↕ sync
    [Heart: GitHub Actions]
    ↙           ↘
[Morning 9AM]  [Evening 9PM]
    ↓               ↓
[Eyes: health check + SerpAPI]
    ↓
[Voice: Discord + Mastodon + Dev.to]
    ↓
[Hands: PayPal + Stripe + Gumroad]
    ↓
[Memory: brain repo updated]
```

## Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| mycelium-morning | 9AM EST daily | Promote + post + brain sync |
| mycelium-evening | 9PM EST daily | Report + prep + brain sync |
| daily-promoter | 9AM UTC (legacy) | Original promoter |
| gallery-health-check | Every 6h | Uptime monitoring |

## What the Mycelium Does

- **Eyes**: Checks gallery is live. Watches for issues.
- **Voice**: Posts to Discord, Mastodon, Dev.to with original messages
- **Hands**: PayPal + Stripe + Coinbase + Gumroad secrets all loaded
- **Memory**: Updates meeko-brain repo after every pulse
- **Mind**: OpenRouter AI generates content when needed

## Secrets Status

All loaded: PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, GUMROAD_TOKEN,  
OPENROUTER_KEY, STRIPE_SECRET, KIMI_API_KEY, SERPAPI_KEY, COINBASE_COMMERCE_KEY

Needs creating by Meeko: DISCORD_WEBHOOK, MASTODON_TOKEN

## Gaza Rose Gallery

56 original 300 DPI digital flowers. $1 each. 70% to PCRF.

https://meekotharaccoon-cell.github.io/gaza-rose-gallery

---
*Runs itself. Updates itself. Never stops.*
