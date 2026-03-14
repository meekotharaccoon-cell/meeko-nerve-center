# Task: Create User Registration API

## Description
Create an Express API for user registration that follows the API contract in `specs/user-api.md` (or see `examples/coordinated-user-system/api-contract.md`).

## API Contract Reference
Follow the contract in api-contract.md (same directory).

## Requirements
- Implement all endpoints from the API contract:
  - POST /api/users (create user)
  - GET /api/users/:id (get user by ID)
  - GET /api/users (list all users)
- Use in-memory storage (array) for users
- Auto-increment user IDs
- Add createdAt timestamp to new users
- Validate required fields (name, email)
- Check for duplicate emails
- Server runs on port 3001
- Bind to 0.0.0.0 (not localhost!)
- Enable CORS for frontend access

## Files to Create
- src/backend/users/server.js
- src/backend/users/package.json

## Success Criteria
- [ ] All three endpoints work correctly
- [ ] Returns correct HTTP status codes
- [ ] Validates required fields
- [ ] Rejects duplicate emails
- [ ] CORS enabled
- [ ] Server accessible from other machines
