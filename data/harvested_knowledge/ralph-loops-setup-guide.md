# Ralph Loops - Complete Setup Guide

## Overview

Ralph Loops is an autonomous AI agent farm that runs overnight on old computers, writing code while you sleep. Git serves as the communication backbone between agents.

**Cost:** $10-20/month electricity only (Gemini CLI is free)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Windows PC (Control)                      │
│   start-night.sh → triggers pc5 manager                 │
│   status.sh, morning-review.sh                          │
└───────────────────────────│──────────────────────────────┘
                            │ SSH
                            ▼
              ┌─────────────────────────────┐
              │     pc5 (Manager)           │
              │   manager-loop.sh           │
              │   Claude API for decisions  │
              └─────────────│───────────────┘
                            │ SSH + Git
    ┌───────────┬───────────┼───────────┬───────────┬───────────┐
    ▼           ▼           ▼           ▼           ▼
┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐
│  pc1  │  │  pc2  │  │  pc3  │  │  pc4  │  │  pc6  │
│backend│  │frontend│ │ tests │  │design │  │utility│
│Gemini │  │Gemini │  │Gemini │  │Gemini │  │Gemini │
└───────┘  └───────┘  └───────┘  └───────┘  └───────┘
```

## Machine Details

| Machine | Tailscale IP | Role | OS | User |
|---------|--------------|------|-----|------|
| pc1 | 100.x.x.1 | backend | Linux Mint | t |
| pc2 | 100.x.x.2 | frontend | Linux Mint | t |
| pc3 | 100.x.x.3 | tests | Linux Mint | t |
| pc4 | 100.x.x.4 | design | Linux Mint | t |
| pc5 | 100.x.x.5 | manager | Linux Mint | your-user |
| pc6 | (pending) | utility | Linux Mint | (pending) |

**Control:** Windows PC triggers runs and monitors via SSH to pc5.

## SSH Commands Reference

```powershell
# SSH to agents from Windows
C:\Windows\System32\OpenSSH\ssh.exe pc1 "command"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "command"

# Interactive SSH
C:\Windows\System32\OpenSSH\ssh.exe -t pc1 "command requiring tty"

# Test Gemini
C:\Windows\System32\OpenSSH\ssh.exe pc1 "gemini -p 'test'"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "gemini -p 'test'"
```

## Repository

- **Target Project Repo:** Configured in `.ralph/config.json` → `git.repo`
- **Example:** https://github.com/YOUR_USERNAME/YOUR_PROJECT
- **Local Path on Agents:** ~/project

## Repository Structure

```
my-project/
│
├── .git/
├── .gitignore
│
├── tasks/
│   ├── pending/                 ← Tasks waiting
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── tests/
│   │
│   ├── in-progress/             ← Tasks being worked (locked)
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── tests/
│   │
│   └── done/                    ← Completed tasks
│       ├── backend/
│       ├── frontend/
│       └── tests/
│
├── results/                     ← Results and reports
│
├── src/                         ← Product code
│   ├── backend/
│   ├── frontend/
│   └── tests/
│
├── logs/                        ← Logs (not in Git)
│
├── scripts/                     ← Automation scripts
│   ├── worker.sh
│   ├── safe-push.sh
│   ├── start-night.sh
│   ├── morning-review.sh
│   ├── watchdog.sh
│   └── manager-loop.sh          ← Phase 2
│
└── .ralph/
    └── config.json
```

## Config File

### .ralph/config.json

```json
{
  "version": "4.0",
  "project": "ralph-loops-project",
  
  "agents": {
    "pc1": {
      "name": "ralph-backend",
      "role": "backend",
      "ip": "100.x.x.1"
    },
    "pc2": {
      "name": "ralph-frontend",
      "role": "frontend",
      "ip": "100.x.x.2"
    }
  },
  
  "limits": {
    "max_tasks_per_agent": 10,
    "max_retries_per_task": 3,
    "task_timeout_minutes": 30,
    "stop_hour": 6,
    "push_retry_attempts": 5,
    "push_retry_base_delay": 10,
    "sleep_between_tasks_seconds": 60,
    "sleep_no_tasks_seconds": 120,
    "manager_poll_interval_seconds": 300
  },
  
  "git": {
    "repo": "git@github.com:YOUR_USERNAME/YOUR_PROJECT.git",
    "branch": "main"
  }
}
```

## Scripts

### scripts/safe-push.sh

```bash
#!/bin/bash
#===============================================
# Safe Git Push with Exponential Backoff
#===============================================

