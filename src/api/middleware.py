"""
Custom Middleware for FinSolve RBAC Chatbot API
Production-grade middleware for logging, rate limiting, security, and monitoring.

Author: Peter Pandey
Version: 1.0.0
"""

import time
import uuid
import json
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_403_FORBIDDEN
from loguru import logger
import asyncio


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware for request/response tracking
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Request started - ID: {request_id} | "
            f"Method: {request.method} | "
            f"Path: {request.url.path} | "
            f"IP: {client_ip} | "
            f"User-Agent: {user_agent}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed - ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"Request failed - ID: {request_id} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with sliding window algorithm
    """
    
    def __init__(self, app, requests_per_minute: int = 60, burst_limit: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_history: Dict[str, deque] = defaultdict(deque)
        self.burst_history: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup task
        asyncio.create_task(self._cleanup_task())
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = datetime.now()
        
        # Check rate limits
        if not self._check_rate_limit(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60,
                    "timestamp": time.time()
                }
            )
        
        # Check burst limit
        if not self._check_burst_limit(client_ip, current_time):
            logger.warning(f"Burst limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Burst limit exceeded",
                    "message": f"Maximum {self.burst_limit} requests in 10 seconds allowed",
                    "retry_after": 10,
                    "timestamp": time.time()
                }
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str, current_time: datetime) -> bool:
        """Check if client is within rate limit"""
        history = self.request_history[client_ip]
        cutoff_time = current_time - timedelta(minutes=1)
        
        # Remove old requests
        while history and history[0] < cutoff_time:
            history.popleft()
        
        return len(history) < self.requests_per_minute
    
    def _check_burst_limit(self, client_ip: str, current_time: datetime) -> bool:
        """Check if client is within burst limit"""
        history = self.burst_history[client_ip]
        cutoff_time = current_time - timedelta(seconds=10)
        
        # Remove old requests
        while history and history[0] < cutoff_time:
            history.popleft()
        
        return len(history) < self.burst_limit
    
    def _record_request(self, client_ip: str, current_time: datetime):
        """Record a request for rate limiting"""
        self.request_history[client_ip].append(current_time)
        self.burst_history[client_ip].append(current_time)
    
    async def _cleanup_task(self):
        """Periodic cleanup of old request history"""
        while True:
            await asyncio.sleep(300)  # Cleanup every 5 minutes
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1)
            
            # Cleanup request history
            for client_ip in list(self.request_history.keys()):
                history = self.request_history[client_ip]
                while history and history[0] < cutoff_time:
                    history.popleft()
                
                # Remove empty histories
                if not history:
                    del self.request_history[client_ip]
            
            # Cleanup burst history
            for client_ip in list(self.burst_history.keys()):
                history = self.burst_history[client_ip]
                burst_cutoff = current_time - timedelta(minutes=1)
                while history and history[0] < burst_cutoff:
                    history.popleft()
                
                if not history:
                    del self.burst_history[client_ip]


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for headers and basic protection
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            "script", "javascript", "vbscript", "onload", "onerror",
            "eval(", "alert(", "document.cookie", "window.location"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check blocked IPs
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
        
        # Check for suspicious patterns in query parameters
        if self._contains_suspicious_content(str(request.url)):
            logger.warning(f"Suspicious request detected from {client_ip}: {request.url}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Suspicious request detected"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _contains_suspicious_content(self, content: str) -> bool:
        """Check for suspicious patterns"""
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in self.suspicious_patterns)
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware for monitoring and observability
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "requests_by_method": defaultdict(int),
            "requests_by_status": defaultdict(int),
            "requests_by_endpoint": defaultdict(int),
            "response_times": deque(maxlen=1000),
            "errors": deque(maxlen=100)
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment total requests
        self.metrics["total_requests"] += 1
        self.metrics["requests_by_method"][request.method] += 1
        self.metrics["requests_by_endpoint"][request.url.path] += 1
        
        try:
            response = await call_next(request)
            
            # Record metrics
            process_time = time.time() - start_time
            self.metrics["response_times"].append(process_time)
            self.metrics["requests_by_status"][response.status_code] += 1
            
            # Add metrics headers
            response.headers["X-Response-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Record error
            self.metrics["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "endpoint": request.url.path,
                "method": request.method,
                "processing_time": process_time
            })
            
            self.metrics["requests_by_status"][500] += 1
            
            raise
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        response_times = list(self.metrics["response_times"])
        
        return {
            "total_requests": self.metrics["total_requests"],
            "requests_by_method": dict(self.metrics["requests_by_method"]),
            "requests_by_status": dict(self.metrics["requests_by_status"]),
            "requests_by_endpoint": dict(self.metrics["requests_by_endpoint"]),
            "response_time_stats": {
                "count": len(response_times),
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0
            },
            "recent_errors": list(self.metrics["errors"])[-10:],  # Last 10 errors
            "timestamp": datetime.now().isoformat()
        }


# Global metrics instance for access from routes
metrics_middleware = MetricsMiddleware(None)
