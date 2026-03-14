# Ralph Loops - Implementation Plan v2

**Created:** 2026-02-08
**Status:** Active
**Last Updated:** 2026-02-10 (Phase 3 skills system complete)

---

## 1. Project Overview

### What is Ralph Loops?

Ralph Loops is an autonomous AI coding farm. The user provides a project idea, and AI agents build working code overnight with minimal human intervention.

**Core concept:** Break a project into tasks, distribute to specialized agents, let them work autonomously, review results in the morning.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MANAGER (Windows 11)                        │
│                     100.x.x.0                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ start-night │  │manager-loop │  │morning-review│             │
│  │    v3.0     │  │    v5.0     │  │    v3.0     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │              │                  │                     │
│         │         Anthropic API           │                     │
│         │         (review results)        │                     │
└─────────┼──────────────┼──────────────────┼─────────────────────┘
          │              │                  │
          └──────────────┼──────────────────┘
                         │
              ┌──────────┴──────────┐
              │   GitHub (main)     │
              │   Git Coordination  │
              └──────────┬──────────┘
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
┌────┴────┐        ┌─────┴────┐        ┌─────┴────┐
│   PC1   │        │   PC2    │        │   PC3    │
│ backend │        │ frontend │        │  tests   │
│ Ubuntu  │        │ Ubuntu   │        │ Ubuntu   │
│100.x.  │        │100.x.  │        │100.x.  │
│160.36   │        │219.106   │        │196.59    │
└─────────┘        └──────────┘        └──────────┘
     │                   │                   │
  worker.sh v9        worker.sh v9       worker.sh v9
  Claude/Gemini       Claude/Gemini      Claude/Gemini
```

**Network:** Tailscale mesh VPN (100.x.x.x addresses)

### Current AI Strategy

| Priority | AI | Usage |
|----------|-----|-------|
| Primary | **Claude CLI** | Can write files, reliable for coding tasks |
| Fallback | Gemini CLI | Used when Claude exhausted (rate limits) |

**Reason for Claude primary:** Gemini CLI in prompt mode (`gemini -p`) cannot create or modify files - it outputs code but says "I cannot directly create or modify files." Claude CLI with `--dangerously-skip-permissions` can write files.

---

## 2. Current State - What's Actually Working

### Script Versions (as of 2026-02-08)

| Script | Version | Location | Status |
|--------|---------|----------|--------|
| worker.sh | v9 | templates/scripts/ | Production |
| manager-loop.sh | v5.0 | scripts/ | Production |
| start-night.sh | v3.0 | scripts/ | Production |
| morning-review.sh | v3.0 | scripts/ | Production |
| status.sh | v2 | scripts/ | Production |
| analyze-result.sh | v2.0 | scripts/ | Production |
| init-project.sh | - | scripts/ | Production |
| generate-tasks.sh | - | scripts/ | Production |
| generate-context.sh | - | templates/scripts/ | Production |
| safe-push.sh | - | scripts/ + templates/ | Production |

### Phase 1: Foundation - COMPLETE (8/8)

| Feature | Status | Implementation |
|---------|--------|----------------|
| Dual AI execution | ✅ | Claude primary, Gemini fallback with exhaustion tracking |
| Rate limit detection | ✅ | Regex match for 429, quota, rate.limit patterns |
| Exponential backoff | ✅ | base_delay * attempt + random jitter |
| Task validation | ✅ | Extracts `## Validation` block, runs with timeout |
| Partial success detection | ✅ | Checks file creation + git status for src/ changes |
| Pre-flight checks | ✅ | 5 checks: git, SSH, AI, tasks, scripts |
| PID lock (manager) | ✅ | /tmp/ralph-manager.pid with stale detection |
| Safe git push | ✅ | Atomic push, rebase, exponential backoff |

### Phase 2: Smart Manager - NEARLY COMPLETE (10/11)

