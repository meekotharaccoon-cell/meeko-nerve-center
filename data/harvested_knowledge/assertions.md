# Test Assertions and Output

## When to Use
- Writing bash test scripts
- Verifying expected outcomes
- Reporting test results

## Exit Code Convention
```bash
# PASS - exit 0
if [ condition_is_true ]; then
  echo "PASS"
  exit 0
fi

# FAIL - exit non-zero
echo "FAIL"
exit 1
```

## Basic Assertions
```bash
# Assert equality
assert_eq() {
  local expected="$1"
  local actual="$2"
  local message="${3:-Values should be equal}"

  if [ "$expected" = "$actual" ]; then
    echo "PASS: $message"
    return 0
  else
    echo "FAIL: $message"
    echo "  Expected: $expected"
    echo "  Actual: $actual"
    return 1
  fi
}

# Assert not empty
assert_not_empty() {
  local value="$1"
  local message="${2:-Value should not be empty}"

  if [ -n "$value" ]; then
    echo "PASS: $message"
    return 0
  else
    echo "FAIL: $message"
    return 1
  fi
}

# Assert contains
assert_contains() {
  local haystack="$1"
  local needle="$2"
  local message="${3:-Should contain expected value}"

  if echo "$haystack" | grep -q "$needle"; then
    echo "PASS: $message"
    return 0
  else
    echo "FAIL: $message"
    echo "  Looking for: $needle"
    echo "  In: $haystack"
    return 1
  fi
}
```

## File Assertions
```bash
# Assert file exists
assert_file_exists() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "PASS: File exists: $file"
    return 0
  else
    echo "FAIL: File not found: $file"
    return 1
  fi
}

# Assert directory exists
assert_dir_exists() {
  local dir="$1"
  if [ -d "$dir" ]; then
    echo "PASS: Directory exists: $dir"
    return 0
  else
    echo "FAIL: Directory not found: $dir"
    return 1
  fi
}
```

## HTTP Status Assertions
```bash
assert_http_status() {
  local url="$1"
  local expected_status="$2"

  local actual_status=$(curl -s -o /dev/null -w "%{http_code}" "$url")

  if [ "$actual_status" = "$expected_status" ]; then
    echo "PASS: $url returned $expected_status"
    return 0
  else
    echo "FAIL: $url returned $actual_status (expected $expected_status)"
    return 1
  fi
}
```

## Test Script Structure
```bash
#!/bin/bash
#===============================================
# Test: {test-name}
# Tests: {what it tests}
#===============================================

set -euo pipefail

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
  local name="$1"
  shift
  echo -n "Test: $name... "
  if "$@"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

# Tests here
run_test "health check" assert_http_status "http://{BACKEND_HOST}:3001/health" "200"
run_test "list items" assert_contains "$(curl -sf http://{BACKEND_HOST}:3001/api/items)" "items"

# Summary
echo ""
echo "=============================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "=============================="

[ $TESTS_FAILED -eq 0 ] && exit 0 || exit 1
```

## Common Mistakes
- Forgetting to exit with proper code
- Not printing PASS/FAIL clearly
- Complex conditionals without logging
- Not capturing stderr for debugging
