# File Structure Patterns

## When to Use
- Creating new services or features
- Organizing code into modules
- Setting up a new project area

## Backend Service Structure
```
src/backend/{service-name}/
├── server.js      # Main entry point with Express app
├── package.json   # Dependencies (express, cors, etc.)
└── routes/        # Optional: separate route files
```

**Minimal package.json:**
```json
{
  "name": "{service-name}",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5"
  }
}
```

## Frontend Feature Structure
```
src/frontend/{feature-name}/
├── index.html     # Main HTML page
├── style.css      # Optional: feature-specific styles
└── script.js      # Optional: feature-specific JavaScript
```

## Test Structure
```
src/tests/{area}/
├── test-{feature}.sh    # Individual test script
└── run-all-tests.sh     # Optional: test runner
```

## Common Mistakes
- Putting package.json in project root instead of service directory
- Creating files outside assigned src/{role}/ directory
- Not running npm install in the correct directory
- Missing required files (server.js must exist for backend)

## Important Rules
- Each backend service is INDEPENDENT with its own package.json
- Run `npm install` inside the service directory, NOT project root
- Do NOT modify files outside your assigned role directory
