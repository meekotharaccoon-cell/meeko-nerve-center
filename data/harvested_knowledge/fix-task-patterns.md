# Fix Task Patterns

## Writing Effective Fix Tasks

### Be Specific
Bad: "Fix the bug"
Good: "Fix the null pointer error in getUserById() when user doesn't exist"

### Include Context
- What the original task was trying to achieve
- What went wrong (error messages, validation output)
- What files are involved

### One Problem at a Time
- If multiple issues, prioritize the blocking one
- Don't overwhelm with too many fixes at once
- Sequential fixes are easier to verify

### Preserve Validation
- Always include the original validation block
- Validation is how we know if the fix worked

## Fix Task Structure

```
1. Context: What attempt number, what was the goal
2. Previous Result: What happened last time
3. Issues: Specific problems to fix
4. Instructions: Clear steps
5. Validation: How to verify success
```

## Common Fix Scenarios

### Syntax Error
- Quote the exact error message
- Point to the file and line if known
- Suggest what might be wrong

### Logic Error
- Describe expected vs actual behavior
- Include test case that fails
- Point to the function/section

### Missing Functionality
- Describe what's missing
- Reference original requirements
- Don't expand scope beyond original task

### Integration Issue
- Describe how components should connect
- Include relevant file paths
- Note any dependencies

## Anti-Patterns

- Don't rewrite the entire task - just fix what's broken
- Don't add new requirements in fix tasks
- Don't be vague - specificity helps the agent succeed
- Don't create fix chains longer than 3 attempts - escalate to human
