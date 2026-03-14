# Task: Create Hello API

## Description
Create a simple Express server with a hello endpoint. This is a basic example task to verify your Ralph Loops setup is working.

## Requirements
- GET /api/hello returns { "message": "Hello from Ralph!" }
- Server runs on port 3001
- Bind to 0.0.0.0 (important - not localhost!)
- Enable CORS for frontend access
- Include basic error handling

## Files to Create
- src/backend/hello/server.js
- src/backend/hello/package.json

## Success Criteria
- [ ] Server starts without errors
- [ ] Endpoint returns correct JSON
- [ ] Server is accessible from other machines on the network
- [ ] CORS headers are present in response
