# Review Patterns

## Evaluation Criteria

### 1. Task Fulfillment
- Does the output match what was requested?
- Are all requirements addressed?
- Is the scope appropriate (not under or over-engineered)?

### 2. Code Quality
- No syntax errors
- No obvious bugs or logic errors
- Follows project patterns (check project-context.md)
- Clean, readable code

### 3. Validation Results
- If validation PASSED: Strong signal for approval
- If validation FAILED: Examine why - is it a real failure or a validation bug?
- If NO_VALIDATION: Be more cautious, check code manually

### 4. Scope Discipline
- Agent stayed within their role directory
- No modifications to unrelated files
- No unnecessary refactoring

## Verdict Guidelines

### APPROVED
- Task requirements met
- Validation passed (or code looks correct if no validation)
- No obvious issues

### NEEDS_FIX
- Clear, specific issues that can be fixed
- Provide actionable feedback
- Examples:
  - "Missing error handling for null case"
  - "Function returns wrong type"
  - "CSS selector doesn't match HTML structure"

### NEEDS_HUMAN
Use sparingly. Only when:
- Cannot understand what the code is supposed to do
- Task requirements are ambiguous
- Multiple conflicting approaches possible
- Security concerns
- API response indicates rate limiting or error

## Anti-Patterns

- Don't approve just because validation passed - read the code
- Don't NEEDS_FIX for style preferences - only real issues
- Don't NEEDS_HUMAN to avoid making a decision
- Don't request fixes for things outside the task scope
