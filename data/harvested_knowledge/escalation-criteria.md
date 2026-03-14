# Escalation Criteria

## When to Mark NEEDS_HUMAN

### Ambiguous Requirements
- Task description is unclear or contradictory
- Multiple valid interpretations possible
- Cannot determine what "success" looks like

### Architectural Decisions
- Task requires choosing between fundamentally different approaches
- Changes would affect multiple roles/components
- No clear pattern in project-context.md

### Security Concerns
- Code handles authentication/authorization
- Involves secrets, API keys, or credentials
- Potential for injection vulnerabilities

### External Dependencies
- Task requires access to external services
- API rate limits or quotas involved
- Network configuration issues

### Repeated Failures
- Fix attempt #3 still failing
- Same error recurring despite fixes
- Agent appears stuck in a loop

### Out of Scope
- Task requires skills not in the agent's role
- Would need to modify files in other role directories
- Requires human judgment (design decisions, UX choices)

## When NOT to Escalate

### Solvable Issues
- Clear syntax errors - create fix task
- Missing imports - create fix task
- Wrong variable names - create fix task
- Validation failures with clear cause - create fix task

### Common Patterns
- If you've seen this issue before and know the fix - don't escalate
- If the error message clearly indicates the problem - don't escalate
- If project-context.md has guidance - don't escalate

## Escalation Message Format

When marking NEEDS_HUMAN, include:
1. What you tried to assess
2. Why you couldn't make a decision
3. What information would help
4. Suggested next steps for human

Example:
```
NEEDS_HUMAN

Unable to assess: Task requires choosing database schema design.

Why: Multiple valid approaches (normalized vs denormalized), depends on
future query patterns not specified in requirements.

Need: Human decision on data modeling approach.

Suggested: Review task with product owner to clarify access patterns.
```
