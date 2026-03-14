# Ralph Loops — Implementation Plan v1.0

**Created:** February 4, 2026
**Updated:** February 4, 2026
**Status:** Sprint 1 COMPLETE

---

## Executive Summary

This plan addresses **34 open issues** across 4 sprints, transforming Ralph Loops from a working prototype into a reliable autonomous coding system.

**Current State:** Phase 1 complete, Sprint 1 complete, Phase 2 ready for testing
**Target State:** Fully autonomous overnight runs with learning capabilities and remote control

---

## Sprint 1 Completion Notes

**Completed:** February 4, 2026

### Changes Made:

1. **worker.sh v8** - Dual AI + Rate Limits + Validation
   - Claude primary, Gemini fallback (Gemini CLI cannot write files in prompt mode)
   - `execute_with_ai()` with exponential backoff for 429 errors
   - `validate_task()` runs validation commands from task files
   - Result files now show: AI Used, Execution status, Validation status

2. **start-night.sh v3** - Comprehensive Pre-Flight Checks
   - 5-point preflight: git clean, SSH, AI availability, tasks exist, scripts executable
   - Fails fast with clear error messages
   - Continues with warnings if non-critical issues

3. **manager-loop.sh v4** - PID Lock
   - `acquire_lock()` prevents duplicate managers
   - Stale lock detection and cleanup
   - Lock released on exit via trap

4. **Documentation Created:**
   - `docs/gemini-auth-upgrade.md` - OAuth setup guide
   - `docs/task-template-with-validation.md` - New task format with validation

### Remaining Manual Step:
- [ ] Run Gemini OAuth on each agent (requires physical/SSH access)
## Execution Strategy

Work in **sprints** with clear deliverables. Each sprint ends with a stable, testable state.

| Sprint | Focus | Duration | Prerequisite |
|--------|-------|----------|--------------|
| Sprint 1 | Foundation Fixes (Critical) | 3-5 days | None |
| Sprint 2 | Smart Manager | 5-7 days | Sprint 1 |
| Sprint 3 | Smart Skills | 5-7 days | Sprint 2 |
| Sprint 4 | Remote Access (Telegram) | 3-5 days | Sprint 2 |

---

## Sprint 1: Foundation Fixes (Critical)

**Goal:** Make overnight runs reliable
**Duration:** 3-5 days
**Prerequisite:** None

### 1.1 Gemini Auth Upgrade (Issue #1)

**Problem:** API Key limits to ~20-250 RPD. Google Login gives 1,000 RPD.

**Steps:**
```bash
# For each agent (PC1, PC2, PC3):
1. SSH to agent
2. Run: gemini (interactive mode)
3. Complete Google OAuth in browser
4. Verify: ls ~/.gemini/oauth_creds.json
5. Test: gemini -p "Say hello"
```

**Success Criteria:**
- [ ] All 3 agents authenticated via Google Login
- [ ] Each agent can run 50+ prompts without rate limit

---

### 1.2 Rate Limit Handling (Issue #4)

**Problem:** 429 at 2 AM kills the night with false FAILED status.

**File:** `scripts/worker.sh`

**Add function:**
```bash
execute_with_retry() {
    local task_content="$1"
    local max_retries=5
    local base_delay=60

    for attempt in $(seq 1 $max_retries); do
        log "Execution attempt $attempt/$max_retries"

        local output
        local exit_code
        output=$(timeout $TASK_TIMEOUT gemini -p "$task_content" --yolo 2>&1) || exit_code=$?

        # Check for rate limit
        if echo "$output" | grep -qi "429\|rate.limit\|quota\|resource.exhausted"; then
            local delay=$((base_delay * attempt + RANDOM % 30))
            log "RATE LIMITED: Waiting ${delay}s before retry (attempt $attempt)"
            sleep $delay
            continue
        fi

        # Real success or failure
        echo "$output"
        return ${exit_code:-0}
    done

    log "ERROR: Max retries exceeded due to rate limiting"
    return 1
}
```

**Update execute_task() to use execute_with_retry()**

**Success Criteria:**
- [ ] 429 triggers retry with exponential backoff
- [ ] Logs clearly show "RATE LIMITED" vs "FAILED"
- [ ] Worker survives overnight rate limits

---

### 1.3 Task Validation Section (Issue #2)

**Problem:** No way to verify code actually works.

**New task format:**
```markdown
# Task: Create Orders API

## Description
...

## Requirements
...

## Files to Create
...

## Validation
```bash
cd src/backend/orders
npm install
node server.js &
SERVER_PID=$!
sleep 3
curl -sf http://localhost:3001/api/health | grep -q "ok"
RESULT=$?
kill $SERVER_PID 2>/dev/null
exit $RESULT
```

## Success Criteria
...
```

**Success Criteria:**
- [ ] Task template documented with Validation section
- [ ] 3 example tasks created with validation commands

---

### 1.4 worker.sh validate_task() (Issue #3)

**Problem:** SUCCESS means Gemini exited, not code works.

