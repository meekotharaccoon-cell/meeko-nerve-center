# Ralph Loops Workflow

## Daily Workflow

### Evening (Before Bed)

1. **Create tasks** in `tasks/pending/ROLE/`
2. **Commit and push** to GitHub
3. **Run start-night.sh** to launch workers

```bash
# From manager machine
ssh pc1 "cd ~/project && git pull && nohup ./scripts/worker.sh backend > /dev/null 2>&1 &"
ssh pc2 "cd ~/project && git pull && nohup ./scripts/worker.sh frontend > /dev/null 2>&1 &"
ssh pc3 "cd ~/project && git pull && nohup ./scripts/worker.sh tests > /dev/null 2>&1 &"
```

### Morning (Wake Up)

1. **Run morning-review.sh** to see what happened
2. **Check results/** for detailed reports
3. **Review generated code** in `src/`
4. **Stop workers** if still running

```bash
# From manager machine
ssh pc1 "cd ~/project && git pull && ./scripts/morning-review.sh"
ssh pc1 "pkill -f worker.sh"
```

---

## Worker Lifecycle

Each worker (agent) follows this loop:

```
┌─────────────────────────────────────────────┐
│                START                         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  1. git pull (sync with remote)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  2. Check for tasks in pending/ROLE/        │
│     If none → sleep 60s → loop              │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  3. Claim task: move to in-progress/ROLE/   │
│     Commit: "claim: task-name"              │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  4. Execute task with Gemini CLI            │
│     - Read task requirements                │
│     - Generate code                         │
│     - Write files to src/                   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  5. Complete task: move to done/ROLE/       │
│     Create result file in results/          │
│     Commit: "complete: task-name"           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  6. Push with safe-push.sh (handles retries)│
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  7. Check stop conditions:                  │
│     - Time > 6:00 AM?                       │
│     - Tasks completed > 10?                 │
│     If yes → EXIT                           │
│     If no → loop to step 1                  │
└─────────────────────────────────────────────┘
```

---

## Task Flow

```
tasks/pending/backend/001-task.md
         │
         │ (worker claims)
         ▼
tasks/in-progress/backend/001-task.md
         │
         │ (worker completes)
         ▼
tasks/done/backend/001-task.md
         +
results/001-task-result.md
         +
src/backend/... (generated code)
```

---

## Git Coordination

### Why Git Works

- Each role has its own folder → no file conflicts
- safe-push.sh handles push race conditions
- Atomic commits: claim, complete, push
- Remote repository is single source of truth

### Commit Message Convention

```
claim: [task-name]          # Worker starts task
complete: [task-name]       # Worker finishes task
fix: [description]          # Manual fixes
task: [description]         # Adding new tasks
```

---

## Troubleshooting Workflow Issues

### Task Stuck in in-progress/

**Cause:** Worker crashed or timed out

**Fix:**
1. Move task back to `pending/`
2. Commit and push
3. Restart worker

### Multiple Workers Claiming Same Task

**Cause:** Race condition (rare with role folders)

**Fix:**
- The first commit wins
- Other workers will fail to push
- safe-push.sh will pull and retry with different task

### No Tasks Being Processed

**Check:**
1. Are tasks in the correct `pending/ROLE/` folder?
2. Is the worker running? `pgrep -f worker.sh`
3. Is Gemini authenticated? Test with `gemini -p "test"`
4. Check logs: `tail -100 ~/project/logs/ROLE-*.log`
