# Fetch API Patterns

## When to Use
- Making HTTP requests to backend APIs
- Loading data from external services
- Submitting forms to APIs

## Basic GET Request
```javascript
async function fetchData() {
  try {
    const response = await fetch('http://{BACKEND_HOST}:3001/api/items');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Fetch failed:', error);
    throw error;
  }
}
```

## POST Request with JSON Body
```javascript
async function createItem(itemData) {
  try {
    const response = await fetch('http://{BACKEND_HOST}:3001/api/items', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(itemData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Create failed:', error);
    throw error;
  }
}
```

## DELETE Request
```javascript
async function deleteItem(id) {
  const response = await fetch(`http://{BACKEND_HOST}:3001/api/items/${id}`, {
    method: 'DELETE'
  });
  return response.ok;
}
```

## With Loading State
```javascript
async function loadAndDisplay() {
  const container = document.getElementById('items');
  container.innerHTML = '<p>Loading...</p>';

  try {
    const items = await fetchData();
    container.innerHTML = items.map(item =>
      `<div class="item">${item.name}</div>`
    ).join('');
  } catch (error) {
    container.innerHTML = `<p class="error">Failed to load: ${error.message}</p>`;
  }
}
```

## Common Mistakes
- Forgetting to check response.ok
- Not parsing JSON (missing .json())
- Using localhost instead of actual backend IP
- Missing Content-Type header for POST
- Not handling network errors

## Backend URLs
Use the actual backend agent IP from config, NOT localhost:
- Backend API: http://{BACKEND_HOST}:3001
- Auth API: http://{BACKEND_HOST}:3002
