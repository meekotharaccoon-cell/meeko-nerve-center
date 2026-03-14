# Troubleshooting Guide - AutoHeal Locator Demo

## Table of Contents
1. [Empty Reports](#empty-reports)
2. [Report Generation Issues](#report-generation-issues)
3. [Common Setup Issues](#common-setup-issues)
4. [Test Execution Issues](#test-execution-issues)

---

## Empty Reports

### Issue: Report Shows 0 Total Selectors

**Symptom**: AutoHeal HTML report exists but shows:
- Total Selectors: 0
- DOM Healed: 0
- Empty table with no healing details

**Root Cause**: No healing occurred during test execution.

**Why This Happens**:

| Scenario | What Happens | Report Details |
|----------|--------------|----------------|
| **All locators work** | Elements found on first try | Empty report (0 selectors) |
| **1+ locators break** | AI heals them | Detailed report with healing events |
| **Using cached healing** | Uses previous healing | No new report (cache hit) |

**Solution**:

An empty report is actually **good news** - it means your locators are working correctly! To see AutoHeal's healing capabilities:

1. **Intentionally break a locator**:
```java
// Change from working:
Locator username = autoHeal.find(page,
    page.getByPlaceholder("Username"),
    "Username field");

// To broken (will trigger healing):
Locator username = autoHeal.find(page,
    page.getByPlaceholder("Username_INTENTIONALLY_WRONG"),
    "Username field");
```

2. **Run the test** and check the report - it should now show healing details

**Key Insight**: Reports only show details when locators break and need healing. No broken locators = empty report.

---

## Report Generation Issues

### Issue: No Report File Generated

**Symptom**: No `AutoHeal_Report_*.html` file created after test run.

**Root Cause**: `autoHeal.shutdown()` was not called.

**Critical Requirement**: You **MUST** call `autoHeal.shutdown()` to generate reports!

**What `shutdown()` Does**:
1. Generates and writes HTML/JSON/TXT reports
2. Flushes cache to disk (saves healed selectors)
3. Closes AI service connections
4. Releases resources

**Solution**:

Add `shutdown()` to your test teardown:

```java
@AfterSuite
public void tearDownSuite() {
    // STEP 1: Shutdown AutoHeal FIRST (generates reports)
    if (autoHeal != null) {
        System.out.println("🔄 Shutting down AutoHeal and generating reports...");
        autoHeal.shutdown();
        System.out.println("✅ Reports generated!");
    }

    // STEP 2: Then close browser
    if (browser != null) {
        browser.close();
    }

    // STEP 3: Then close playwright
    if (playwright != null) {
        playwright.close();
    }
}
```

**Common Mistakes**:

❌ **Mistake 1**: No `shutdown()` call at all
❌ **Mistake 2**: Calling `shutdown()` AFTER closing browser
✅ **Correct**: Call `shutdown()` BEFORE closing browser

**Verification**:

Check console output for:
```
🔄 Shutting down AutoHeal and generating reports...
[FILE-CACHE] Saving cache to file before shutdown...
✅ Reports generated!
```

---

### Issue: Report Exists But Table is Empty

**Possible Causes**:
- Test failed before healing could occur
- API key is invalid (AI never called)
- Network issues prevented AI calls
- Framework bug (known issue with reporting system)

**Solution**:

1. **Check console for errors**:
```bash
mvn test -Dtest=YourTest 2>&1 | grep -i "error\|exception"
```

2. **Verify API key is set**:
```cmd
echo %GEMINI_API_KEY%  # Windows CMD
echo $env:GEMINI_API_KEY  # PowerShell
```

3. **Check test actually ran**:
```bash
# Should show "Tests run: 1" (not 0)
mvn test -Dtest=YourTest | grep "Tests run"
```

4. **Known Issue**: The AutoHeal framework reporting system may not track all operations. Use console output and cache files to verify healing is working:

**Check Console Output**:
```
✅ GOOD SIGNS (Healing is working):
- "AI Healing in progress..."
- "AI found alternative selector"
- "Cached healed selector"
- "[FILE-CACHE] Saving cache..."

❌ BAD SIGNS (Issues):
- "AutoHealException: Could not find element"
- "AI healing failed"
- No healing messages at all
```

**Check Cache Files**:
```bash
# If healing occurred, cache files should exist
dir target\autoheal-cache
```

---

## Common Setup Issues

### Issue: API Key Not Found

**Symptom**:
```
Error: AI API key not configured
```

**Solution**: Set the appropriate environment variable:

**Gemini (Recommended)**:
```bash
# Windows CMD
set GEMINI_API_KEY=your-gemini-api-key-here

# Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Linux/Mac
export GEMINI_API_KEY="your-gemini-api-key-here"
```

Get your Gemini API key: https://aistudio.google.com/app/apikey

**OpenAI**:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Anthropic Claude**:
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

**Verify**:
```bash
echo %GEMINI_API_KEY%  # Windows CMD
echo $env:GEMINI_API_KEY  # PowerShell
```

---

### Issue: Playwright Browsers Not Installed

**Symptom**:
```
Error: Executable doesn't exist at /path/to/chromium
```

**Solution**: Install Playwright browsers:
```bash
mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="install"
```

---

### Issue: Tests Run Too Fast (Can't See Actions)

**Solution**: Increase `slowMo` in `BaseTest.java`:

```java
// In BaseTest.java
browser = playwright.chromium().launch(
    new BrowserType.LaunchOptions()
        .setHeadless(false)
        .setSlowMo(1000)  // Change from 500 to 1000 or higher
);
```

---

## Test Execution Issues

### Issue: Tests Fail on First Run

**Expected Behavior**: First run may be slower due to AI healing (5-10 seconds per healed locator).

**Solution**:
- Run tests again - subsequent runs use cached selectors and are much faster (<100ms)
- This is normal and expected behavior

**Performance Comparison**:
- **First run (no cache)**: 5-10 seconds per healed locator
- **Second run (cached)**: <100ms per cached locator

---

### Issue: Cache Not Being Used

**Symptom**: Every test run is slow, healing happens every time.

**Solution**:

1. **Verify cache is enabled** in `autoheal.properties`:
```properties
autoheal.cache.type=PERSISTENT_FILE
autoheal.cache.expire-after-write-hours=24
```

2. **Check cache directory exists**:
```bash
dir target\autoheal-cache
```

3. **Check cache files are being created**:
- After first run with healing, cache files should exist
- Files are named based on locator hash

4. **To force fresh healing** (clear cache):
```bash
rmdir /s /q target\autoheal-cache  # Windows
rm -rf target/autoheal-cache        # Linux/Mac
```

---

### Issue: Test Hangs or Times Out

**Possible Causes**:
- AI service is slow or unresponsive
- Network connectivity issues
- API rate limiting

**Solution**:

1. **Check network connectivity**:
```bash
ping api.google.com  # For Gemini
ping api.openai.com  # For OpenAI
```

2. **Check API rate limits**:
- Gemini free tier: 15 requests per minute
- Consider upgrading or using different AI provider

3. **Increase timeout** in configuration:
```java
AutoHealConfiguration config = AutoHealConfiguration.builder()
    .ai(AIConfig.builder()
        .timeout(Duration.ofSeconds(30))  // Increase from default
        .build())
    .build();
```

---

### Issue: All Tests Skip or Show "Tests run: 0"

**Possible Causes**:
- Test class not found
- TestNG configuration issue
- Missing test annotations

**Solution**:

1. **Verify test class name is correct**:
```bash
mvn test -Dtest=OrangeHRMLoginTest  # Must match actual class name
```

2. **Check testng.xml includes your test**:
```xml
<test name="Login Tests">
    <classes>
        <class name="com.autoheal.demo.tests.OrangeHRMLoginTest"/>
    </classes>
</test>
```

3. **Verify @Test annotations are present**:
```java
@Test  // Must have this annotation
public void testLogin() {
    // test code
}
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the main README**: `README.md`
2. **Check migration guide**: `docs/MIGRATION_GUIDE.md`
3. **Check locators guide**: `docs/LOCATORS_GUIDE.md`
4. **Enable debug logging** and check console output
5. **Verify all prerequisites** are installed (Java 17, Maven 3.6+, API key set)

---

## Quick Diagnostics Checklist

Before asking for help, verify:

- [ ] Java 17 or higher installed (`java -version`)
- [ ] Maven 3.6+ installed (`mvn -version`)
- [ ] API key is set correctly (`echo %GEMINI_API_KEY%`)
- [ ] Playwright browsers installed
- [ ] `autoHeal.shutdown()` is called in teardown
- [ ] Network connectivity to AI service
- [ ] Cache directory is writable
- [ ] TestNG configuration includes your tests
- [ ] Test methods have `@Test` annotation

---

**Remember**: Many "issues" are actually expected behavior. Empty reports mean your locators are working correctly!
