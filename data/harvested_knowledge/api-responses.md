# API Response Patterns

## When to Use
- Returning data from API endpoints
- Handling errors consistently
- Designing REST API responses

## Success Response Patterns
```javascript
// Single item
app.get('/api/items/:id', (req, res) => {
  const item = findItem(req.params.id);
  if (item) {
    res.json(item);
  } else {
    res.status(404).json({ error: 'Item not found' });
  }
});

// Collection
app.get('/api/items', (req, res) => {
  const items = getAllItems();
  res.json(items);  // Return array directly
});

// Created resource
app.post('/api/items', (req, res) => {
  const newItem = createItem(req.body);
  res.status(201).json(newItem);  // 201 = Created
});
```

## Error Response Pattern
```javascript
// Consistent error format
function sendError(res, status, message) {
  res.status(status).json({ error: message });
}

// Usage
app.get('/api/resource', (req, res) => {
  try {
    const data = getData();
    res.json(data);
  } catch (error) {
    sendError(res, 500, error.message);
  }
});
```

## HTTP Status Codes
| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Unexpected error |

## Pagination Pattern
```javascript
app.get('/api/items', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const offset = (page - 1) * limit;

  const items = getItems(offset, limit);
  const total = getTotalCount();

  res.json({
    items: items,
    pagination: {
      page: page,
      limit: limit,
      total: total,
      pages: Math.ceil(total / limit)
    }
  });
});
```

## Common Mistakes
- Returning HTML instead of JSON
- Not setting Content-Type (express.json() handles this)
- Using wrong status codes (200 for errors)
- Inconsistent error message format
