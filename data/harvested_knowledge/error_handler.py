"""
Error handler middleware
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler middleware"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of exceptions"""

        # Log the exception
        logger.exception(f"Unhandled exception: {exc}")

        # Handle HTTP exceptions
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "type": "http_exception",
                        "message": exc.detail,
                        "status_code": exc.status_code
                    }
                }
            )

        # Handle validation errors
        if isinstance(exc, RequestValidationError):
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "type": "validation_error",
                        "message": "Request validation failed",
                        "details": exc.errors(),
                        "status_code": 422
                    }
                }
            )

        # Handle database errors
        if isinstance(exc, SQLAlchemyError):
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "database_error",
                        "message": "Database operation failed",
                        "status_code": 500
                    }
                }
            )

        # Handle all other exceptions
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_server_error",
                    "message": "Internal server error",
                    "status_code": 500
                }
            }
        )
