# CORS Patterns

## When to Use
- Any API that will be called from a browser
- Cross-origin requests from frontend services
- When you see "CORS policy" errors

## Basic CORS Setup
```javascript
const cors = require('cors');

// Enable all origins (development)
app.use(cors());

// Or with specific configuration
app.use(cors({
  origin: '*',  // Allow all origins
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

## CORS Must Come First
```javascript
// CORRECT order
app.use(cors());           // 1. CORS first
app.use(express.json());   // 2. Body parser
app.get('/api/data', ...); // 3. Routes last

// WRONG order - CORS won't work
app.get('/api/data', ...);
app.use(cors());  // Too late!
```

## Manual CORS Headers (alternative)
```javascript
// If cors package not available
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});
```

## Testing CORS
```bash
# Check OPTIONS preflight response
curl -I -X OPTIONS http://localhost:3001/api/test \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: GET"

# Should see:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, ...
```

## Common Mistakes
- Forgetting to `npm install cors`
- Placing cors() after route definitions
- Not handling OPTIONS preflight requests
- Returning 404 for OPTIONS (should return 200)
