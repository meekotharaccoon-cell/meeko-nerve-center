# Self-Hosted Gitea — Your Own GitHub

Gitea is open source, lightweight, GitHub-compatible, and runs on the same $4/month VPS
you'll eventually use for radio. One server. Everything.

## What You Get

- Full Git hosting (repos, branches, PRs, issues, wikis)
- GitHub Actions-compatible CI/CD (Gitea Actions)
- Package registry
- Built-in container registry
- Web interface identical feel to GitHub
- **Total data ownership. No one can ban you. No one reads your code.**

## Migration Plan (When You Have a VPS)

### Step 1: Spin up a $4/month VPS
- Hetzner CX11: €3.29/month, 2 vCPU, 2GB RAM, 20GB SSD
- Good enough for: Gitea + Icecast radio + n8n + Gitea Actions

### Step 2: Install Gitea (15 minutes)
```bash
# On the VPS:
curl -fsSL https://raw.githubusercontent.com/go-gitea/gitea/main/contrib/quick-start/install.sh | bash

# Or with Docker (easier):
docker run -d \
  --name gitea \
  -p 3000:3000 \
  -p 222:22 \
  -v gitea-data:/data \
  gitea/gitea:latest
```

### Step 3: Mirror all your repos from GitHub to Gitea
Gitea has a built-in GitHub migration tool:
- Settings → Migrate Repository
- Paste GitHub URL
- It copies everything: code, issues, wiki, stars
- Automatically syncs on a schedule

### Step 4: Update workflows to push to both
```yaml
# In any workflow:
- name: Push to Gitea mirror
  run: |
    git remote add gitea https://git.yourdomain.com/meeko/${{ github.event.repository.name }}.git
    git push gitea main || true
```

### Step 5: Redirect spawn.html to point to Gitea
Keep GitHub as a mirror. Gitea becomes primary.
GitHub stays as the public face (more discovery). Gitea is your actual home.

## Cost to Run Everything on One VPS

| Service | VPS Resources |
|---------|---------------|
| Gitea | 200MB RAM |
| Icecast radio | 100MB RAM |
| n8n automation | 300MB RAM |
| Flowise AI | 400MB RAM |
| Nginx reverse proxy | 50MB RAM |
| **Total** | **~1GB** (fits in 2GB VPS) |

**Monthly cost: ~$4**

## Thank You, GitHub

GitHub gave us:
- 2,000 free CI minutes/month
- Free Pages hosting
- Free package registry
- Free Actions runners
- The platform that let this whole system be built for $0

We're not leaving. We're duplicating. GitHub stays as the free public mirror.
Gitea becomes the sovereign home.

That's how open source infrastructure works: build on free platforms,
own your own copy, never be locked in, never be locked out.