**File:** `scripts/worker.sh`

**Add function:**
```bash
extract_validation() {
    local task_file="$1"
    # Extract content between ## Validation and next ## or EOF
    sed -n '/^## Validation/,/^## \|^$/p' "$task_file" | \
        sed '1d;/^## /d;/^```/d' | \
        grep -v '^$'
}

validate_task() {
    local task_file="$1"
    local validation_script
    validation_script=$(extract_validation "$task_file")

    if [ -z "$validation_script" ]; then
        log "NO_VALIDATION: No validation section in task"
        echo "NO_VALIDATION"
        return 0
    fi

    log "Running validation..."
    local validation_output
    local validation_exit

    # Run with timeout, capture output
    validation_output=$(timeout 120s bash -c "$validation_script" 2>&1) || validation_exit=$?

    if [ "${validation_exit:-0}" -eq 0 ]; then
        log "VALIDATION PASSED"
        echo "PASSED"
    else
        log "VALIDATION FAILED: $validation_output"
        echo "FAILED"
    fi

    # Store output for result file
    VALIDATION_OUTPUT="$validation_output"
    return ${validation_exit:-0}
}
```

**Update complete_task() to include 3 fields:**
```bash
complete_task() {
    local task_file="$1"
    local exec_status="$2"      # SUCCESS/FAILED (Gemini exit)
    local valid_status="$3"     # PASSED/FAILED/NO_VALIDATION

    local result_file="results/${task_name%.md}-result.md"

    {
        echo "# Result: $task_name"
        echo "Agent: $ROLE"
        echo "Execution: $exec_status"
        echo "Validation: $valid_status"
        echo "Started: $TASK_START_TIME"
        echo "Finished: $(date)"
        echo ""
        if [ -n "$VALIDATION_OUTPUT" ]; then
            echo "## Validation Output"
            echo '```'
            echo "$VALIDATION_OUTPUT"
            echo '```'
        fi
        echo ""
        echo "## Log (last 50 lines)"
        echo '```'
        tail -50 "$LOG_FILE"
        echo '```'
    } > "$result_file"
    ...
}
```

**Success Criteria:**
- [ ] worker.sh extracts and runs validation
- [ ] Result files show 3 statuses: Execution, Validation, Output
- [ ] Failed validation doesn't crash worker

---

### 1.5 Pre-Flight Checks (Issue #12)

**File:** `scripts/start-night.sh`

**Add at beginning:**
```bash
preflight_check() {
    local errors=0

    echo "Running pre-flight checks..."

    # 1. Uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "ERROR: Uncommitted changes exist"
        git status --short
        errors=$((errors + 1))
    else
        echo "OK: Working directory clean"
    fi

    # 2. SSH to all agents
    for agent in pc1 pc2 pc3; do
        if timeout 10s ssh "$agent" "echo ok" >/dev/null 2>&1; then
            echo "OK: SSH to $agent"
        else
            echo "ERROR: Cannot SSH to $agent"
            errors=$((errors + 1))
        fi
    done

    # 3. Gemini works on agents
    for agent in pc1 pc2 pc3; do
        if timeout 30s ssh "$agent" "gemini -p 'say ok'" 2>&1 | grep -qi "ok"; then
            echo "OK: Gemini on $agent"
        else
            echo "WARN: Gemini test failed on $agent (may be OK)"
        fi
    done

    # 4. Tasks exist
    local task_count=$(find tasks/pending -name "*.md" ! -name ".gitkeep" | wc -l)
    if [ "$task_count" -gt 0 ]; then
        echo "OK: $task_count pending tasks"
    else
        echo "ERROR: No pending tasks"
        errors=$((errors + 1))
    fi

    # 5. Scripts executable
    if [ -x scripts/worker.sh ]; then
        echo "OK: Scripts executable"
    else
        echo "ERROR: Scripts not executable"
        errors=$((errors + 1))
    fi

    if [ "$errors" -gt 0 ]; then
        echo ""
        echo "PREFLIGHT FAILED: $errors errors"
        exit 1
    fi

    echo ""
    echo "All pre-flight checks passed"
}

# Call at start
preflight_check
```

**Success Criteria:**
- [ ] start-night.sh fails fast if problems detected
- [ ] Clear error messages for each check

---

### 1.6 PID Lock for Manager (Issue #13)

**Problem:** Duplicate managers cause git conflicts.

**File:** `scripts/manager-loop.sh`

**Add at beginning:**
```bash
LOCK_FILE="/tmp/ralph-manager.pid"

acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local old_pid=$(cat "$LOCK_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "ERROR: Manager already running (PID $old_pid)"
            echo "Kill it first: kill $old_pid"
            exit 1
        else
            echo "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT
    echo "Lock acquired (PID $$)"
}

