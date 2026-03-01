# Permanent Internet Presence
### Your work, permanently preserved, uncensorable, findable forever.

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The complete guide to permanent digital preservation: Internet Archive, IPFS, GitHub mirroring, and the automation that keeps it all synced.

---

## Layer 1: Internet Archive

```python
import requests, time

def archive_url(url):
    r = requests.get(f"https://web.archive.org/save/{url}",
        headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code == 200:
        print(f"Archived: https://web.archive.org/web/{url}")
        return True
    return False

pages = [
    "https://YOUR-SITE.github.io/spawn.html",
    "https://YOUR-SITE.github.io/app.html",
]
for page in pages:
    archive_url(page)
    time.sleep(5)
```

---

## Layer 2: IPFS (Free at web3.storage)

1. Create account at web3.storage
2. Generate API token  
3. `npm install -g @web3-storage/w3cli`
4. `w3 up ./your-file.pdf` — returns a permanent `ipfs://` link

Anyone can access it. No company controls it.

---

## Layer 3: Mirror to Codeberg

```yaml
# .github/workflows/mirror.yml
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
      - run: |
          git remote add codeberg https://codeberg.org/USER/REPO.git
          git push --force codeberg main
        env:
          GIT_CREDENTIALS: ${{ secrets.CODEBERG_TOKEN }}
```

Setup: codeberg.org → create account → create repo → generate token → add as GitHub Secret.

---

## The 5-Minute Checklist

- [ ] Key pages submitted to archive.org
- [ ] Repo mirrored to Codeberg or GitLab
- [ ] Important files pinned to IPFS
- [ ] Automated workflow runs on every push
- [ ] README links to archived versions

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