MAX_ATTEMPTS=${1:-5}
BASE_DELAY=${2:-10}
LOG_FILE=${3:-/tmp/safe-push.log}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    log "Push attempt $attempt/$MAX_ATTEMPTS"
    
    # Pull and rebase first
    if ! git pull --rebase origin main 2>> "$LOG_FILE"; then
        log "Pull failed, checking for conflicts..."
        
        # If rebase failed due to conflicts, abort and report
        if git status | grep -q "rebase in progress"; then
            git rebase --abort
            log "ERROR: Rebase conflict, aborted"
            exit 1
        fi
    fi
    
    # Try atomic push
    if git push --atomic origin main 2>> "$LOG_FILE"; then
        log "Push successful!"
        exit 0
    fi
    
    # Calculate delay with jitter
    delay=$((BASE_DELAY * attempt + RANDOM % 10))
    log "Push failed, waiting ${delay}s before retry..."
    sleep $delay
done

log "CRITICAL: Push failed after $MAX_ATTEMPTS attempts"
exit 1
```

### scripts/clean-json.sh

```bash
#!/bin/bash
#===============================================
# Clean JSON output from AI models
#===============================================

clean_json() {
    local input="$1"
    
    # Remove markdown code blocks
    # Remove leading/trailing whitespace
    # Validate with jq
    echo "$input" | \
        sed -e 's/^```json//g' \
            -e 's/^```//g' \
            -e '/^```$/d' \
            -e 's/^[[:space:]]*//' \
            -e 's/[[:space:]]*$//' | \
        jq -c . 2>/dev/null
    
    return ${PIPESTATUS[1]}
}

# If called directly with a file
if [ -n "$1" ] && [ -f "$1" ]; then
    clean_json "$(cat "$1")"
fi
```

### scripts/worker.sh

```bash
#!/bin/bash
#===============================================
# Ralph Worker v5 - With Auth & Quota Handling
#===============================================

set -euo pipefail

# Configuration
ROLE=${1:?Usage: worker.sh <role>}
REPO_DIR=~/project
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/${ROLE}-$(date +%Y%m%d).log"
SCRIPTS_DIR="$REPO_DIR/scripts"

# Limits
MAX_TASKS=10
MAX_RETRIES=3
TASK_TIMEOUT=30m
STOP_HOUR=6
SLEEP_BETWEEN=60
SLEEP_NO_TASKS=120
QUOTA_RETRY_SLEEP=3600  # 1 hour

#-----------------------------------------------
# Setup
#-----------------------------------------------

mkdir -p "$LOG_DIR"
cd "$REPO_DIR"

#-----------------------------------------------
# Functions
#-----------------------------------------------

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] [$ROLE] $1" | tee -a "$LOG_FILE"
}

should_stop() {
    local hour=$(date +%H)
    if [ "$hour" -ge "$STOP_HOUR" ] && [ "$hour" -lt 12 ]; then
        return 0
    fi
    return 1
}

check_quota() {
    if ! timeout 30s gemini -p "echo ok" >/dev/null 2>&1; then
        log "WARNING: Gemini quota may be exhausted"
        return 1
    fi
    return 0
}

git_sync() {
    log "Syncing with remote..."
    for i in 1 2 3; do
        if git pull --rebase origin main >> "$LOG_FILE" 2>&1; then
            return 0
        fi
        log "Pull attempt $i failed, retrying..."
        sleep 5
    done
    log "ERROR: Could not sync with remote"
    return 1
}

safe_push() {
    "$SCRIPTS_DIR/safe-push.sh" 5 10 "$LOG_FILE"
}

