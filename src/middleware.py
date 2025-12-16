"""FastAPI middleware for request/response handling."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from src.utils import generate_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Get X-Request-ID from request header, or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = generate_request_id()
        
        # Store in request state for use in routes
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add X-Request-ID to response header
        response.headers["X-Request-ID"] = request_id
        
        # Add cache control headers for all API endpoints to prevent browser caching
        # This ensures sensitive data is never cached by browsers
        # CRITICAL: This prevents security issues where cached authenticated responses
        # are served to unauthenticated requests
        if request.url.path.startswith("/v1/"):
            # Always set aggressive cache control headers (override any existing ones)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            # Vary header ensures responses are cached separately per Authorization header
            response.headers["Vary"] = "Authorization"
        
        return response

