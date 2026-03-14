# Instructions for Using Claude to Create Tasks

You can use Claude (or any AI assistant) to help you write well-structured task files. Here's how:

## Prompt Template

```
I need you to create a task file for my Ralph Loops system.

The task should:
- [Describe what you want built]
- [Any specific requirements]

The backend server runs at http://100.x.x.1:3001

Please create a markdown task file with:
1. Clear description
2. Specific requirements (including 0.0.0.0 binding, CORS if needed)
3. Exact file paths in src/ROLE/
4. Success criteria as a checklist

Format it like this:
# Task: [Title]
## Description
## Requirements
## Files to Create
## Success Criteria
```

## Example Conversation

**You:** Create a task for an API endpoint that returns user statistics.

**Claude:** Here's a task file for your Ralph Loops system:

```markdown
# Task: Create User Statistics API

## Description
Create an Express endpoint that returns aggregated user statistics including total users, active users, and new signups.

## Requirements
- GET /api/stats returns JSON with user statistics
- Server runs on port 3001
- Bind to 0.0.0.0 (not localhost)
- Enable CORS for frontend access
- Include counts for: totalUsers, activeUsers, newSignupsToday

## Files to Create
- src/backend/stats/server.js
- src/backend/stats/package.json

## Success Criteria
- [ ] Server starts without errors
- [ ] Endpoint returns valid JSON
- [ ] All required fields present in response
- [ ] Accessible from other machines on the network
```

## Tips for Better Tasks

1. **Be specific** - Vague requirements get vague results
2. **Specify ports and binding** - Always mention 0.0.0.0 for servers
3. **Include file paths** - Tell the AI exactly where to put files
4. **Define the API contract** - For frontend/backend coordination, define the exact JSON structure
5. **Add success criteria** - Helps the AI verify its own work

## Coordinating Frontend and Backend

When you need frontend and backend to work together:

1. **Create an API contract first** (in `specs/`)
2. **Reference the contract** in both task files
3. **Use placeholder IPs** - Replace with your actual Tailscale IPs

Example API contract reference in a task:

```markdown
## Requirements
- Follow the API contract in specs/user-api.md
- Backend endpoint: http://100.x.x.1:3001/api/users
```
