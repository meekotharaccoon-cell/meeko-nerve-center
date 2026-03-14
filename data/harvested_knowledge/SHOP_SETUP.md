# Gaza Rose Gallery — $1 Art Shop

## Setup (5 minutes)

### 1. Enable GitHub Pages
Settings → Pages → Source: **main branch** → `/docs` folder → Save  
Your shop URL: `https://meekotharaccoon-cell.github.io/meeko-nerve-center`

### 2. Get PayPal Client ID (free)
1. Go to [developer.paypal.com](https://developer.paypal.com)
2. Create app → copy **Client ID**
3. In `docs/index.html`, replace `client-id=sb` with your real Client ID

### 3. Set up Lightning address (free, instant)
1. Create account at [strike.me](https://strike.me) 
2. Your Lightning address: `yourusername@strike.me`
3. In `docs/index.html`, replace `gazarose@strike.me` with yours

### 4. Add GitHub Secrets
Go to Settings → Secrets → Actions:
- `ANTHROPIC_API_KEY` — for AI art generation
- `GMAIL_ADDRESS` — for art delivery emails  
- `GMAIL_APP_PASSWORD` — Gmail app password
- `HF_TOKEN` — HuggingFace token (free, for image generation)
- `X_API_KEY` — Getscreen.me for desktop control

### 5. Add Gaza Rose PayPal
In `docs/index.html`, find `gazarose@example.com` and replace with Gaza Rose's PayPal email

### The Loop Math
```
Someone pays $1
  → Gaza Rose gets $0.70 (auto-sent to Gaza Rose PayPal)  
  → Loop Fund gets $0.30
  → Loop Fund pools until $1.00
  → Auto-buys another piece (triggers another sale cycle)
  → Loop continues forever
```

Every 3.33 human sales = 1 auto-sale from the loop.  
At 10 sales/day = $3/day Meeko = 3 more auto-sales = compounding.

**The system is its own customer.**
