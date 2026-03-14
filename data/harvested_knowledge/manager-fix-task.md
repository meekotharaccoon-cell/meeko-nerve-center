# Fix Task: {ORIGINAL_TASK_NAME}

## Before You Begin

Read and internalize these files:
1. `.ralph/project-context.md` - Project overview and architecture
2. `.ralph/skills/common/` - Patterns all agents must follow
3. `.ralph/skills/{ROLE}/` - Your role-specific expertise
4. `.ralph/skills/lessons/` - Learnings from past runs

## Context Verification

After reading the files above, output this confirmation:
```
## Context Loaded
- Project: {name from project-context.md}
- My Role: {ROLE}
- Fix Attempt: #{FIX_NUMBER}
- Skills Read: common (N files), {ROLE} (N files), lessons (N files)
```

## Context

This is attempt #{FIX_NUMBER} to complete the original task.

## Original Task

{ORIGINAL_TASK_CONTENT}

## Previous Attempt Result

{PREVIOUS_RESULT}

## What Went Wrong

{ISSUES_IDENTIFIED}

## Your Instructions

1. Review the previous attempt's output above
2. Fix the specific issues identified
3. Stay within scope - only fix what's broken
4. Validate your work before finishing

## Validation

{VALIDATION_BLOCK}
