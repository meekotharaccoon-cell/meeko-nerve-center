# 🧠 Knowledge Base Index

*Auto-built daily by knowledge_harvester.py*

This directory is populated automatically every day at 5am UTC by the `knowledge-harvester.yml` workflow.

## Sources
- `github/` — trending repos by topic (autonomous agents, solarpunk, mutual aid, local-llm, etc.)
- `wikipedia/` — reference articles on key topics
- `arxiv/` — recent research papers (AI, decentralized systems, humanitarian tech)
- `hackernews/` — top stories + Show HN builder projects
- `nasa/` — ISS position, APOD, Near Earth Objects
- `repos/` — deep README harvests of specific high-value repos
- `digest/` — daily combined digest, one file
- `LATEST_DIGEST.md` — always the most recent digest

## How to use this

Other scripts in the system can read from `knowledge/` to get fresh context:

```python
from pathlib import Path
digest = Path('knowledge/LATEST_DIGEST.md').read_text()
# pass digest into Ollama prompt for context-aware responses
```

Or from any GitHub Actions workflow:
```yaml
- name: Load knowledge
  run: |
    cat knowledge/LATEST_DIGEST.md >> $GITHUB_ENV
```

## Manual harvest

Trigger a harvest anytime (no secrets needed):
1. Go to Actions tab in your repo
2. Click "Knowledge Harvester"
3. Click "Run workflow"
4. Optionally type a custom topic in the input box

---
*No API keys required. All sources are public and free.*
