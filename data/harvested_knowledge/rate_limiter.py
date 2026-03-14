"""
Rate limiter middleware
"""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.requests: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)

        # Check rate limit
        if not self.is_allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60
                    }
                }
            )

        response = await call_next(request)
        return response

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limit"""
        current_time = time.time()
        current_minute = int(current_time // 60)

        # Get or initialize client data
        if client_ip not in self.requests:
            self.requests[client_ip] = (0, current_minute)
            return True

        request_count, window_start = self.requests[client_ip]

        # Reset counter if we're in a new window
        if window_start != current_minute:
            self.requests[client_ip] = (1, current_minute)
            return True

        # Check if limit exceeded
        if request_count >= self.requests_per_minute:
            return False

        # Increment counter
        self.requests[client_ip] = (request_count + 1, current_minute)
        return True

    def cleanup(self):
        """Clean up old entries (call periodically)"""
        current_time = time.time()
        current_minute = int(current_time // 60)

        expired_ips = [
            ip for ip, (_, window_start) in self.requests.items()
            if window_start != current_minute
        ]

        for ip in expired_ips:
            del self.requests[ip]
