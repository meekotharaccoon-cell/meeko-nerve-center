# Ralph Loops - Night Run Checklist

**Version:** 2.0
**Updated:** 2026-02-11

Use this checklist before every night run to ensure everything is ready.

---

## Quick Start (If All Checks Pass)

```bash
# From ralph-loops directory
bash scripts/start-night.sh

# IMPORTANT: Verify all processes started (script should complete in ~30 seconds)
bash scripts/status.sh
```

**If start-night.sh hangs:** Kill it (Ctrl+C) and check status.sh - workers may have started but script got stuck. Manually start missing components.

---

## Pre-Flight Checklist

### 1. Manager Ready

| Check | Command | Expected |
|-------|---------|----------|
| .ralph-project set | `cat .ralph-project` | Path to test project |
| API key set | `echo ${ANTHROPIC_API_KEY:+SET}` | `SET` |
| No stale manager | `cat /tmp/ralph-manager.pid 2>/dev/null` | Empty or stale PID |
| Scripts present | `ls scripts/*.sh \| wc -l` | 8+ scripts |

### 2. Test Project Ready

| Check | Command (from project dir) | Expected |
|-------|---------------------------|----------|
| Git clean | `git status --short` | Empty or only untracked |
| Config exists | `cat .ralph/config.json` | Valid JSON |
| Pending tasks | `find tasks/pending -name "*.md" \| wc -l` | 1+ tasks |
| No stuck tasks | `find tasks/in-progress -name "*.md" \| wc -l` | 0 |

### 3. Agents Ready (6 machines)

| Check | Command | Expected |
|-------|---------|----------|
| PC1 SSH | `ssh pc1 echo ok` | `ok` |
| PC2 SSH | `ssh pc2 echo ok` | `ok` |
| PC3 SSH | `ssh pc3 echo ok` | `ok` |
| PC4 SSH | `ssh pc4 echo ok` | `ok` |
| PC5 SSH | `ssh pc5 echo ok` | `ok` |
| PC6 SSH | `ssh pc6 echo ok` | `ok` |
| Claude available | `ssh pc1 "~/node_modules/.bin/claude --version"` | Version number |
| No stale workers | `ssh pc1 "pgrep -f worker.sh"` | Empty (no PIDs) |
| Agents synced | `ssh pc1 "cd ~/project && git log -1 --oneline"` | Same commit as local |

---

## Pre-Run Actions

### Stop Stale Processes

```bash
# Stop any running workers (all 5 worker machines)
ssh pc1 "pkill -f worker.sh" 2>/dev/null
ssh pc2 "pkill -f worker.sh" 2>/dev/null
ssh pc3 "pkill -f worker.sh" 2>/dev/null
ssh pc4 "pkill -f worker.sh" 2>/dev/null
ssh pc6 "pkill -f worker.sh" 2>/dev/null

# Stop stale manager on pc5
ssh pc5 "pkill -f manager-loop.sh" 2>/dev/null
```

### Sync Agents

```bash
# Push any local changes first
cd D:/projects/ralph-test-app
git add -A && git commit -m "Pre-run sync" && git push

# Sync all agents (5 workers + manager)
ssh pc1 "cd ~/project && git pull"
ssh pc2 "cd ~/project && git pull"
ssh pc3 "cd ~/project && git pull"
ssh pc4 "cd ~/project && git pull"
ssh pc5 "cd ~/project && git pull"
ssh pc6 "cd ~/project && git pull"
```

### Generate Tasks (If Needed)

```bash
cd D:/projects/ralph-loops
bash scripts/generate-tasks.sh "Your feature description here"
```

---

## Night Run Commands

### Start Everything

```bash
cd D:/projects/ralph-loops
bash scripts/start-night.sh
```

This will:
1. Run pre-flight checks
2. SSH to agents and start workers
3. Start manager loop in background

### Post-Start Verification (CRITICAL)

**Always verify after start-night.sh completes:**

```bash
# Check all workers running (5 workers)
ssh pc1 "pgrep -f 'worker.sh backend'" && echo "PC1: OK"
ssh pc2 "pgrep -f 'worker.sh frontend'" && echo "PC2: OK"
ssh pc3 "pgrep -f 'worker.sh tests'" && echo "PC3: OK"
ssh pc4 "pgrep -f 'worker.sh design'" && echo "PC4: OK"
ssh pc6 "pgrep -f 'worker.sh utility'" && echo "PC6: OK"

# Check manager running on pc5
ssh pc5 "pgrep -f manager-loop.sh" && echo "Manager: OK"

# Or use status script (recommended)
bash scripts/status.sh
```

**If any component missing, start manually:**
```bash
# Start missing worker
ssh -f pc1 "cd ~/project && nohup bash scripts/worker.sh backend > ~/worker-backend.log 2>&1 &"

# Start manager on pc5
ssh -f pc5 "cd ~/project && nohup bash scripts/manager-loop.sh > logs/manager.log 2>&1 &"
```

### Monitor During Run

```bash
# Real-time status
bash scripts/status.sh

# Watch manager log
tail -f D:/projects/ralph-test-app/logs/manager-$(date +%Y%m%d).log

# Check worker logs on agents
ssh pc1 "tail -20 ~/worker-backend.log"
ssh pc2 "tail -20 ~/worker-frontend.log"
ssh pc3 "tail -20 ~/worker-tests.log"
```

### Morning Review

```bash
bash scripts/morning-review.sh
```

---

## Troubleshooting

### Claude CLI Not Found on PC3

```bash
ssh pc3 "mkdir -p ~/.npm-global && npm config set prefix ~/.npm-global"
ssh pc3 "npm install -g @anthropic-ai/claude-code"
ssh pc3 "echo 'export PATH=~/.npm-global/bin:\$PATH' >> ~/.bashrc"
```

### Git Conflicts on Agent

```bash
ssh pc1 "cd ~/project && git fetch origin && git reset --hard origin/main"
```

### Manager Won't Start (Lock File)

```bash
rm -f /tmp/ralph-manager.pid
```

### Worker Stuck on Task

```bash
# Kill specific worker
ssh pc1 "pkill -f worker.sh"

# Move stuck task back to pending
cd D:/projects/ralph-test-app
mv tasks/in-progress/backend/*.md tasks/pending/backend/
git add -A && git commit -m "Reset stuck task" && git push
```

---

## Infrastructure Reference

| Host | IP | Role | Project Dir |
|------|-----|------|-------------|
| Windows | - | Control (triggers runs) | D:\projects\ralph-loops |
| PC1 | 100.x.x.1 | Backend (Express.js) | ~/project |
| PC2 | 100.x.x.2 | Frontend (HTML/JS) | ~/project |
| PC3 | 100.x.x.3 | Tests (Bash/curl) | ~/project |
| PC4 | 100.x.x.4 | Design (CSS/styling) | ~/project |
| PC5 | 100.x.x.5 | Manager (reviews) | ~/project |
| PC6 | 100.x.x.6 | Utility (docs/overflow) | ~/project |

| Service | Port |
|---------|------|
| Drive API | 3003 |
| Albums API | 3004 |
| Image Indexer | 3006 |
| Frontend | 3000 |

---

## Config Locations

| File | Purpose |
|------|---------|
| `.ralph-project` | Points manager to test project |
| `.ralph/config.json` | Project config (ports, limits, model) |
| `.ralph/project-context.md` | Project description for agents |
| `CLAUDE.md` | Coding rules for agents |

---

*Last verified: 2026-02-11*