| Feature | Status | Notes |
|---------|--------|-------|
| Fix chain naming | ✅ | Strips all `-fix-N` suffixes, creates `original-fix-N` |
| Enhanced fix tasks | ✅ | Includes previous result, git diff, validation block |
| Escalation files | ✅ | Created when max attempts reached |
| Circuit breaker | ✅ | Stops after N consecutive API failures |
| Daily review limits | ✅ | Configurable max_daily_reviews |
| Context injection | ✅ | generate-context.sh provides project structure |
| Role-specific fix instructions | ✅ | Backend/frontend/tests get different guidance |
| Validation block propagation | ✅ | Original task's validation copied to fix tasks |
| Evidence-based auto-approve | ✅ | Skips API when Execution=SUCCESS + Validation=PASSED (v5.1) |
| Follow-up task generation | ✅ | Context-preserving follow-ups with chain depth tracking (v5.2) |
| Packup mode (quota threshold) | ❌ | Not implemented |

### Phase 3: Smart Skills - COMPLETE (7/8)

| Feature | Status | Notes |
|---------|--------|-------|
| Skill directory structure | ✅ | templates/skills/ + init-project copies |
| Common skills | ✅ | 3 skills: error-handling, validation, file-structure |
| Role-specific skills | ✅ | backend (3), frontend (3), tests (2) |
| build_prompt() with context | ✅ | Done via generate-context.sh (different approach) |
| Project structure injection | ✅ | Tree/find output included in prompts |
| Lesson extraction | ✅ | extract_lesson() in manager-loop.sh |
| Skills metrics | ❌ | Not implemented |
| Learning from failures | ✅ | Lessons auto-saved to .ralph/skills/lessons/ |

### Phase 4: Remote Access - NOT STARTED (0/4)

| Feature | Status |
|---------|--------|
| Telegram bot | ❌ |
| Mobile notifications | ❌ |
| Remote start/stop | ❌ |
| Status queries | ❌ |

### Test Runs Completed

| Run | Date | Tasks | Success Rate | Notes |
|-----|------|-------|--------------|-------|
| Night Run 1 | 2026-02-05 | 10 | ~70% | Claude rate limit hit, 4 approved |
| Night Run 2 | 2026-02-08 | 12 | ~95% exec | Albums API failed (Gemini file-write) |

**Current metrics (ralph-test-app):**
- Total results: 32
- Execution SUCCESS: 21/22 (95%)
- Reviews completed: 10
- Approved: 3
- Validation coverage: Low (most tasks have NO_VALIDATION)

---

## 3. Lessons Learned

### AI & Rate Limits

| Lesson | Detail |
|--------|--------|
| Gemini CLI can't write files | In `-p` prompt mode, Gemini generates code but cannot create/modify files. Switch to Claude as primary. |
| Google quota reduced | Dec 2025: 250 RPD → 20 RPD for free tier. Gemini exhausts quickly. |
| Claude more reliable for coding | Claude CLI with `--dangerously-skip-permissions` actually writes files. |
| Rate limit detection works | Regex catches 429, quota, resource.exhausted patterns. |
| Dual AI fallback essential | When primary exhausts, seamless fallback prevents total failure. |

### Git Coordination

| Lesson | Detail |
|--------|--------|
| safe-push prevents races | Exponential backoff + atomic push handles 3 agents pushing simultaneously. |
| Separate folders per role | `tasks/pending/{backend,frontend,tests}/` prevents merge conflicts. |
| Rebase before push | `git pull --rebase` keeps history clean, avoids merge commits. |
| Lock rollback on push fail | If push fails after commit, reset HEAD~1 and restore task file. |
| Redirect git output | Capture to log file, don't let it pollute variables. |

### Validation

| Lesson | Detail |
|--------|--------|
| File creation ≠ working code | Just because files exist doesn't mean they work. Need actual validation. |
| 3-phase validation needed | 1) Execution status, 2) Validation command, 3) Result parsing |
| Timeout validation scripts | Use `timeout 120s` to prevent hung validations. |
| Validation in task markdown | `## Validation` section with bash code block works well. |
| Most tasks lack validation | Task generator should create better validation scripts. |

### Task Design

