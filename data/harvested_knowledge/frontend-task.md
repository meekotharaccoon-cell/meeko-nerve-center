# Task: Create User Registration Frontend

## Description
Create a simple web page for user registration that communicates with the backend API. Follow the API contract in `examples/coordinated-user-system/api-contract.md`.

## API Contract Reference
Follow the contract in api-contract.md (same directory).

Backend URL: http://100.x.x.1:3001 (replace with your backend agent's Tailscale IP)

## Requirements
- Registration form with:
  - Name input field
  - Email input field
  - Submit button
- Display list of existing users below the form
- On form submit:
  - POST to /api/users
  - Show success message
  - Refresh user list
  - Clear form
- Handle errors:
  - Show validation errors
  - Show duplicate email error
  - Show network errors
- Loading states:
  - Show "Loading..." when fetching users
  - Disable submit button while saving
- Clean, simple styling

## Files to Create
- src/frontend/users/index.html
- src/frontend/users/style.css
- src/frontend/users/app.js

## Success Criteria
- [ ] Form displays correctly
- [ ] Can create new users
- [ ] User list updates after creation
- [ ] Error messages display properly
- [ ] Loading states work
- [ ] No JavaScript console errors
