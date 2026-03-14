# Playwright Locators Guide - Used in OrangeHRM Demo

## Overview

This demo now uses **Playwright's recommended locators** instead of generic CSS selectors. This follows Playwright best practices for more resilient, accessible tests.

## Playwright Locator Types Used

### 1. **getByRole()** - Most Recommended ⭐

Used for elements with semantic ARIA roles (buttons, links, headings, etc.)

```java
// Button locator
page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Login"))

// Link locator
page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("PIM"))

// Heading locator
page.getByRole(AriaRole.HEADING, new Page.GetByRoleOptions().setName("Dashboard"))
```

**Where used in demo:**
- Login button
- Navigation links (Admin, PIM, Leave, Dashboard)
- Add/Save/Search buttons
- Dashboard heading

### 2. **getByPlaceholder()** - For Input Fields

Used for input fields with placeholder text

```java
// Username field
page.getByPlaceholder("Username")

// Password field
page.getByPlaceholder("Password")

// Employee name fields
page.getByPlaceholder("First Name")
page.getByPlaceholder("Middle Name")
page.getByPlaceholder("Last Name")
```

**Where used in demo:**
- Login form (username, password)
- Employee form (first/middle/last name)
- Search fields

### 3. **getByLabel()** - For Labeled Inputs

Used for inputs associated with labels (not heavily used in OrangeHRM)

```java
page.getByLabel("Email Address")
```

### 4. **getByText()** - For Text Content

Used to find elements by their text content

```java
page.getByText("Employee Management")
```

### 5. **locator()** - Fallback for Complex Cases

Used when semantic locators don't work (tables, grids, etc.)

```java
// Table locator
page.locator(".oxd-table").first()
```

**Where used in demo:**
- Results tables (when no better semantic option exists)

## AutoHeal Integration

All Playwright locators work seamlessly with AutoHeal:

```java
// Option 1: Pass Playwright locator directly
Locator element = autoHeal.find(
    page,
    page.getByPlaceholder("Username"),  // Playwright locator
    "Username input field"               // Semantic description for AI
);

// Option 2: Traditional CSS selector (fallback)
Locator element = autoHeal.find(
    page,
    "input[name='username']",           // CSS selector
    "Username input field"              // Semantic description for AI
);
```

## Benefits of Playwright Locators

| Benefit | Description |
|---------|-------------|
| **Accessibility** | Forces thinking about ARIA roles and accessibility |
| **Resilience** | Less brittle than CSS selectors |
| **Readability** | Self-documenting test code |
| **Best Practice** | Follows Playwright recommendations |
| **AutoHeal Ready** | Works perfectly with AI healing |

## Playwright Locator Priority (Recommended Order)

1. **getByRole()** - Best for accessibility
2. **getByLabel()** - Best for form fields
3. **getByPlaceholder()** - Good for inputs
4. **getByText()** - Good for content
5. **getByTestId()** - Good for custom test attributes
6. **locator()** - Use as last resort

## Examples from OrangeHRM Demo

### Login Test
```java
// Username with placeholder
Locator usernameField = autoHeal.find(
    page,
    page.getByPlaceholder("Username"),
    "Username input field with placeholder"
);

// Password with placeholder
Locator passwordField = autoHeal.find(
    page,
    page.getByPlaceholder("Password"),
    "Password input field with placeholder"
);

// Login button with role
Locator loginButton = autoHeal.find(
    page,
    page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Login")),
    "Login button with accessible role"
);
```

### Navigation Test
```java
// Navigate using link role
Locator pimMenu = autoHeal.find(
    page,
    page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("PIM")),
    "PIM menu link in main navigation"
);
```

### Add Employee Test
```java
// Add button with role
Locator addButton = autoHeal.find(
    page,
    page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Add")),
    "Add Employee button"
);

// First name with placeholder
Locator firstNameField = autoHeal.find(
    page,
    page.getByPlaceholder("First Name"),
    "Employee first name input field"
);

// Save button with role
Locator saveButton = autoHeal.find(
    page,
    page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Save")),
    "Save employee button"
);
```

## When AutoHeal Kicks In

Even with Playwright locators, if the page structure changes:

1. **Playwright locator fails** (e.g., placeholder text changes)
2. **AutoHeal activates** using your semantic description
3. **AI analyzes** the page (DOM + screenshot)
4. **Finds element** based on semantic meaning
5. **Returns working locator** and caches it

## Chaining Locators

Playwright supports chaining for more specific targeting:

```java
// Find button within a specific form
page.locator("form.login-form")
    .getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Submit"));

// First occurrence
page.getByPlaceholder("Type for hints...").first();
```

## Complete AriaRole Options

```java
AriaRole.ALERT
AriaRole.BUTTON
AriaRole.CHECKBOX
AriaRole.HEADING
AriaRole.LINK
AriaRole.LISTBOX
AriaRole.MENUITEM
AriaRole.NAVIGATION
AriaRole.OPTION
AriaRole.RADIO
AriaRole.SEARCHBOX
AriaRole.TABLE
AriaRole.TEXTBOX
// ... and many more
```

## Migration from CSS Selectors

### Before (CSS Selectors)
```java
autoHeal.find(page, "input[name='username']", "Username field");
autoHeal.find(page, "button[type='submit']", "Login button");
autoHeal.find(page, "text=PIM", "PIM menu");
```

### After (Playwright Locators)
```java
autoHeal.find(page, page.getByPlaceholder("Username"), "Username field");
autoHeal.find(page, page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Login")), "Login button");
autoHeal.find(page, page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("PIM")), "PIM menu");
```

## Testing Locators Interactively

Use Playwright Inspector to test locators:

```bash
# Set PWDEBUG environment variable
set PWDEBUG=1
mvn test -Dtest=OrangeHRMMinimalDemo
```

Then in the inspector, try:
```javascript
page.getByPlaceholder("Username")
page.getByRole("button", { name: "Login" })
```

## Best Practices

1. ✅ **Prefer role-based** locators for interactive elements
2. ✅ **Use placeholder** for input fields
3. ✅ **Use getByText** for content verification
4. ✅ **Add .first()** when multiple matches exist
5. ✅ **Keep semantic descriptions** clear for AutoHeal
6. ❌ **Avoid CSS selectors** unless absolutely necessary
7. ❌ **Avoid XPath** unless absolutely necessary

## Resources

- **Playwright Locators Docs**: https://playwright.dev/docs/locators
- **Playwright Best Practices**: https://playwright.dev/docs/best-practices
- **ARIA Roles**: https://www.w3.org/TR/wai-aria-1.1/#role_definitions

## Summary

The OrangeHRM demo now demonstrates:
- ✅ Playwright best practice locators
- ✅ AutoHeal AI-powered self-healing
- ✅ Accessible, resilient test code
- ✅ Both minimal and full configuration options

Run the demo to see Playwright locators + AutoHeal in action:
```bash
mvn clean test -Dtest=OrangeHRMEnhancedDemo
mvn clean test -Dtest=OrangeHRMMinimalDemo
```