| Lesson | Detail |
|--------|--------|
| Bind to 0.0.0.0 | Servers must not bind to localhost - other machines can't reach them. |
| Enable CORS | All APIs need CORS for cross-origin requests from frontend. |
| Specify exact file paths | `## Files to Create` section helps verify completion. |
| Role instructions need ports | Template had wrong ports; each project needs correct IPs/ports. |
| Self-contained tasks | Each task should be completable without other tasks being done first. |

### Architecture

| Lesson | Detail |
|--------|--------|
| Manager doesn't need Claude Code | Direct Anthropic API calls via curl work fine, no CLI dependency. |
| PID lock prevents duplicates | Critical - running two managers causes chaos. |
| STOP_HOUR for overnight | Workers stop at 6 AM, manager stops at 6 AM. Designed for overnight runs. |
| nohup + background | Required for processes to survive SSH disconnection. |
| Tailscale IPs stable | Use 100.x.x.x addresses, not hostnames. |

### Scripting

| Lesson | Detail |
|--------|--------|
| No exclamation marks in echo | Bash history expansion interprets `!` in double quotes. |
| CRLF causes issues | Windows creates CRLF, Linux agents need LF. Use .gitattributes. |
| tr -d '\r' for safety | Strip carriage returns when reading files created on Windows. |
| jq for JSON | Manager uses jq extensively for API responses. Reliable. |

---

## 4. What Needs to Be Done

### Critical (Blocks Reliable Overnight Runs)

| Item | Current State | What's Left |
|------|---------------|-------------|
| ~~Rate limit handling~~ | ✅ Done | 429 detection + backoff implemented in worker.sh |
| ~~Task validation~~ | ✅ Done | Validation extraction + execution implemented |
| ~~PID lock~~ | ✅ Done | manager-loop.sh has acquire_lock() |
| Better validation scripts | 🔄 Partial | generate-tasks.sh creates basic validations, need improvement |
| Claude primary everywhere | ✅ Done | worker.sh template + ralph-test-app updated |

### Important (Completes Phase 2)

| Item | Description | Status |
|------|-------------|--------|
| Evidence-based auto-approve | If validation PASSED, manager auto-approves (skips Claude API) | ✅ Done |
| Follow-up task generation | After approved task, auto-create dependent tasks with context | ✅ Done |
| Context preservation | Pass relevant context between dependent tasks | ✅ Done (context_from_parent in follow-ups) |
| Packup mode | Detect low quota/credits, gracefully stop and summarize | ❌ Not implemented |
| Retry cap per original task | Track fix attempts across all variants, stop at max | ✅ Done |

### Nice to Have (Quality of Life)

| Item | Description | Status |
|------|-------------|--------|
| Skills system | Static knowledge files that teach agents patterns | ✅ Done |
| Lesson extraction | Manager learns from failures, appends to skills | ❌ Not started |
| Telegram bot | Remote notifications and control | ❌ Not started |
| Better task generator | Smarter validation scripts, dependency awareness | 🔄 Basic version exists |
| Metrics dashboard | Track success rates over time | ❌ Not started |

---

## 5. Future Options (Documented, Not Scheduled)

### F1: Matrix Model
Dynamic skill packs per agent. Backend gets Express patterns, frontend gets DOM patterns. Skills loaded based on role + task type.

### F2: Local Caching & Persistence
Agents cache npm packages, frequently-used code patterns. Reduces network and speeds up tasks.

### F3: Local AI Fallback
Small local LLM (Ollama, llama.cpp) as last resort when both Claude and Gemini exhausted. Lower quality but non-zero progress.

### F4: Agent-Local Dev Servers
Each agent runs its own dev server. Backend agent has Node running, can test its own code before committing.

### F5: 6-Agent Expansion
Add specialized agents: design (UI/UX), docs (README, API docs), security (vulnerability scanning). Requires more hardware.

### F6: Wave-Based Orchestration
Instead of all agents working in parallel, run in waves:
1. Wave 1: Backend APIs
2. Wave 2: Frontend UIs (after APIs exist)
3. Wave 3: Tests (after code exists)
4. Wave 4: Fixes

