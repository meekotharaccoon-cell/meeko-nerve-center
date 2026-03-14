# Lessons Learned: Night Run Issues (2026-02-12)

## Issue 1: Git Sync Failures (28 occurrences)

**Symptom:**
```
error: cannot pull with rebase: You have unstaged changes.
```

**Root Cause:**
Manager machine (pc5) accumulated unstaged changes from various operations. `git pull --rebase` fails when working directory is dirty.

**Fix Applied (v3.2):**
```bash
# In git_sync(), added auto-cleanup before pull:
git checkout -- . 2>> "$LOG_FILE" || true
git clean -fd 2>> "$LOG_FILE" || true
```

**Prevention:**
- Manager now auto-cleans before every sync
- More aggressive cleanup on retry attempts

---

## Issue 2: Claude API Empty Responses (12 occurrences)

**Symptom:**
```
ERROR: Empty response from Claude API
API failure count: 1 / 3
Verdict: NEEDS_HUMAN | Summary: API error
```

**Root Cause:**
Single API call with no retry. Rate limits or temporary failures immediately marked tasks for human review.

**Fix Applied (v6.4):**
```bash
# Retry loop with exponential backoff:
for attempt in $(seq 1 3); do
    # ... API call ...
    if [ -n "$text" ]; then break; fi
    sleep $retry_delay
    retry_delay=$((retry_delay * 2))  # 5s, 10s, 20s
done
```

**Prevention:**
- 3 retries with exponential backoff (5s, 10s, 20s)
- Rate limit errors detected and logged
- Only marks NEEDS_HUMAN after all retries exhausted

---

## Issue 3: Task Execution Failures (4 occurrences)

**Symptom:**
```
Result status: Execution=FAILED, Validation=SKIPPED
```

**Root Cause:**
Worker timeouts or AI execution issues. Tasks without validation blocks couldn't verify partial success.

**Fix Applied (Worker v11):**
- Auto-validation added before task execution
- Workers now generate role-appropriate validation if missing

**Prevention:**
- All tasks guaranteed to have validation
- generate-tasks.sh includes validation in prompt

---

## Summary of Fixes

| Script | Version | Fix |
|--------|---------|-----|
| manager-utils.sh | v3.2 | Git auto-cleanup before sync |
| manager-loop.sh | v6.4 | API retry with exponential backoff |
| worker.sh | v11 | Auto-validation for all tasks |

## Metrics Impact (Expected)

- Git sync failures: 28 → 0
- API failures causing NEEDS_HUMAN: 12 → ~2-3 (only true failures)
- Tasks without validation: 67 → 0
