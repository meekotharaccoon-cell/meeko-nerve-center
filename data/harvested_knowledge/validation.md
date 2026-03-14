# Validation Patterns

## When to Use
- Verifying your code works before finishing a task
- Writing task validation scripts
- Testing API endpoints

## Backend Validation Pattern
```bash
# Start server, test endpoint, stop server
cd src/backend/{service} && npm install --silent 2>/dev/null

# Start server in background
timeout 30s node server.js &
SERVER_PID=$!
sleep 2  # Wait for server to start

# Test endpoint
RESPONSE=$(curl -sf http://localhost:{PORT}/api/endpoint 2>/dev/null)
RESULT=$?

# Cleanup
kill $SERVER_PID 2>/dev/null || true

# Check result
if [ $RESULT -eq 0 ] && echo "$RESPONSE" | grep -q "expected"; then
  echo "PASS"
  exit 0
else
  echo "FAIL"
  exit 1
fi
```

## Frontend Validation Pattern
```bash
# Check required files exist
if [ -f "src/frontend/{feature}/index.html" ]; then
  # Check for expected content
  if grep -q "expected-element" src/frontend/{feature}/index.html; then
    echo "PASS"
    exit 0
  fi
fi
echo "FAIL"
exit 1
```

## Test Script Validation Pattern
```bash
# Check test script exists and is executable
if [ -f "src/tests/{area}/test-{name}.sh" ]; then
  # Check it has proper shebang
  if head -1 src/tests/{area}/test-{name}.sh | grep -q "#!/bin/bash"; then
    echo "PASS"
    exit 0
  fi
fi
echo "FAIL"
exit 1
```

## Exit Code Convention
- `exit 0` = PASS / SUCCESS
- `exit 1` = FAIL / ERROR
- Non-zero = Something went wrong

## Common Mistakes
- Forgetting to kill background server process
- Not waiting for server to start (missing sleep)
- Using localhost instead of 0.0.0.0 for testing
- Not handling curl failures gracefully