find_task() {
    ls "tasks/pending/$ROLE"/*.md 2>/dev/null | head -1
}

lock_task() {
    local task_file="$1"
    local task_name=$(basename "$task_file")
    local dest="tasks/in-progress/$ROLE/$task_name"

    mkdir -p "tasks/in-progress/$ROLE"
    mv "$task_file" "$dest"

    git add -A
    git commit -m "[$ROLE] Started: $task_name" >> "$LOG_FILE" 2>&1

    if safe_push >> "$LOG_FILE" 2>&1; then
        echo "$dest"
        return 0
    else
        mv "$dest" "$task_file"
        git reset HEAD~1 >> "$LOG_FILE" 2>&1
        return 1
    fi
}

complete_task() {
    local task_file="$1"
    local status="$2"
    local task_name=$(basename "$task_file")
    local result_file="results/${task_name%.md}-result.md"

    {
        echo "# Result: $task_name"
        echo "Agent: $ROLE"
        echo "Status: $status"
        echo "Started: $TASK_START_TIME"
        echo "Finished: $(date)"
        echo ""
        echo "## Log"
        echo '```'
        tail -50 "$LOG_FILE"
        echo '```'
    } > "$result_file"

    mkdir -p "tasks/done/$ROLE"
    mv "$task_file" "tasks/done/$ROLE/"

    git add -A
    git commit -m "[$ROLE] Completed ($status): $task_name" >> "$LOG_FILE" 2>&1
    safe_push >> "$LOG_FILE" 2>&1
}

execute_task() {
    local task_file="$1"
    local task_content
    task_content=$(cat "$task_file")

    log "Executing task..."
    log "Task file: $task_file"

    cd "$REPO_DIR"

    if timeout $TASK_TIMEOUT gemini --yolo -p "$task_content" >> "$LOG_FILE" 2>&1; then
        cd "$REPO_DIR"
        return 0
    else
        local exit_code=$?
        cd "$REPO_DIR"
        if [ $exit_code -eq 124 ]; then
            log "Task timed out after $TASK_TIMEOUT"
        else
            log "Task failed with exit code $exit_code"
        fi
        return 1
    fi
}

#-----------------------------------------------
# Main Loop
#-----------------------------------------------

log "=========================================="
log "Worker started"
log "Role: $ROLE"
log "Max tasks: $MAX_TASKS"
log "Stop hour: $STOP_HOUR:00"
log "=========================================="

# Pre-flight check - verify Gemini works before processing
log "Checking Gemini authentication..."
if ! timeout 30s gemini -p "echo test" >/dev/null 2>&1; then
    log "ERROR: Gemini authentication failed or quota exceeded"
    log "Run 'gemini' interactively to re-authenticate"
    exit 1
fi
log "Gemini OK"

COMPLETED=0
QUOTA_RETRIES=0
MAX_QUOTA_RETRIES=3

while [ $COMPLETED -lt $MAX_TASKS ]; do

    if should_stop; then
        log "Stop time reached (${STOP_HOUR}:00), shutting down"
        break
    fi

    if ! git_sync; then
        log "Sync failed, sleeping ${SLEEP_NO_TASKS}s"
        sleep $SLEEP_NO_TASKS
        continue
    fi

    TASK_FILE=$(find_task)

    if [ -z "$TASK_FILE" ]; then
        log "No tasks available, sleeping ${SLEEP_NO_TASKS}s"
        sleep $SLEEP_NO_TASKS
        continue
    fi

    TASK_NAME=$(basename "$TASK_FILE")
    log "Found task: $TASK_NAME"

    # Check quota before locking task
    if ! check_quota; then
        QUOTA_RETRIES=$((QUOTA_RETRIES + 1))
        if [ $QUOTA_RETRIES -ge $MAX_QUOTA_RETRIES ]; then
            log "ERROR: Quota exhausted after $MAX_QUOTA_RETRIES retries, exiting"
            exit 1
        fi
        log "Quota check failed, sleeping ${QUOTA_RETRY_SLEEP}s (retry $QUOTA_RETRIES/$MAX_QUOTA_RETRIES)"
        sleep $QUOTA_RETRY_SLEEP
        continue
    fi
    QUOTA_RETRIES=0  # Reset on success

    LOCKED_FILE=$(lock_task "$TASK_FILE")
    if [ -z "$LOCKED_FILE" ]; then
        log "Could not lock task, skipping"
        sleep $SLEEP_BETWEEN
        continue
    fi

    log "Task locked: $LOCKED_FILE"
    TASK_START_TIME=$(date)

    if execute_task "$LOCKED_FILE"; then
        complete_task "$LOCKED_FILE" "SUCCESS"
        log "Task completed successfully"
    else
        complete_task "$LOCKED_FILE" "FAILED"
        log "Task failed"
    fi

    COMPLETED=$((COMPLETED + 1))
    log "Progress: $COMPLETED/$MAX_TASKS tasks"

    sleep $SLEEP_BETWEEN
done

log "=========================================="
log "Worker finished"
log "Total completed: $COMPLETED"
log "=========================================="
```

### scripts/start-night.sh

```bash
#!/bin/bash
#===============================================
# Ralph Loops - Start Night Run
#===============================================

set -euo pipefail

REPO_DIR=~/project
SCRIPTS_DIR="$REPO_DIR/scripts"

echo "=========================================="
echo "Ralph Loops - Starting Night Run"
echo "$(date)"
echo "=========================================="

cd "$REPO_DIR"

# 1. Check for pending tasks
echo ""
echo "--- Checking Tasks ---"
BACKEND_TASKS=$(ls tasks/pending/backend/*.md 2>/dev/null | wc -l || echo 0)
FRONTEND_TASKS=$(ls tasks/pending/frontend/*.md 2>/dev/null | wc -l || echo 0)
TESTS_TASKS=$(ls tasks/pending/tests/*.md 2>/dev/null | wc -l || echo 0)

echo "Backend tasks:  $BACKEND_TASKS"
echo "Frontend tasks: $FRONTEND_TASKS"
echo "Tests tasks:    $TESTS_TASKS"

TOTAL=$((BACKEND_TASKS + FRONTEND_TASKS + TESTS_TASKS))
if [ $TOTAL -eq 0 ]; then
    echo ""
    echo "ERROR: No tasks defined!"
    echo "Create task files in tasks/pending/<role>/"
    exit 1
fi

# 2. Commit and push tasks
echo ""
echo "--- Syncing Tasks to GitHub ---"
git add -A
if git diff --cached --quiet; then
    echo "No new changes to commit"
else
    git commit -m "[init] Night run: $TOTAL tasks"
    "$SCRIPTS_DIR/safe-push.sh"
fi

# 3. Start workers on remote machines
echo ""
echo "--- Starting Workers ---"

start_worker() {
    local host=$1
    local role=$2
    
    echo "Starting $role worker on $host..."
    ssh "$host" "cd ~/project && git pull && nohup ./scripts/worker.sh $role > /dev/null 2>&1 &"
    
    sleep 2
    if ssh "$host" "pgrep -f 'worker.sh $role'" > /dev/null; then
        echo "  ✓ $role worker running"
    else
        echo "  ✗ $role worker FAILED to start"
    fi
}

start_worker pc1 backend
start_worker pc2 frontend

# 4. Summary
echo ""
echo "=========================================="
echo "Night run started!"
echo ""
echo "Workers will stop at 06:00"
echo "Run ./scripts/morning-review.sh tomorrow"
echo ""
echo "Good night! 🌙"
echo "=========================================="
```

### scripts/morning-review.sh

```bash
#!/bin/bash
#===============================================
# Ralph Loops - Morning Review
#===============================================

REPO_DIR=~/project

echo "=========================================="
echo "Ralph Loops - Morning Review"
echo "$(date)"
echo "=========================================="

cd "$REPO_DIR"

# 1. Sync
echo ""
echo "--- Syncing ---"
git pull

# 2. Task Summary
echo ""
echo "--- Task Summary ---"
echo "Done (backend):    $(ls tasks/done/backend/*.md 2>/dev/null | wc -l || echo 0)"
echo "Done (frontend):   $(ls tasks/done/frontend/*.md 2>/dev/null | wc -l || echo 0)"
echo "Done (tests):      $(ls tasks/done/tests/*.md 2>/dev/null | wc -l || echo 0)"
echo "In-progress:       $(ls tasks/in-progress/*/*.md 2>/dev/null | wc -l || echo 0)"
echo "Pending:           $(ls tasks/pending/*/*.md 2>/dev/null | wc -l || echo 0)"

