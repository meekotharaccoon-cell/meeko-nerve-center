# API Contract: User System

This is an example API contract. Create similar files in `specs/` to coordinate frontend and backend development.

## Purpose

When you have tasks that span frontend and backend, define the API contract FIRST. Both agents reference this same document to ensure compatibility.

## Base URL

Backend server: http://100.x.x.1:3001

(Replace `100.x.x.1` with your backend agent's Tailscale IP)

## Endpoints

### POST /api/users

Create a new user.

**Request:**
```json
{
  "name": "string (required)",
  "email": "string (required)"
}
```

**Success Response (201 Created):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields
- `409 Conflict` - Email already exists

### GET /api/users/:id

Get a specific user by ID.

**Success Response (200 OK):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - User does not exist

### GET /api/users

List all users.

**Success Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

## Field Names (CRITICAL)

**Use these exact names in both frontend and backend:**

| Field | Correct | Wrong |
|-------|---------|-------|
| User's name | `name` | `username`, `fullName`, `user_name` |
| Email address | `email` | `mail`, `emailAddress`, `e_mail` |
| User ID | `id` | `userId`, `_id`, `user_id` |
| Creation time | `createdAt` | `created_at`, `timestamp`, `created` |

---

## CORS Configuration

Backend MUST return these headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Usage in Tasks

Reference this contract in your task files:

**Backend task:**
```markdown
## Requirements
- Follow the API contract in specs/example-api-contract.md
- Implement all endpoints exactly as specified
```

**Frontend task:**
```markdown
## Requirements
- Follow the API contract in specs/example-api-contract.md
- Backend URL: http://100.x.x.1:3001
```

This ensures both agents create compatible code that works together.
