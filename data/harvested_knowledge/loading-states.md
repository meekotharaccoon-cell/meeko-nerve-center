# Loading State Patterns

## When to Use
- Any async operation (API calls, file uploads)
- Long-running processes
- Data fetching on page load

## Basic Loading Pattern
```javascript
async function loadData() {
  const container = document.getElementById('content');
  const loadingEl = document.getElementById('loading');

  // Show loading, hide content
  loadingEl.style.display = 'block';
  container.style.display = 'none';

  try {
    const data = await fetchData();
    renderData(data);
    // Show content, hide loading
    container.style.display = 'block';
  } catch (error) {
    container.innerHTML = `<p class="error">${error.message}</p>`;
    container.style.display = 'block';
  } finally {
    loadingEl.style.display = 'none';
  }
}
```

## Loading Spinner HTML
```html
<div id="loading" class="loading-spinner">
  <div class="spinner"></div>
  <p>Loading...</p>
</div>

<style>
.loading-spinner {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

## Button Loading State
```javascript
async function handleSubmit(button) {
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Saving...';

  try {
    await saveData();
    button.textContent = 'Saved!';
    setTimeout(() => {
      button.textContent = originalText;
      button.disabled = false;
    }, 1500);
  } catch (error) {
    button.textContent = 'Error - Try Again';
    button.disabled = false;
  }
}
```

## Skeleton Loading (Placeholder)
```html
<div class="skeleton-card">
  <div class="skeleton skeleton-title"></div>
  <div class="skeleton skeleton-text"></div>
  <div class="skeleton skeleton-text short"></div>
</div>

<style>
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-title { height: 24px; width: 60%; margin-bottom: 12px; }
.skeleton-text { height: 16px; width: 100%; margin-bottom: 8px; }
.skeleton-text.short { width: 40%; }

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
```

## Common Mistakes
- Not showing loading state at all
- Loading state but no error handling
- Forgetting to hide loading after completion
- Button remains disabled after error