# 3. Results Summary
echo ""
echo "--- Results ---"
for f in results/*.md; do
    if [ -f "$f" ]; then
        name=$(basename "$f")
        status=$(grep "^Status:" "$f" | cut -d: -f2 | tr -d ' ')
        
        if [ "$status" = "SUCCESS" ]; then
            echo "  ✓ $name"
        else
            echo "  ✗ $name ($status)"
        fi
    fi
done

# 4. Recent Commits
echo ""
echo "--- Last Night's Commits ---"
git log --oneline --since="yesterday 20:00" --until="today 08:00" | head -20

# 5. Code Changes
echo ""
echo "--- Files Changed ---"
git diff --stat HEAD~10 HEAD -- src/ 2>/dev/null | tail -10

# 6. Worker Status
echo ""
echo "--- Worker Status ---"
for host in pc1 pc2; do
    if ssh "$host" "pgrep -f worker.sh" > /dev/null 2>&1; then
        echo "  $host: Still running"
    else
        echo "  $host: Stopped"
    fi
done

# 7. Recommendations
echo ""
echo "--- Actions ---"
echo "1. Review results:  less results/*.md"
echo "2. Check logs:      ssh pc1 'tail -100 ~/project/logs/backend*.log'"
echo "3. View code:       git diff HEAD~10 HEAD -- src/"
echo "4. Merge if OK:     git push origin main"
echo ""
echo "=========================================="
```

### scripts/watchdog.sh

```bash
#!/bin/bash
#===============================================
# Ralph Loops - Watchdog
#===============================================

REPO_DIR=~/project
ALERT_THRESHOLD_MINUTES=60
CHECK_INTERVAL=300  # 5 minutes

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [watchdog] $1"
}

send_alert() {
    local message="$1"
    log "ALERT: $message"
    
    # Option 1: Desktop notification (Linux)
    # notify-send "Ralph Loops Alert" "$message"
    
    # Option 2: Write to file
    echo "[$(date)] $message" >> "$REPO_DIR/logs/alerts.log"
    
    # Option 3: Email (configure mail command)
    # echo "$message" | mail -s "Ralph Loops Alert" you@email.com
}

cd "$REPO_DIR"

while true; do
    # Get last commit time
    LAST_COMMIT=$(git log -1 --format=%ct 2>/dev/null || echo 0)
    NOW=$(date +%s)
    DIFF_MINUTES=$(( (NOW - LAST_COMMIT) / 60 ))
    
    if [ $DIFF_MINUTES -gt $ALERT_THRESHOLD_MINUTES ]; then
        send_alert "No commits in the last ${DIFF_MINUTES} minutes!"
    else
        log "OK - Last commit ${DIFF_MINUTES} minutes ago"
    fi
    
    sleep $CHECK_INTERVAL
done
```

### scripts/manager-loop.sh (Phase 2)

```bash
#!/bin/bash
#===============================================
# Ralph Loops - Manager Loop (Phase 2)
#===============================================

# This script is for PHASE 2 only
# In Phase 1, use start-night.sh with predefined tasks

REPO_DIR=~/project
LOG_FILE="$REPO_DIR/logs/manager-$(date +%Y%m%d).log"
POLL_INTERVAL=300  # 5 minutes
STOP_HOUR=6

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [manager] $1" | tee -a "$LOG_FILE"
}

should_stop() {
    local hour=$(date +%H)
    [ "$hour" -ge "$STOP_HOUR" ] && [ "$hour" -lt 12 ]
}

cd "$REPO_DIR"
LAST_HASH=$(git rev-parse HEAD)

log "Manager started"

while ! should_stop; do
    git fetch origin main 2>> "$LOG_FILE"
    CURRENT_HASH=$(git rev-parse origin/main)
    
    if [ "$CURRENT_HASH" != "$LAST_HASH" ]; then
        log "Changes detected, analyzing..."
        git pull --rebase origin main
        
        # Find new results
        NEW_RESULTS=$(git diff --name-only "$LAST_HASH" "$CURRENT_HASH" | grep "^results/")
        
        if [ -n "$NEW_RESULTS" ]; then
            log "New results: $NEW_RESULTS"
            
            # Analyze with Claude and decide next task
            # (This is a simplified example)
            for result in $NEW_RESULTS; do
                STATUS=$(grep "^Status:" "$result" | cut -d: -f2 | tr -d ' ')
                
                if [ "$STATUS" = "FAILED" ]; then
                    log "Task failed, creating retry task..."
                    # Create retry task logic here
                fi
            done
        fi
        
        LAST_HASH=$CURRENT_HASH
    fi
    
    sleep $POLL_INTERVAL
done

log "Manager stopped (stop hour reached)"
```

## Task Template

### tasks/pending/backend/001-create-auth-api.md

```markdown
# Task: Create Auth API

## Description
Create a REST API for user authentication with JWT.

## Functional Requirements
- POST /api/auth/register - Register new user (email, password, name)
- POST /api/auth/login - Login, returns JWT token
- POST /api/auth/refresh - Refresh token
- GET /api/auth/me - Get current user details (requires JWT)

## Technical Requirements
- Node.js + Express
- JWT for authentication (jsonwebtoken)
- bcrypt for password hashing
- .env file for secrets

## Files to Create
- src/backend/auth/routes.js
- src/backend/auth/controller.js
- src/backend/auth/middleware.js
- src/backend/auth/utils.js

## Success Criteria
- [ ] Server starts without errors
- [ ] All endpoints respond
- [ ] Passwords are hashed
- [ ] JWT is created and verified
```

## Phased Approach

| Phase | What Works | When to Advance |
|-------|-----------|-----------------|
| **Phase 1** | Fixed task queue, no smart Manager | One night 8/8 |
| **Phase 2** | Manager checks results and reacts | 3 stable nights |
| **Phase 3** | Auto-fix loops + Docker | As needed |

## Success Criteria - Phase 1

### Required Tests (8/8)

| # | Criterion |
|---|-----------|
| 1 | SSH from manager to agents without password |
| 2 | Git clone works on all agents |
| 3 | worker.sh starts without errors |
| 4 | Agent takes task from pending/ |
| 5 | Agent moves to in-progress/ and pushes |
| 6 | Agent executes task with Gemini |
| 7 | Agent moves to done/ and writes result |
| 8 | Morning: commits + results visible on GitHub |

**Rule:** One night with 8/8 → Can add third agent or move to Phase 2.

## Current Progress

### Completed ✅
- Linux Mint on 2 PCs
- Sleep mode disabled
- Tailscale on all 3 machines
- Node.js on agents
- Gemini CLI installed & authenticated
- SSH Server on agents
- SSH key on Windows
- Passwordless SSH to both agents
- SSH config (pc1, pc2 aliases)
- GitHub repo created
- Git installed on agents
- Git identity configured
- SSH keys for GitHub
- Repo cloned to ~/project on both
- Folder structure created
- .gitignore created
- .gitkeep files added

### In Progress ⏳
- Create scripts in ~/project/scripts/
- Create config.json in ~/project/.ralph/
- Initial commit and push
- Pull on pc2
- Test worker.sh manually
- First night run

## Gemini Authentication - IMPORTANT

### OAuth Credentials
Gemini CLI uses OAuth authentication stored in `~/.gemini/oauth_creds.json`.

**Critical Rules:**
1. **NEVER delete `oauth_creds.json`** - Quota is tied to the Google account, not the credentials file
2. Deleting credentials does NOT reset quota - it just breaks authentication
3. Each Google account has its own separate quota

### Quota Management
- Free Gemini API has daily quota limits per Google account
- When quota is exhausted, you'll see: `TerminalQuotaError: You have exhausted your capacity`
- Quota resets after ~24 hours

### To Switch Google Accounts (for different quota):
```bash
# SSH into agent interactively
ssh -t pc1 "gemini"

# Complete OAuth flow with NEW Google account:
# 1. Open the URL shown in your browser
# 2. Sign in with a DIFFERENT Google account
# 3. Click "Allow"
# 4. Copy the authorization code
# 5. Paste it back in terminal
# 6. Type /exit

# Verify credentials saved
ssh pc1 "ls ~/.gemini/oauth_creds.json"
```

### Pre-flight Auth Check
The worker.sh script includes an authentication check that runs before processing tasks:
```bash
check_gemini_auth() {
    if timeout 30s gemini -p "Say OK" 2>&1 | grep -q "Please visit"; then
        log "ERROR: Gemini authentication required"
        return 1
    fi
    if [ ! -f ~/.gemini/oauth_creds.json ]; then
        log "ERROR: OAuth credentials missing"
        return 1
    fi
    return 0
}
```

This prevents workers from picking up tasks when authentication is broken.
