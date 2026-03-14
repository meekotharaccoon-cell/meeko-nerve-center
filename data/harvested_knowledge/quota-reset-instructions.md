# When Quota Resets - Instructions

## 1. Create the pending task
```bash
ssh pc1 "cd ~/project && cat > tasks/pending/backend/007-auth-endpoints.md << 'EOF'
# Task: Create Auth Endpoints

## Description
Create authentication REST API with JWT.

## Requirements
- POST /api/auth/register - Register user (email, password, name)
- POST /api/auth/login - Login, return JWT token
- GET /api/auth/me - Get current user (requires valid JWT)
- Use jsonwebtoken for JWT (add to package.json)
- Use existing userStore.js from src/backend/auth/
- Server on port 3002, bind to 0.0.0.0, enable CORS

## Files to Create
- src/backend/auth/server.js
- src/backend/auth/middleware.js
EOF
git add -A && git commit -m 'Add auth endpoints task' && git push origin main"
```

## 2. Start the backend worker
```bash
ssh pc1 "cd ~/project && nohup ./scripts/worker.sh backend </dev/null >/dev/null 2>&1 &"
```

## 3. Monitor progress
```bash
ssh pc1 "tail -f ~/project/logs/backend-$(date +%Y%m%d).log"
```

## 4. Verify completion
```bash
ssh pc1 "ls ~/project/src/backend/auth/"
# Should see: server.js, middleware.js, userStore.js, package.json
```

## 5. Test the auth API
```bash
ssh pc1 "cd ~/project/src/backend/auth && node server.js &"
curl http://100.x.x.1:3002/api/auth/register -X POST -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"123456","name":"Test"}'
```
