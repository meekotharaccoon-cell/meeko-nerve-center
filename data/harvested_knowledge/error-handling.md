# Error Handling Patterns

## When to Use
- Any code that calls external services, APIs, or reads files
- Database operations
- Network requests
- User input processing

## JavaScript/Node.js Pattern
```javascript
// Async/await with try-catch
async function fetchData() {
  try {
    const result = await someAsyncOperation();
    return result;
  } catch (error) {
    console.error('Operation failed:', error.message);
    throw error; // Re-throw if caller should handle
  }
}

// Express route handler
app.get('/api/resource', async (req, res) => {
  try {
    const data = await getData();
    res.json(data);
  } catch (error) {
    console.error('Error:', error.message);
    res.status(500).json({ error: error.message });
  }
});
```

## Bash Pattern
```bash
# Check command success
if ! command_that_might_fail; then
  echo "ERROR: Command failed" >&2
  exit 1
fi

# Or with set -e at script start
set -euo pipefail  # Exit on error, undefined vars, pipe failures
```

## Common Mistakes
- Catching errors but not logging them
- Swallowing errors silently (empty catch blocks)
- Not returning proper HTTP status codes
- Forgetting to handle promise rejections

## Error Response Format
Always use consistent JSON error format:
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE_IF_APPLICABLE"
}
```
