"""Authentication API documentation."""
from typing import ClassVar


class AuthApiDocs:
    """API documentation for Authentication endpoints."""
    
    login: ClassVar[dict] = {
        "summary": "Authenticate user with email and password, return JWT token",
        "description": (
            "Authenticates a user with email and password. Returns a JWT access token "
            "with user information including role and family details. "
            "User must have Active status and belong to an Active family. "
            "PendingActivation users receive a specific error message."
        ),
    }
    
    logout: ClassVar[dict] = {
        "summary": "Logout user and invalidate session",
        "description": (
            "Logs out the current user. Token invalidation is handled server-side "
            "if token blacklist is implemented. This endpoint always succeeds, "
            "even if the session was already invalid."
        ),
    }
    
    token: ClassVar[dict] = {
        "summary": "OAuth2-compatible token endpoint for Swagger UI authorization",
        "description": (
            "OAuth2-compatible token endpoint that accepts form data (username/password) "
            "and returns an access token. This endpoint is used by Swagger UI for "
            "authorization. The 'username' parameter is treated as email."
        ),
    }
