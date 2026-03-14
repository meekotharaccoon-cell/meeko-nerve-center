# curl Testing Patterns

## When to Use
- Testing backend API endpoints
- Verifying API responses
- Integration testing

## Basic GET Request
```bash
# Simple GET
curl -sf http://{BACKEND_HOST}:3001/api/items

# With headers shown
curl -i http://{BACKEND_HOST}:3001/api/items

# Silent with fail on error
curl -sf http://{BACKEND_HOST}:3001/api/items || echo "FAILED"
```

## POST with JSON Body
```bash
curl -sf -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "value": 123}' \
  http://{BACKEND_HOST}:3001/api/items
```

## PUT (Update)
```bash
curl -sf -X PUT \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item"}' \
  http://{BACKEND_HOST}:3001/api/items/123
```

## DELETE
```bash
curl -sf -X DELETE http://{BACKEND_HOST}:3001/api/items/123
```

## Common curl Flags
| Flag | Meaning |
|------|---------|
| `-s` | Silent (no progress) |
| `-f` | Fail silently on HTTP errors |
| `-i` | Include response headers |
| `-X` | HTTP method (GET, POST, etc.) |
| `-H` | Add header |
| `-d` | Request body data |
| `-o` | Output to file |

## Testing Response Content
```bash
# Check response contains expected text
RESPONSE=$(curl -sf http://{BACKEND_HOST}:3001/api/items)
if echo "$RESPONSE" | grep -q "expected_value"; then
  echo "PASS"
else
  echo "FAIL: Response missing expected_value"
  echo "$RESPONSE"
  exit 1
fi
```

## Testing HTTP Status Code
```bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://{BACKEND_HOST}:3001/api/items)
if [ "$STATUS" = "200" ]; then
  echo "PASS: Got 200 OK"
else
  echo "FAIL: Expected 200, got $STATUS"
  exit 1
fi
```

## Complete Test Script Template
```bash
#!/bin/bash
set -e

API_URL="http://{BACKEND_HOST}:3001/api"
PASS=0
FAIL=0

test_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"

  echo -n "Testing $name... "
  RESPONSE=$(curl -sf "$url" 2>/dev/null) || { echo "FAIL (request failed)"; FAIL=$((FAIL+1)); return; }

  if echo "$RESPONSE" | grep -q "$expected"; then
    echo "PASS"
    PASS=$((PASS+1))
  else
    echo "FAIL (missing: $expected)"
    FAIL=$((FAIL+1))
  fi
}

# Run tests
test_endpoint "list items" "$API_URL/items" "items"
test_endpoint "health check" "$API_URL/health" "ok"

# Summary
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

## Common Mistakes
- Using localhost instead of actual backend IP
- Forgetting -f flag (hides HTTP errors)
- Not quoting JSON in -d parameter
- Missing Content-Type header for POST/PUT
