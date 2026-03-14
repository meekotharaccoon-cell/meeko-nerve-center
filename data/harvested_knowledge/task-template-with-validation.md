# Task Template with Validation

This template shows the new task format with automatic validation support (worker.sh v8+).

---

## Template

```markdown
# Task: [Short descriptive title]

## Description
[1-3 sentences explaining what needs to be built]

## Requirements
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

## Files to Create
- `src/path/to/file1.js`
- `src/path/to/file2.js`

## Validation
```bash
# Commands to verify the code works
# Exit 0 = PASSED, non-zero = FAILED
cd src/path/to
npm install 2>/dev/null || true
node server.js &
SERVER_PID=$!
sleep 3
curl -sf http://localhost:3001/api/health | grep -q "ok"
RESULT=$?
kill $SERVER_PID 2>/dev/null
exit $RESULT
```

## Success Criteria
- [Human-readable criterion 1]
- [Human-readable criterion 2]
```

---

## Example: Backend API Task

```markdown
# Task: Create Orders API

## Description
Build a REST API for order management with CRUD operations and health check endpoint.

## Requirements
- POST /api/orders - Create new order (accepts JSON body)
- GET /api/orders/:id - Get order by ID
- GET /api/health - Return {"status": "ok"}
- Server binds to 0.0.0.0:3001
- Enable CORS for all origins

## Files to Create
- `src/backend/orders/server.js`
- `src/backend/orders/routes.js`
- `src/backend/orders/package.json`

## Validation
```bash
cd src/backend/orders
npm install
node server.js &
SERVER_PID=$!
sleep 3
# Test health endpoint
curl -sf http://localhost:3001/api/health | grep -q "ok"
RESULT=$?
kill $SERVER_PID 2>/dev/null
exit $RESULT
```

## Success Criteria
- Server starts without errors
- Health endpoint returns {"status": "ok"}
- CORS headers present in responses
```

---

## Example: Frontend Component Task

```markdown
# Task: Create Login Form Component

## Description
Build a React login form with email/password fields and form validation.

## Requirements
- Email field with validation (must contain @)
- Password field (minimum 8 characters)
- Submit button disabled until valid
- Show error messages for invalid input
- Call onSubmit prop with {email, password} on valid submission

## Files to Create
- `src/frontend/components/LoginForm.jsx`
- `src/frontend/components/LoginForm.css`

## Validation
```bash
cd src/frontend
npm install 2>/dev/null || true
# Check component file exists and has required elements
grep -q "email" components/LoginForm.jsx && \
grep -q "password" components/LoginForm.jsx && \
grep -q "onSubmit" components/LoginForm.jsx
```

## Success Criteria
- Component renders without errors
- Form validation works as specified
- Accessible (labels, aria attributes)
```

---

## Example: Test Task

```markdown
# Task: Add Unit Tests for UserService

## Description
Write Jest unit tests for the UserService class covering all public methods.

## Requirements
- Test createUser() with valid and invalid input
- Test getUserById() with existing and non-existing IDs
- Test updateUser() with partial updates
- Achieve >80% code coverage

## Files to Create
- `src/tests/UserService.test.js`

## Validation
```bash
cd src
npm test -- --coverage --testPathPattern=UserService.test.js 2>&1 | grep -E "Statements|passed"
# Check tests pass
npm test -- --testPathPattern=UserService.test.js --passWithNoTests
```

## Success Criteria
- All tests pass
- Coverage > 80%
- Tests are readable and well-organized
```

---

## Validation Section Guidelines

### Do:
- Keep validation simple (< 10 lines)
- Use `set -e` implicitly (script stops on first error)
- Clean up background processes (kill $PID)
- Use timeouts for network calls
- Test the minimum viable success criteria

### Don't:
- Run full test suites (too slow)
- Depend on external services
- Leave processes running
- Use interactive commands

### Common Patterns:

**Start server and test endpoint:**
```bash
node server.js &
PID=$!
sleep 3
curl -sf http://localhost:PORT/endpoint
kill $PID 2>/dev/null
```

**Check file contains expected content:**
```bash
grep -q "expected_string" path/to/file.js
```

**Run specific test file:**
```bash
npm test -- --testPathPattern=specific.test.js
```

**Check syntax validity:**
```bash
node --check path/to/file.js
```

---

## Result File Output

With validation, result files now show:

```
# Result: create-orders-api.md
Agent: backend
AI Used: gemini
Execution: SUCCESS
Validation: PASSED
Started: Tue Feb 4 22:30:00 2026
Finished: Tue Feb 4 22:35:00 2026

## Validation Output
```
Server listening on port 3001
{"status":"ok"}
```

## Log (last 50 lines)
...
```

---

**Created:** Sprint 1, February 2026
**Requires:** worker.sh v8+
