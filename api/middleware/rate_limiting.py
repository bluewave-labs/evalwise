"""
Rate limiting middleware to prevent API abuse
"""
import time
import logging
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from config import settings
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware
    Different limits for authenticated vs unauthenticated users
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Rate limits (requests per minute) - Increased 10x for testing
        self.unauthenticated_limit = 200  # 20 * 10 for easier testing
        self.authenticated_limit = 1000   # 100 * 10 for authenticated users
        self.admin_limit = 5000          # 500 * 10 for admin users
        
        # Window size in seconds
        self.window_size = 60
        
        # Storage for rate limiting data
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.last_cleanup = time.time()
        
        # Cleanup interval (seconds)
        self.cleanup_interval = 300  # 5 minutes
        
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Determine rate limit based on authentication
        rate_limit = await self._get_rate_limit(request)
        
        # Check rate limit
        if not self._is_request_allowed(client_id, rate_limit):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Record the request
        self._record_request(client_id)
        
        # Clean up old entries periodically
        self._periodic_cleanup()
        
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_id, rate_limit)
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address for unauthenticated requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Use the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    async def _get_rate_limit(self, request: Request) -> int:
        """Determine rate limit based on user authentication and role"""
        
        # Check if user is authenticated and get their role
        user = getattr(request.state, 'current_user', None)
        
        if user:
            # Check if user is admin/superuser
            if getattr(user, 'is_superuser', False):
                return self.admin_limit
            # Regular authenticated user
            return self.authenticated_limit
        
        # Unauthenticated user
        return self.unauthenticated_limit
    
    def _is_request_allowed(self, client_id: str, rate_limit: int) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        # Get request history for this client
        requests = self.request_counts[client_id]
        
        # Remove requests outside the time window
        while requests and requests[0] < now - self.window_size:
            requests.popleft()
        
        # Check if we're within the limit
        return len(requests) < rate_limit
    
    def _record_request(self, client_id: str) -> None:
        """Record a new request for the client"""
        now = time.time()
        self.request_counts[client_id].append(now)
    
    def _add_rate_limit_headers(self, response: Response, client_id: str, rate_limit: int) -> None:
        """Add rate limiting headers to response"""
        now = time.time()
        requests = self.request_counts[client_id]
        
        # Count current requests in window
        current_requests = sum(1 for req_time in requests if req_time > now - self.window_size)
        
        # Add headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_requests))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_size))
    
    def _periodic_cleanup(self) -> None:
        """Periodically clean up old request data"""
        now = time.time()
        
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Clean up old entries
        cutoff_time = now - self.window_size * 2  # Keep data for 2x window size
        
        clients_to_remove = []
        for client_id, requests in self.request_counts.items():
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Mark empty clients for removal
            if not requests:
                clients_to_remove.append(client_id)
        
        # Remove empty clients
        for client_id in clients_to_remove:
            del self.request_counts[client_id]
        
        self.last_cleanup = now
        
        logger.debug(f"Rate limiter cleanup completed. Active clients: {len(self.request_counts)}")


class IPBasedRateLimiter:
    """
    Simple IP-based rate limiter for specific endpoints
    """
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed to make request"""
        now = time.time()
        requests = self.requests[ip_address]
        
        # Remove old requests
        while requests and requests[0] < now - 60:  # 60 seconds window
            requests.popleft()
        
        # Check limit
        if len(requests) >= self.requests_per_minute:
            return False
        
        # Record request
        requests.append(now)
        return True


# Global rate limiter instances for specific use cases
login_rate_limiter = IPBasedRateLimiter(5)  # 5 login attempts per minute per IP
password_reset_rate_limiter = IPBasedRateLimiter(3)  # 3 reset attempts per minute per IP