# Call at start
acquire_lock
```

**Success Criteria:**
- [ ] Cannot start two managers
- [ ] Lock cleaned up on exit
- [ ] Stale locks handled

---

### Sprint 1 Deliverables

| Item | Deliverable |
|------|-------------|
| Gemini Auth | All 3 agents on Google Login |
| worker.sh | v7 with retry + validation |
| start-night.sh | With pre-flight checks |
| manager-loop.sh | With PID lock |
| Task template | With Validation section |

**Test:** Run one overnight with 5 tasks, verify:
- Rate limits handled gracefully
- Validation runs and reports accurately
- No duplicate manager issues

---

## Sprint 2: Smart Manager

**Goal:** Manager auto-reviews and creates fix tasks
**Duration:** 5-7 days
**Prerequisite:** Sprint 1 complete

### 2.1 Evidence-Based Review (Issue #6)

**File:** `scripts/analyze-result.sh`

**Update Claude API prompt:**
```bash
build_review_prompt() {
    local task_file="$1"
    local result_file="$2"
    local diff_content="$3"

    cat << EOF
You are reviewing an AI agent's work. Analyze and return JSON.

TASK:
$(cat "$task_file")

RESULT:
$(cat "$result_file")

CODE CHANGES:
$diff_content

RULES:
1. If "Validation: FAILED" → verdict MUST be "NEEDS_FIX"
2. If "Validation: NO_VALIDATION" → APPROVED only for docs/config tasks
3. If "Validation: PASSED" → can be APPROVED if code looks correct
4. If security issue found → verdict is "NEEDS_HUMAN"

Return ONLY valid JSON:
{
  "verdict": "APPROVED|NEEDS_FIX|NEEDS_HUMAN",
  "summary": "One sentence summary",
  "issues": ["issue1", "issue2"],
  "fix_instructions": "If NEEDS_FIX, specific instructions"
}
EOF
}
```

**Success Criteria:**
- [ ] FAILED validation always triggers NEEDS_FIX
- [ ] NO_VALIDATION handled appropriately
- [ ] Clear fix instructions generated

---

### 2.2 Auto-Generate Fix Tasks (Issue #7)

**File:** `scripts/manager-loop.sh` (or new `scripts/create-fix-task.sh`)

```bash
create_fix_task() {
    local original_task="$1"
    local result_file="$2"
    local fix_instructions="$3"
    local attempt=${4:-1}

    # Check retry limit
    if [ "$attempt" -gt 3 ]; then
        log "Max fix attempts reached for $original_task"
        move_to_review "$original_task" "Max retries exceeded"
        return 1
    fi

    local task_name=$(basename "$original_task" .md)
    local fix_task="tasks/pending/${ROLE}/${task_name}-fix${attempt}.md"

    cat > "$fix_task" << EOF
# Task: Fix ${task_name} (Attempt $attempt)

## Context
This is a fix task. The original task failed validation.

## Original Task
$(cat "$original_task")

## What Failed
$(grep -A 20 "## Validation Output" "$result_file" || echo "See result file")

## Fix Instructions
$fix_instructions

## IMPORTANT
- Do NOT rewrite everything from scratch
- Only fix the specific issue mentioned above
- Keep existing working code intact

## Validation
$(grep -A 20 "## Validation" "$original_task" || echo "# Same as original")
EOF

    # Track attempt count
    echo "$task_name:$attempt" >> "$REPO_DIR/.ralph/fix-attempts.txt"

    git add "$fix_task"
    git commit -m "[manager] Created fix task: ${task_name}-fix${attempt}"
    safe_push

    log "Created fix task: $fix_task"
}
```

**Success Criteria:**
- [ ] Fix tasks created automatically
- [ ] Original context preserved
- [ ] Max 3 retries enforced
- [ ] Clear "do not rewrite" instruction

---

### 2.3 Auto-Generate Follow-Up Tasks (Issue #8)

**File:** `scripts/analyze-result.sh`

**Add to Claude prompt:**
```
Additionally, if this task is APPROVED and there's a logical next step,
suggest a follow-up task:

