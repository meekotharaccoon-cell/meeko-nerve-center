# Permanent Internet Presence
### Your work, permanently preserved, uncensorable, findable forever.

*How to make sure what you create cannot be deleted, lost, or buried.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The complete guide to making your digital work permanent: Internet Archive, IPFS, GitHub mirroring, and the automation that keeps it all synced. After this, your content survives server failures, account bans, and company shutdowns.

---

## Why Permanence Matters

In 2026:
- Twitter/X can delete any account instantly
- GitHub can suspend repos (it's happened to political content)
- Websites go down when hosting isn't paid
- Cloud services shut down with 30 days notice

If your work only exists in one place, it's one decision away from gone.

Permanence means: copies in multiple systems, at least one of which no single company controls.

---

## Layer 1: Internet Archive (Free, Immediate)

The Internet Archive (archive.org) preserves web pages permanently. Anyone can submit any URL.

**Manual:**
Go to `web.archive.org/save` → paste your URL → save.

**Automated (runs on every GitHub push):**
```python
import requests

def archive_url(url):
    r = requests.get(
        f"https://web.archive.org/save/{url}",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    if r.status_code == 200:
        archived_url = f"https://web.archive.org/web/{url}"
        print(f"✅ Archived: {archived_url}")
        return archived_url
    return None

# Archive your key pages
pages = [
    "https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html",
    "https://meekotharaccoon-cell.github.io/meeko-nerve-center/app.html",
]

for page in pages:
    archive_url(page)
    import time; time.sleep(5)  # Don't hammer the API
```

---

## Layer 2: IPFS (Permanent, Decentralized)

IPFS (InterPlanetary File System) stores files by their content hash — not by location. Once pinned, a file lives as long as anyone is pinning it.

**Free pinning services:**
- **web3.storage** — 5GB free, no credit card
- **Pinata** — 1GB free tier
- **Filebase** — 5GB free

**Setup with web3.storage:**
1. Create account at web3.storage
2. Generate API token
3. Install: `pip install web3storage`

```python
import subprocess
import os

WEB3_TOKEN = "your-web3-storage-token"

def pin_to_ipfs(file_path):
    """Pin a file to IPFS via web3.storage CLI"""
    result = subprocess.run(
        ["w3", "up", file_path],
        capture_output=True, text=True,
        env={**os.environ, "WEB3_TOKEN": WEB3_TOKEN}
    )
    if result.returncode == 0:
        cid = result.stdout.strip().split('/')[-1]
        print(f"✅ Pinned: ipfs://{cid}")
        return cid
    return None
```

---

## Layer 3: Mirror to Codeberg

Codeberg is a European non-profit Git hosting. Mirroring your repo there means GitHub outages don't take you down.

**Automated mirror via GitHub Actions:**
```yaml
# .github/workflows/mirror-codeberg.yml
name: Mirror to Codeberg
on:
  push:
    branches: [main]
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Push to Codeberg
        run: |
          git remote add codeberg https://codeberg.org/YOUR_USER/YOUR_REPO.git
          git push --force codeberg main
        env:
          GIT_CREDENTIALS: ${{ secrets.CODEBERG_TOKEN }}
```

Set up: create account at codeberg.org → create repo → generate token → add as GitHub Secret `CODEBERG_TOKEN`.

---

## Layer 4: The Permanence Workflow

Combine all three into one GitHub Action that runs on every push:

```yaml
# .github/workflows/make-permanent.yml
name: Make Permanent
on:
  push:
    branches: [main]
jobs:
  preserve:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Archive to Wayback Machine
        run: |
          python -c "
import requests, time
pages = ['https://YOUR-SITE.github.io/spawn.html']
for p in pages:
    requests.get(f'https://web.archive.org/save/{p}')
    time.sleep(3)
print('Archived')"
      - name: Pin to IPFS
        run: |
          pip install -q requests
          # Add your IPFS pinning logic here
        env:
          WEB3_TOKEN: ${{ secrets.WEB3_TOKEN }}
```

---

## The 5-Minute Permanence Checklist

- [ ] Key pages submitted to archive.org
- [ ] GitHub repo has at least one mirror (Codeberg or GitLab)
- [ ] Important files pinned to IPFS
- [ ] Automated workflow runs permanence actions on every push
- [ ] README links to archived versions

Five things. After this, your work is significantly harder to erase.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
