"""
Rate limiting middleware
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from laas.core.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.rate_limit_requests = self.settings.rate_limit_requests
        self.rate_limit_window = self.settings.rate_limit_window
        
        # In-memory rate limiting (for development)
        # In production, this should use Redis
        self.rate_limit_store: Dict[str, Dict[str, int]] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(request):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {self.rate_limit_requests} requests per {self.rate_limit_window} seconds",
                        "retry_after": self.rate_limit_window
                    }
                },
                headers={
                    "Retry-After": str(self.rate_limit_window),
                    "X-RateLimit-Limit": str(self.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + self.rate_limit_window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id)
        reset_time = int(time.time()) + self.rate_limit_window
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request"""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get tenant ID first
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            return f"tenant:{tenant_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = int(time.time())
        window_start = current_time - self.rate_limit_window
        
        # Clean up old entries
        if client_id in self.rate_limit_store:
            self.rate_limit_store[client_id] = {
                timestamp: count for timestamp, count in self.rate_limit_store[client_id].items()
                if int(timestamp) > window_start
            }
        else:
            self.rate_limit_store[client_id] = {}
        
        # Count requests in current window
        current_requests = sum(self.rate_limit_store[client_id].values())
        
        # Check if limit exceeded
        if current_requests >= self.rate_limit_requests:
            return False
        
        # Increment request count
        timestamp_str = str(current_time)
        if timestamp_str in self.rate_limit_store[client_id]:
            self.rate_limit_store[client_id][timestamp_str] += 1
        else:
            self.rate_limit_store[client_id][timestamp_str] = 1
        
        return True
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        current_time = int(time.time())
        window_start = current_time - self.rate_limit_window
        
        if client_id not in self.rate_limit_store:
            return self.rate_limit_requests
        
        # Count requests in current window
        current_requests = sum(
            count for timestamp, count in self.rate_limit_store[client_id].items()
            if int(timestamp) > window_start
        )
        
        return max(0, self.rate_limit_requests - current_requests)