### F7: Publication as Open-Source Template
Clean up, document, create example projects. Publish to GitHub as reusable framework.

---

## 6. Target Metrics

| Metric | Current | Phase 2 Target | Final Target |
|--------|---------|----------------|--------------|
| Overnight execution success | 95% | >95% | >98% |
| Validation coverage | ~30% | >80% | >95% |
| Auto-fix success rate | N/A | >50% | >70% |
| Human intervention | Daily | 2-3x/week | Weekly |
| Rate limit failures | Occasional | Rare | Zero |
| Tasks per night | 10-12 | 15-20 | 30+ |

---

## 7. Infrastructure Reference

### Manager (Windows 11)
- **IP:** 100.x.x.0
- **Role:** Orchestration, review, task generation
- **Scripts:** start-night.sh, manager-loop.sh, morning-review.sh, status.sh
- **Requires:** Git Bash, jq, curl, ANTHROPIC_API_KEY

### PC1 - Backend Agent (Ubuntu)
- **IP:** 100.x.160.36
- **Role:** Express.js microservices
- **Ports:** 3001 (general), 3002 (auth), 3003 (drive), 3004 (albums)
- **Scripts:** worker.sh backend

### PC2 - Frontend Agent (Ubuntu)
- **IP:** 100.x.219.106
- **Role:** Vanilla HTML/CSS/JS pages
- **Port:** 3000 (dev server)
- **Scripts:** worker.sh frontend

### PC3 - Tests Agent (Ubuntu)
- **IP:** 100.x.196.59
- **Role:** Bash test scripts with curl
- **Scripts:** worker.sh tests

### Repositories
- **Ralph Loops (orchestration):** D:\projects\ralph-loops (local, no remote)
- **Test Project:** git@github.com:YOUR_USERNAME/YOUR_PROJECT.git

---

## 8. Definition of Done

### When is Ralph Loops "Finished"?

**Minimum Viable Product (Phase 2 Complete):**
- [ ] 3 consecutive overnight runs with >90% success rate
- [ ] Auto-fix working (at least 50% of NEEDS_FIX resolved automatically)
- [x] Evidence-based auto-approve implemented
- [ ] All critical items resolved
- [ ] Documentation updated (this plan + user manual)
- [ ] Test project (Media Organizer) is actually usable

**Full Product (Phase 3-4 Complete):**
- [x] Skills system implemented and learning from failures
- [ ] Telegram bot for remote control
- [ ] Metrics dashboard
- [ ] Published as open-source template with examples
- [ ] 5+ overnight runs with minimal human intervention

### Success Criteria for a Single Night Run

1. All pending tasks processed (moved to done/)
2. Manager reviewed all results
3. Fix tasks auto-generated for failures
4. No stuck tasks in in-progress/
5. Clean git history (no conflicts, no duplicate commits)
6. Logs capture full execution trace

---

## Appendix: File Reference

### Manager Scripts (ralph-loops/scripts/)
| File | Purpose |
|------|---------|
| start-night.sh | Pre-flight checks, start workers + manager |
| manager-loop.sh | Poll for results, review with Claude API, create fix tasks |
| morning-review.sh | Summary of overnight run, stop processes |
| status.sh | Real-time status dashboard |
| analyze-result.sh | Standalone result analysis (used by manager) |
| init-project.sh | Create new project from templates |
| generate-tasks.sh | AI-powered idea → task files |
| safe-push.sh | Git push with retry + backoff |

### Agent Templates (ralph-loops/templates/)
| File | Purpose |
|------|---------|
| scripts/worker.sh | Main agent loop - pick task, execute, validate, commit |
| scripts/generate-context.sh | Build prompt context from project state |
| scripts/safe-push.sh | Git push with retry (copied to projects) |
| ralph/config.json | Project configuration template |
| ralph/project-context.md | Project description template |
| CLAUDE.md | Coding rules template |
| gitignore | Standard ignores |
| gitattributes | Force LF line endings |

---

*Plan v2 created 2026-02-08. Previous version archived as implementation-plan-v1-archived.md*