{
  "verdict": "APPROVED",
  "follow_up": {
    "suggested": true,
    "role": "tests",
    "title": "Add tests for Orders API",
    "description": "Create curl-based tests for the Orders API endpoints"
  }
}
```

**File:** `scripts/manager-loop.sh`

```bash
create_follow_up_task() {
    local follow_up_json="$1"

    local role=$(echo "$follow_up_json" | jq -r '.role')
    local title=$(echo "$follow_up_json" | jq -r '.title')
    local description=$(echo "$follow_up_json" | jq -r '.description')

    # Generate task number
    local next_num=$(ls tasks/pending/$role/*.md 2>/dev/null | wc -l)
    next_num=$((next_num + 1))
    local padded=$(printf "%03d" $next_num)

    local task_file="tasks/pending/$role/${padded}-$(echo "$title" | tr ' ' '-' | tr '[:upper:]' '[:lower:]').md"

    cat > "$task_file" << EOF
# Task: $title

## Description
$description

## Context
Auto-generated follow-up task from Manager.

## Requirements
- TBD by agent

## Validation
\`\`\`bash
# Add appropriate validation
echo "TODO: Add validation"
\`\`\`
EOF

    git add "$task_file"
    git commit -m "[manager] Created follow-up: $title"
    safe_push

    log "Created follow-up task: $task_file"
}
```

**Success Criteria:**
- [ ] Manager suggests follow-ups
- [ ] Follow-up tasks created in correct role folder
- [ ] Human can review/edit before next run

---

### 2.4 Context Preservation (Issue #9)

**Approach:** Store task history in `.ralph/context/` and inject into prompts.

**File:** `scripts/manager-utils.sh`

```bash
save_task_context() {
    local task_name="$1"
    local result_file="$2"
    local verdict="$3"

    local context_dir="$REPO_DIR/.ralph/context"
    mkdir -p "$context_dir"

    local context_file="$context_dir/${task_name}.json"

    cat > "$context_file" << EOF
{
  "task": "$task_name",
  "completed": "$(date -Iseconds)",
  "verdict": "$verdict",
  "result_file": "$result_file",
  "attempts": $(grep -c "^${task_name}:" .ralph/fix-attempts.txt 2>/dev/null || echo 0)
}
EOF
}

get_related_context() {
    local task_file="$1"
    local context=""

    # Find related completed tasks (same feature/number prefix)
    local prefix=$(basename "$task_file" | cut -d'-' -f1)

    for ctx in .ralph/context/${prefix}-*.json; do
        [ -f "$ctx" ] || continue
        context+="Previous: $(jq -r '.task' "$ctx") - $(jq -r '.verdict' "$ctx")\n"
    done

    echo -e "$context"
}
```

**Success Criteria:**
- [ ] Task history saved after each review
- [ ] Related context injected into fix tasks
- [ ] Context kept lean (not entire codebase)

---

### 2.5 Packup Mode (Issue #10)

**File:** `scripts/manager-loop.sh`

```bash
DAILY_REVIEW_COUNT=0
MAX_DAILY_REVIEWS=50
PACKUP_THRESHOLD=0.75  # 75%

check_packup_mode() {
    local usage_ratio=$(echo "scale=2; $DAILY_REVIEW_COUNT / $MAX_DAILY_REVIEWS" | bc)

    if (( $(echo "$usage_ratio >= $PACKUP_THRESHOLD" | bc -l) )); then
        return 0  # Should enter packup
    fi
    return 1
}

enter_packup_mode() {
    log "PACKUP MODE: Credit threshold reached ($DAILY_REVIEW_COUNT/$MAX_DAILY_REVIEWS)"

    # 1. Stop creating new tasks
    log "Stopping new task creation"

    # 2. Wait for in-progress tasks
    log "Waiting for in-progress tasks to complete..."
    local wait_count=0
    while [ "$(find tasks/in-progress -name '*.md' ! -name '.gitkeep' | wc -l)" -gt 0 ]; do
        sleep 60
        wait_count=$((wait_count + 1))
        if [ "$wait_count" -gt 30 ]; then
            log "Timeout waiting for in-progress tasks"
            break
        fi
    done

    # 3. Final sync
    git pull --rebase origin main

    # 4. Generate night report
    generate_night_report

    # 5. Stop agents
    log "Stopping agents..."
    for agent in pc1 pc2 pc3; do
        ssh "$agent" "pkill -f worker.sh" 2>/dev/null || true
    done

    log "PACKUP COMPLETE"
    exit 0
}

generate_night_report() {
    local report="logs/night-report-$(date +%Y%m%d).md"

    {
        echo "# Night Report - $(date)"
        echo ""
        echo "## Summary"
        echo "- Reviews performed: $DAILY_REVIEW_COUNT"
        echo "- Approved: $(ls tasks/approved/*/*.md 2>/dev/null | wc -l)"
        echo "- Needs Fix: $(find tasks/pending -name '*-fix*.md' | wc -l)"
        echo "- Needs Human: $(ls tasks/review/*/*.md 2>/dev/null | wc -l)"
        echo ""
        echo "## Recent Commits"
        git log --oneline --since="yesterday 20:00" | head -20
        echo ""
        echo "## Files Changed"
        git diff --stat HEAD~20 HEAD -- src/
    } > "$report"

    git add "$report"
    git commit -m "[manager] Night report"
    safe_push
}

# In main loop:
if check_packup_mode; then
    enter_packup_mode
fi
```

**Success Criteria:**
- [ ] Manager enters packup at 75% usage
- [ ] In-progress tasks allowed to finish
- [ ] Night report generated
- [ ] Agents stopped gracefully

---

### 2.6 morning-review.sh v2 (Issue #14)

**File:** `scripts/morning-review.sh`

```bash
#!/bin/bash
# Morning Review v2

REPO_DIR="${1:-$(pwd)}"
cd "$REPO_DIR"

echo "═══════════════════════════════════════════════════════"
echo "   Ralph Loops — Morning Review"
echo "   $(date)"
echo "═══════════════════════════════════════════════════════"
echo ""

# Sync first
git pull --rebase origin main 2>/dev/null

