# DOM Manipulation Patterns

## When to Use
- Updating page content dynamically
- Handling user interactions
- Building UI components

## Selecting Elements
```javascript
// By ID (single element)
const container = document.getElementById('container');

// By selector (single element)
const button = document.querySelector('.submit-btn');

// By selector (multiple elements)
const items = document.querySelectorAll('.item');
```

## Creating Elements
```javascript
// Create and append
function createCard(data) {
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <h3>${data.title}</h3>
    <p>${data.description}</p>
    <button onclick="handleClick('${data.id}')">Action</button>
  `;
  return card;
}

// Append to container
const container = document.getElementById('cards');
container.appendChild(createCard(data));
```

## Updating Content
```javascript
// Replace all content
container.innerHTML = '<p>New content</p>';

// Clear content
container.innerHTML = '';

// Append HTML
container.innerHTML += '<p>Additional content</p>';

// Text only (safer, no HTML parsing)
element.textContent = 'Plain text';
```

## Event Handling
```javascript
// Inline handler (simple)
<button onclick="handleClick()">Click me</button>

// addEventListener (preferred)
button.addEventListener('click', function(event) {
  event.preventDefault();
  // Handle click
});

// Form submission
form.addEventListener('submit', async function(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  // Process form
});
```

## Building Lists
```javascript
function renderList(items) {
  const container = document.getElementById('list');
  container.innerHTML = items.map(item => `
    <div class="list-item" data-id="${item.id}">
      <span>${item.name}</span>
      <button onclick="deleteItem('${item.id}')">Delete</button>
    </div>
  `).join('');
}
```

## Common Mistakes
- Forgetting to escape user content (XSS risk)
- Using innerHTML when textContent would be safer
- Not checking if element exists before manipulating
- Memory leaks from event listeners not cleaned up
