# Contributing to AutoHeal Locator Demo

Thank you for your interest in contributing to the AutoHeal Locator Demo project! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Adding New Test Scenarios](#adding-new-test-scenarios)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

---

## Getting Started

Before contributing, please:

1. Read the main [README.md](README.md) to understand the project
2. Review existing [issues](https://github.com/yourusername/playwright-autoheal-locators-demo/issues) and [pull requests](https://github.com/yourusername/playwright-autoheal-locators-demo/pulls)
3. Set up the development environment (see below)

---

## How to Contribute

### Reporting Issues

Found a bug or have a suggestion? Please [create an issue](https://github.com/yourusername/playwright-autoheal-locators-demo/issues/new) with:

- **Clear title** describing the issue
- **Steps to reproduce** (for bugs)
- **Expected vs. actual behavior**
- **Environment details** (OS, Java version, Maven version)
- **Error messages or screenshots** (if applicable)

### Suggesting Enhancements

We welcome enhancement suggestions! Please:

- Check if the enhancement has already been suggested
- Provide a clear use case and rationale
- Include examples of how it would work

### Contributing Code

1. **Fork** the repository
2. **Create a branch** for your feature/fix: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the code style guidelines
4. **Test** your changes thoroughly
5. **Commit** with clear, descriptive messages
6. **Push** to your fork: `git push origin feature/your-feature-name`
7. **Submit a pull request** to the main repository

---

## Development Setup

### Prerequisites

- Java 17 or higher
- Maven 3.6+
- Git
- AI API key (Gemini, OpenAI, or Anthropic)

### Clone and Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/playwright-autoheal-locators-demo.git
cd playwright-autoheal-locators-demo

# Install dependencies
mvn clean install

# Install Playwright browsers
mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="install"

# Set API key
export GEMINI_API_KEY="your-gemini-api-key"
```

### Run Tests

```bash
# Run all tests
mvn clean test

# Run specific test
mvn test -Dtest=OrangeHRMLoginTest
```

---

## Adding New Test Scenarios

Want to add more test scenarios to demonstrate AutoHeal? Follow these steps:

### 1. Create a New Page Object

If testing a new page, create a Page Object in `src/main/java/com/autoheal/demo/pages/`:

```java
package com.autoheal.demo.pages;

import com.microsoft.playwright.Page;
import com.autoheal.locator.AutoHealLocator;

public class YourNewPage extends BasePage {

    // Page-specific selectors (intentionally WRONG to demonstrate AutoHeal)
    private static final String YOUR_ELEMENT = "selector-WRONG";

    public YourNewPage(Page page, AutoHealLocator autoHeal) {
        super(page, autoHeal);
    }

    public void yourAction() {
        click(YOUR_ELEMENT, "Description of the element");
    }

    public boolean isElementVisible() {
        return isVisible(YOUR_ELEMENT, "Description");
    }
}
```

### 2. Create a Test Class

Create a test in `src/test/java/com/autoheal/demo/tests/`:

```java
package com.autoheal.demo.tests;

import org.testng.annotations.Test;

public class YourNewTest extends BaseTest {

    @Test(priority = 1, description = "Test description")
    public void testYourScenario() {
        YourNewPage page = new YourNewPage(this.page, autoHeal);

        // Navigate and perform actions
        this.page.navigate("https://example.com");
        page.yourAction();

        // Assertions
        assertTrue(page.isElementVisible(), "Element should be visible");
    }
}
```

### 3. Add to TestNG Suite

Update `testng.xml` to include your new test:

```xml
<test name="Your New Test">
    <classes>
        <class name="com.autoheal.demo.tests.YourNewTest"/>
    </classes>
</test>
```

### 4. Use Intentionally Wrong Selectors

**Key Point**: To demonstrate AutoHeal's healing capabilities, use intentionally wrong selectors:

```java
// Good for demo: Forces AutoHeal to fix it
private static final String USERNAME = "input[name='username-WRONG']";

// Not ideal for demo: Works without healing
private static final String USERNAME = "input[name='username']";
```

### 5. Add Clear Descriptions

Always provide clear element descriptions to help AI healing:

```java
// Good: Clear, specific description
click(LOGIN_BTN, "Login button on the main login page");

// Poor: Vague description
click(LOGIN_BTN, "button");
```

---

## Code Style

### Java Code Style

- **Indentation**: 4 spaces (no tabs)
- **Line length**: Max 120 characters
- **Naming**:
  - Classes: PascalCase (`LoginPage`, `BaseTest`)
  - Methods: camelCase (`testLogin`, `clickButton`)
  - Constants: UPPER_SNAKE_CASE (`LOGIN_BUTTON`, `USERNAME_FIELD`)
- **Comments**: Use for complex logic, not obvious code

### Example:

```java
public class ExamplePage extends BasePage {
    // Constants for selectors
    private static final String LOGIN_BUTTON = "button[type='submit-WRONG']";

    public ExamplePage(Page page, AutoHealLocator autoHeal) {
        super(page, autoHeal);
    }

    /**
     * Performs login with provided credentials
     * @param username User's username
     * @param password User's password
     */
    public void login(String username, String password) {
        type(USERNAME_FIELD, username, "Username input field");
        type(PASSWORD_FIELD, password, "Password input field");
        click(LOGIN_BUTTON, "Login submit button");
    }
}
```

### TestNG Test Style

```java
@Test(priority = 1, description = "Clear description of what the test does")
public void testDescriptiveName() {
    // Arrange
    LoginPage loginPage = new LoginPage(page, autoHeal);

    // Act
    page.navigate("https://example.com");
    loginPage.login("username", "password");

    // Assert
    assertTrue(loginPage.isLoggedIn(), "User should be logged in");
}
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes**: Run all tests and ensure they pass
2. **Update documentation**: Update README or docs if needed
3. **Clean commits**: Squash unnecessary commits
4. **No generated files**: Don't commit `target/`, `test-reports/`, etc.

### PR Title Format

Use clear, descriptive titles:

- `feat: Add new dashboard navigation test`
- `fix: Correct timeout issue in login test`
- `docs: Update troubleshooting guide`
- `refactor: Improve BasePage error handling`

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Changes Made
- List key changes
- Include any breaking changes

## Testing
How did you test these changes?

## Screenshots (if applicable)
Add screenshots showing the changes.

## Checklist
- [ ] Tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] No unnecessary files committed
```

---

## Best Practices

### For AutoHeal Demos

1. **Use wrong selectors** to demonstrate healing capabilities
2. **Add clear descriptions** for all elements
3. **Run in non-headless mode** so users can see the healing in action
4. **Include console logging** to show healing progress
5. **Document expected behavior** in test descriptions

### For Test Architecture

1. **Follow Page Object Model** pattern
2. **Extend BasePage** for all page objects
3. **Extend BaseTest** for all test classes
4. **Keep tests independent** - each test should run standalone
5. **Use meaningful assertions** with clear failure messages

### For Documentation

1. **Keep README updated** with new features
2. **Add examples** for new functionality
3. **Update troubleshooting** for new known issues
4. **Include code snippets** in documentation
5. **Use clear, beginner-friendly language**

---

## Questions?

If you have questions about contributing:

1. Check existing [documentation](README.md)
2. Review [troubleshooting guide](docs/TROUBLESHOOTING.md)
3. Open an [issue](https://github.com/yourusername/playwright-autoheal-locators-demo/issues) with your question
4. Tag it as `question`

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

---

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers this project.

---

**Thank you for contributing to AutoHeal Locator Demo!**

Your contributions help make test automation more resilient and accessible to everyone.
