# Express.js Setup Patterns

## When to Use
- Creating a new backend API service
- Setting up Express server with proper middleware

## Basic Express Template
```javascript
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware - ORDER MATTERS
app.use(cors());              // Enable CORS first
app.use(express.json());      // Parse JSON bodies

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Your routes here
app.get('/api/example', (req, res) => {
  res.json({ message: 'Hello World' });
});

// Start server - MUST bind to 0.0.0.0
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Critical Requirements
1. **Bind to 0.0.0.0** - NOT localhost, NOT 127.0.0.1
2. **Enable CORS before routes** - Required for cross-origin requests
3. **Use express.json()** - For parsing JSON request bodies
4. **Log startup message** - Helps verify server started

## package.json Dependencies
```json
{
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5"
  }
}
```

## Common Mistakes
- Binding to localhost (other machines can't connect)
- Forgetting cors() middleware
- Placing cors() after routes (won't work)
- Missing express.json() for POST/PUT endpoints
- Using `app.listen(PORT)` without host parameter

## Port Assignments
Check your project's config.json for assigned ports:
- General APIs typically use 3001-3004
- Frontend dev server typically uses 3000