# Task Summary
echo "TASK SUMMARY"
echo "───────────────────────────────────────────────────────"
printf "  %-20s %s\n" "Pending:" "$(find tasks/pending -name '*.md' ! -name '.gitkeep' | wc -l)"
printf "  %-20s %s\n" "In-Progress:" "$(find tasks/in-progress -name '*.md' ! -name '.gitkeep' | wc -l)"
printf "  %-20s %s\n" "Done:" "$(find tasks/done -name '*.md' ! -name '.gitkeep' | wc -l)"
printf "  %-20s %s\n" "Approved:" "$(find tasks/approved -name '*.md' ! -name '.gitkeep' 2>/dev/null | wc -l)"
printf "  %-20s %s\n" "Needs Human:" "$(find tasks/review -name '*.md' ! -name '.gitkeep' 2>/dev/null | wc -l)"
echo ""

# Results Summary
echo "OVERNIGHT RESULTS"
echo "───────────────────────────────────────────────────────"
for result in results/*-result.md; do
    [ -f "$result" ] || continue
    name=$(basename "$result" -result.md)
    exec_status=$(grep "^Execution:" "$result" 2>/dev/null | cut -d: -f2 | tr -d ' ')
    valid_status=$(grep "^Validation:" "$result" 2>/dev/null | cut -d: -f2 | tr -d ' ')

    if [ "$valid_status" = "PASSED" ]; then
        icon="[OK]"
    elif [ "$valid_status" = "FAILED" ]; then
        icon="[FAIL]"
    else
        icon="[WARN]"
    fi

    printf "  %s %-30s Exec: %-8s Valid: %s\n" "$icon" "$name" "$exec_status" "$valid_status"
done
echo ""

# Needs Human Attention
human_tasks=$(find tasks/review -name '*.md' ! -name '.gitkeep' 2>/dev/null)
if [ -n "$human_tasks" ]; then
    echo "NEEDS YOUR ATTENTION"
    echo "───────────────────────────────────────────────────────"
    for task in $human_tasks; do
        echo "  - $(basename "$task")"
    done
    echo ""
fi

# New Learned Lessons (Phase 3)
if [ -d ".ralph/skills/learned" ]; then
    new_lessons=$(find .ralph/skills/learned -name '*.md' -mtime 0 2>/dev/null)
    if [ -n "$new_lessons" ]; then
        echo "NEW LESSONS LEARNED"
        echo "───────────────────────────────────────────────────────"
        for lesson in $new_lessons; do
            echo "  $(basename "$lesson"):"
            tail -5 "$lesson" | sed 's/^/    /'
        done
        echo ""
    fi
fi

# Recent Commits
echo "OVERNIGHT COMMITS"
echo "───────────────────────────────────────────────────────"
git log --oneline --since="yesterday 20:00" --until="today 08:00" | head -15
echo ""

# Code Stats
echo "CODE CHANGES"
echo "───────────────────────────────────────────────────────"
git diff --stat HEAD~10 HEAD -- src/ 2>/dev/null | tail -10
echo ""

# Agent Status
echo "AGENT STATUS"
echo "───────────────────────────────────────────────────────"
for agent in pc1 pc2 pc3; do
    if ssh "$agent" "pgrep -f worker.sh" >/dev/null 2>&1; then
        printf "  %-10s %s\n" "$agent:" "Running"
    else
        printf "  %-10s %s\n" "$agent:" "Stopped"
    fi
done
echo ""

# Recommendations
echo "RECOMMENDED ACTIONS"
echo "───────────────────────────────────────────────────────"
if [ -n "$human_tasks" ]; then
    echo "  1. Review tasks in tasks/review/"
fi
if [ "$(find tasks/pending -name '*-fix*.md' | wc -l)" -gt 0 ]; then
    echo "  2. Check fix tasks — some items needed multiple attempts"
fi
echo "  3. Create new tasks for tonight"
echo "  4. Run: git add -A && git commit -m 'Morning review' && git push"
echo ""
echo "═══════════════════════════════════════════════════════"
```

**Success Criteria:**
- [ ] Shows execution AND validation status
- [ ] Highlights tasks needing human attention
- [ ] Shows new learned lessons
- [ ] Clear recommendations

---

### Sprint 2 Deliverables

| Item | Deliverable |
|------|-------------|
| analyze-result.sh | Evidence-based review with validation check |
| manager-loop.sh | v2 with fix tasks, follow-ups, packup mode |
| manager-utils.sh | Context preservation functions |
| morning-review.sh | v2 with full metrics |

**Test:** Run 3 consecutive nights, verify:
- Fix tasks created for failures
- Fix loop runs until approved or max retries
- Packup mode triggers correctly
- Morning review shows complete picture

---

## Sprint 3: Smart Skills

**Goal:** Agents learn and specialize
**Duration:** 5-7 days
**Prerequisite:** Sprint 2 complete (stable Manager)

### 3.1 Create Skill Directory Structure

```bash
mkdir -p .ralph/skills/{common,backend,frontend,tests,learned}
touch .ralph/skills/learned/{backend,frontend,tests}-lessons.md
```

### 3.2 Write Common Skills

**File:** `.ralph/skills/common/01-project-context.md`
```markdown
# Project Context

## Tech Stack
- Backend: Node.js + Express
- Frontend: HTML/CSS/JavaScript (vanilla)
- Tests: Bash + curl

## Architecture
- Backend runs on PC1 (100.x.x.1:3001)
- Frontend runs on PC2 (100.x.x.2:3000)
- Tests run on PC3

## File Structure
- src/backend/<feature>/ — Backend code
- src/frontend/<feature>/ — Frontend code
- src/tests/<feature>/ — Test scripts
```

**File:** `.ralph/skills/common/02-code-standards.md`
```markdown
# Code Standards

## General
- Use clear, descriptive variable names
- Add error handling for all external calls
- Log errors to stderr, info to stdout

## Git
- Do not commit node_modules
- Do not commit .env files
- Create package.json for each backend service
```

**File:** `.ralph/skills/common/03-workflow-rules.md`
```markdown
# Workflow Rules

## File Paths
- Always use paths relative to project root
- Create files in exact paths specified in task
- Never create files outside src/ directory

## Dependencies
- Run npm install before npm start
- Check if port is in use before binding
- Kill any processes you start
```

### 3.3 Write Backend Skills

**File:** `.ralph/skills/backend/01-api-patterns.md`
```markdown
# Backend API Patterns

## Server Setup — MANDATORY
- Bind to 0.0.0.0 (NEVER localhost or 127.0.0.1)
- Enable CORS: app.use(cors({ origin: '*' }))
- Parse JSON: app.use(express.json())
- Default port: 3001 (or as specified in task)
- Add health endpoint: GET /api/health → { "status": "ok" }

## REST Conventions
- GET /api/resource — list all (200)
- GET /api/resource/:id — get one (200, 404)
- POST /api/resource — create (201)
- PUT /api/resource/:id — update (200, 404)
- DELETE /api/resource/:id — delete (204, 404)

## Response Format
Always return JSON:
{
  "success": true,
  "data": { ... }
}

Or on error:
{
  "success": false,
  "error": "Error message"
}

## Error Handling
- Wrap routes in try/catch
- Return proper HTTP status codes
- Never expose stack traces
```

**File:** `.ralph/skills/backend/02-security.md`
```markdown
# Security Patterns

## Input Validation
- Validate all user input
- Sanitize before database operations
- Reject unexpected fields

## Authentication (if required)
- Use JWT tokens
- Store secrets in environment variables
- Never log passwords or tokens
```

### 3.4 Write Frontend Skills

**File:** `.ralph/skills/frontend/01-ui-patterns.md`
```markdown
# Frontend UI Patterns

## HTML Structure
- Use semantic HTML5 elements
- Include viewport meta tag
- Link CSS in head, JS before </body>

## Styling
- Mobile-first approach
- Use CSS Grid or Flexbox for layouts
- Keep styles in separate .css file
```

**File:** `.ralph/skills/frontend/02-api-consumption.md`
```markdown
# API Consumption

## Backend URLs
- NEVER use localhost
- Use Tailscale IP: http://100.x.x.1:3001
- Always include /api/ prefix

## Fetch Pattern
async function fetchData() {
    try {
        const response = await fetch('http://100.x.x.1:3001/api/endpoint');
        if (!response.ok) throw new Error('Network error');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch failed:', error);
        showError('Could not load data');
    }
}

## State Handling
- Show loading indicator during fetch
- Handle errors gracefully with user message
- Update UI only after successful response
```

### 3.5 Write Tests Skills

**File:** `.ralph/skills/tests/01-test-design.md`
```markdown
# Test Design

## Self-Contained Tests
Every test script must:
1. Start any servers it needs
2. Run the tests
3. Kill the servers
4. Exit with proper code

## Template
#!/bin/bash
set -e

# Start server
cd src/backend/feature
npm install
node server.js &
SERVER_PID=$!
sleep 3

# Run tests
PASSED=0
FAILED=0

# Test 1
if curl -sf http://localhost:3001/api/health | grep -q "ok"; then
    echo "PASS: Health check"
    PASSED=$((PASSED + 1))
else
    echo "FAIL: Health check"
    FAILED=$((FAILED + 1))
fi

# Cleanup
kill $SERVER_PID

# Report
echo "Results: $PASSED passed, $FAILED failed"
[ $FAILED -eq 0 ]
```

### 3.6 Update worker.sh with build_prompt()

**File:** `scripts/worker.sh`

```bash
build_prompt() {
    local task_file="$1"
    local prompt=""
    local word_count=0
    local max_words=2000

    # 1. Common skills
    for skill in "$REPO_DIR/.ralph/skills/common/"*.md; do
        [ -f "$skill" ] || continue
        local content=$(cat "$skill")
        local words=$(echo "$content" | wc -w)
        if [ $((word_count + words)) -lt $max_words ]; then
            prompt+="$content"$'\n\n'
            word_count=$((word_count + words))
        fi
    done

    # 2. Role-specific skills
    for skill in "$REPO_DIR/.ralph/skills/$ROLE/"*.md; do
        [ -f "$skill" ] || continue
        local content=$(cat "$skill")
        local words=$(echo "$content" | wc -w)
        if [ $((word_count + words)) -lt $max_words ]; then
            prompt+="$content"$'\n\n'
            word_count=$((word_count + words))
        fi
    done

    # 3. Learned lessons
    local learned="$REPO_DIR/.ralph/skills/learned/${ROLE}-lessons.md"
    if [ -f "$learned" ]; then
        local content=$(cat "$learned")
        local words=$(echo "$content" | wc -w)
        if [ $((word_count + words)) -lt $max_words ]; then
            prompt+="$content"$'\n\n'
            word_count=$((word_count + words))
        fi
    fi

    log "Loaded skills: $word_count words"

    # 4. The actual task
    prompt+="---"$'\n'
    prompt+="# YOUR TASK — Execute the following:"$'\n\n'
    prompt+="$(cat "$task_file")"

    echo "$prompt"
}

execute_task() {
    local task_file="$1"
    local full_prompt
    full_prompt=$(build_prompt "$task_file")

    cd "$REPO_DIR"

    # Use execute_with_retry from Sprint 1
    if execute_with_retry "$full_prompt"; then
        return 0
    else
        return $?
    fi
}
```

### 3.7 Add Lesson Extraction to Manager

**File:** `scripts/analyze-result.sh`

**Add to Claude prompt:**
```
Additionally, if this task FAILED, identify whether it reveals a
REPEATABLE pattern that future tasks should avoid.

If yes, include a "lesson" field:
{
  "verdict": "NEEDS_FIX",
  "lesson": {
    "pattern": "Express POST body parsing",
    "rule": "Always add app.use(express.json()) before route definitions",
    "role": "backend"
  }
}

Only include a lesson if it's genuinely reusable.
Do NOT include lessons for typos or one-off errors.
```

**File:** `scripts/manager-loop.sh`

```bash
append_lesson() {
    local role="$1"
    local pattern="$2"
    local rule="$3"
    local source_task="$4"

    local lessons_file="$REPO_DIR/.ralph/skills/learned/${role}-lessons.md"

    # Check if pattern already exists
    if grep -qi "$pattern" "$lessons_file" 2>/dev/null; then
        log "Lesson already exists: $pattern"
        return 0
    fi

    # Check lesson count (max 20)
    local count=$(grep -c "^## " "$lessons_file" 2>/dev/null || echo 0)
    if [ "$count" -ge 20 ]; then
        log "Max lessons reached, archiving oldest"
        # Archive to learned/archive/
        mkdir -p "$REPO_DIR/.ralph/skills/learned/archive"
        head -20 "$lessons_file" >> "$REPO_DIR/.ralph/skills/learned/archive/${role}-archived.md"
        tail -n +21 "$lessons_file" > "${lessons_file}.tmp"
        mv "${lessons_file}.tmp" "$lessons_file"
    fi

    # Append new lesson
    cat >> "$lessons_file" << EOF

## $(date +%Y-%m-%d): $pattern
$rule
Source: $source_task
EOF

    git add "$lessons_file"
    git commit -m "[manager] Learned: $pattern"
    safe_push

    log "Appended lesson: $pattern"
}
```

### 3.8 Skills Metrics

**File:** `.ralph/skills/metrics.json`

```bash
update_skill_metrics() {
    local metrics_file="$REPO_DIR/.ralph/skills/metrics.json"

    local total=$(find results -name "*-result.md" | wc -l)
    local passed=$(grep -l "Validation: PASSED" results/*-result.md 2>/dev/null | wc -l)
    local failed=$(grep -l "Validation: FAILED" results/*-result.md 2>/dev/null | wc -l)
    local lessons=$(grep -c "^## " .ralph/skills/learned/*.md 2>/dev/null || echo 0)

    cat > "$metrics_file" << EOF
{
  "updated": "$(date -Iseconds)",
  "tasks_total": $total,
  "tasks_passed": $passed,
  "tasks_failed": $failed,
  "pass_rate": "$(echo "scale=0; $passed * 100 / $total" | bc)%",
  "lessons_total": $lessons
}
EOF
}
```

---

### Sprint 3 Deliverables

| Item | Deliverable |
|------|-------------|
| .ralph/skills/ | Directory structure with all skill files |
| worker.sh | v8 with build_prompt() |
| analyze-result.sh | Lesson extraction |
| manager-loop.sh | Lesson appending |
| metrics.json | Skill effectiveness tracking |

**Test:** Run 5 nights, measure:
- Fix rate before skills vs after
- Lessons accumulating correctly
- No skill bloat (under 2K words)

---

## Sprint 4: Remote Access (Telegram Bot)

**Goal:** Control farm from phone
**Duration:** 3-5 days
**Prerequisite:** Sprint 2 complete

### 4.1 Create Telegram Bot

```
1. Open Telegram, search @BotFather
2. Send /newbot
3. Name: Ralph Loops
4. Username: ralph_loops_bot (or similar)
5. Save the API token
```

### 4.2 Bot Implementation

**File:** `.ralph/bot/package.json`
```json
{
  "name": "ralph-bot",
  "version": "1.0.0",
  "main": "bot.js",
  "dependencies": {
    "node-telegram-bot-api": "^0.64.0"
  }
}
```

**Key commands:**
- `/status` — Check all agents
- `/start` — Start night run
- `/stop` — Stop all agents
- `/morning` — Get morning report
- `/tasks` — Show task summary
- `/logs [agent]` — View recent logs

### 4.3 Proactive Alerts

Bot monitors and alerts on:
- Agent crashed
- Rate limit hit
- Task needs human review
- Night run complete
- No activity for 1 hour

---

### Sprint 4 Deliverables

| Item | Deliverable |
|------|-------------|
| .ralph/bot/ | Complete bot implementation |
| /status, /start, /stop | Control commands |
| /morning | Report delivery |
| Alerts | Proactive notifications |

**Test:** Manage one full night entirely from phone.

---

## Implementation Timeline

```
Week 1:  Sprint 1 (Foundation Fixes)
         - Days 1-2: Gemini auth + rate limiting
         - Days 3-4: Validation + pre-flight
         - Day 5: Test overnight run

Week 2:  Sprint 2 (Smart Manager)
         - Days 1-3: Evidence-based review + fix tasks
         - Days 4-5: Follow-ups + context
         - Days 6-7: Packup mode + morning review v2

Week 3:  Sprint 2 Validation + Sprint 3 Start
         - Days 1-3: Run 3 stable nights
         - Days 4-7: Skill files + worker.sh update

Week 4:  Sprint 3 Completion + Sprint 4
         - Days 1-3: Lesson extraction + metrics
         - Days 4-7: Telegram bot
```

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Overnight success rate | ~60% | >85% |
| Fix rate (needs retry) | ~40% | <20% |
| Human intervention needed | Daily | 1-2x/week |
| Rate limit failures | Common | Zero |
| Duplicate manager issues | Occurred | Zero |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Skills bloat prompts | 2K word cap, monitoring |
| Bad lessons learned | Human review, max 20 cap |
| Packup too aggressive | Configurable threshold |
| Bot exposes access | Chat ID auth, command whitelist |
| Fix loop burns credits | Max 3 retries per task |

---

## Files to Create/Modify

### New Files
- `.ralph/skills/common/*.md` (3 files)
- `.ralph/skills/backend/*.md` (2 files)
- `.ralph/skills/frontend/*.md` (2 files)
- `.ralph/skills/tests/*.md` (1 file)
- `.ralph/skills/learned/*.md` (3 files)
- `.ralph/skills/metrics.json`
- `.ralph/bot/*` (bot implementation)
- `scripts/ralph-agent-setup.sh`

### Modified Files
- `scripts/worker.sh` → v8 (retry + validation + skills)
- `scripts/manager-loop.sh` → v2 (full features)
- `scripts/analyze-result.sh` (evidence-based + lessons)
- `scripts/start-night.sh` (pre-flight)
- `scripts/morning-review.sh` → v2
- `.ralph/config.json` (new settings)

---

## Checklist Summary

### Sprint 1
- [ ] 1.1 Gemini Auth Upgrade (all 3 agents)
- [ ] 1.2 Rate Limit Handling (worker.sh)
- [ ] 1.3 Task Validation Section (template)
- [ ] 1.4 worker.sh validate_task()
- [ ] 1.5 Pre-Flight Checks (start-night.sh)
- [ ] 1.6 PID Lock (manager-loop.sh)
- [ ] Sprint 1 Test: 1 overnight run

### Sprint 2
- [ ] 2.1 Evidence-Based Review
- [ ] 2.2 Auto-Generate Fix Tasks
- [ ] 2.3 Auto-Generate Follow-Up Tasks
- [ ] 2.4 Context Preservation
- [ ] 2.5 Packup Mode
- [ ] 2.6 morning-review.sh v2
- [ ] Sprint 2 Test: 3 stable nights

### Sprint 3
- [ ] 3.1 Skill Directory Structure
- [ ] 3.2 Common Skills (3 files)
- [ ] 3.3 Backend Skills (2 files)
- [ ] 3.4 Frontend Skills (2 files)
- [ ] 3.5 Tests Skills (1 file)
- [ ] 3.6 worker.sh build_prompt()
- [ ] 3.7 Lesson Extraction
- [ ] 3.8 Skills Metrics
- [ ] Sprint 3 Test: 5 nights, measure fix rate

### Sprint 4
- [ ] 4.1 Create Telegram Bot
- [ ] 4.2 Bot Commands
- [ ] 4.3 Proactive Alerts
- [ ] Sprint 4 Test: Full night from phone

---

*This plan addresses all 34 open issues in a logical sequence with clear deliverables and success criteria.*
