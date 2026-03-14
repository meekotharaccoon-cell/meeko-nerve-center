# API Contract: User System

This contract defines the interface between frontend and backend for the user registration system.

## Base URL
Backend server: http://100.x.x.1:3001 (replace with your backend agent's Tailscale IP)

## Endpoints

### POST /api/users
Create a new user.

**Request:**
```json
{
  "name": "string",
  "email": "string"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "string",
  "email": "string",
  "createdAt": "ISO8601 timestamp"
}
```

**Errors:**
- 400: Missing required fields
- 409: Email already exists

### GET /api/users/:id
Get a user by ID.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "string",
  "email": "string",
  "createdAt": "ISO8601 timestamp"
}
```

**Errors:**
- 404: User not found

### GET /api/users
List all users.

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "name": "string",
      "email": "string",
      "createdAt": "ISO8601 timestamp"
    }
  ],
  "total": 1
}
```

## Field Names (IMPORTANT)
Use these exact field names in both frontend and backend:
- `name` (not "username" or "fullName")
- `email` (not "mail" or "emailAddress")
- `id` (not "userId" or "_id")
- `createdAt` (not "created_at" or "timestamp")

## CORS
Backend must include these headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`
