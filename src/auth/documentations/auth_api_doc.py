"""Authentication API documentation."""
from typing import ClassVar


class AuthApiDocs:
    """API documentation for Authentication endpoints."""
    
    login: ClassVar[dict] = {
        "summary": "Purpose of this API is to authenticate user with email and password and return JWT token",
        "description": (
            "Authenticates a user with email and password. Returns a JWT access token "
            "with user information including role and family details. "
            "User must have Active status and belong to an Active family. "
            "PendingActivation users receive a specific error message."
        ),
    }
    
    logout: ClassVar[dict] = {
        "summary": "Purpose of this API is to logout user and invalidate session",
        "description": (
            "Logs out the current user. Token invalidation is handled server-side "
            "if token blacklist is implemented. This endpoint always succeeds, "
            "even if the session was already invalid."
        ),
    }
    
    token: ClassVar[dict] = {
        "summary": "Purpose of this API is to provide OAuth2-compatible token endpoint for Swagger UI authorization",
        "description": (
            "OAuth2-compatible token endpoint that accepts form data (username/password) "
            "and returns an access token. This endpoint is used by Swagger UI for "
            "authorization. The 'username' parameter is treated as email."
        ),
    }
    
    password_reset_request: ClassVar[dict] = {
        "summary": "Purpose of this API is to request password reset for a user",
        "description": (
            "Requests a password reset for a user by email address. If the email exists and the user is active, "
            "a password reset token is generated and sent via email. The token expires in 1 hour. "
            "Rate limiting: Maximum 3 requests per hour per email address. "
            "For security, this endpoint always returns success to prevent email enumeration attacks. "
            "Only active users (not pending or soft-deleted) can request password reset. "
            "Any existing reset token is invalidated when a new request is made."
        ),
    }
    
    password_reset_confirm: ClassVar[dict] = {
        "summary": "Purpose of this API is to confirm password reset with token and new password",
        "description": (
            "Confirms password reset using the token received via email and sets a new password. "
            "The reset token must be valid and not expired (expires after 1 hour). "
            "The new password must meet password policy requirements (minimum 12 characters, "
            "at least one uppercase, lowercase, number, and special character). "
            "The password must not match any of the last 5 passwords. "
            "After successful reset, the token is invalidated and cannot be reused."
        ),
    }