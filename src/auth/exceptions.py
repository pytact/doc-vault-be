"""Authentication exceptions."""
from src.exceptions import UnauthenticatedError, ValidationError


class InvalidCredentials(UnauthenticatedError):
    """Invalid email or password."""
    
    def __init__(self):
        super().__init__(
            message="Authentication failed. Please check your credentials.",
            error_code="UNAUTHENTICATED",
            details=[{"field": "credentials", "issue": "Invalid email or password"}],
        )


class UserNotActivated(UnauthenticatedError):
    """User account not activated."""
    
    def __init__(self):
        super().__init__(
            message="Account not activated. Please check your invitation email.",
            error_code="USER_NOT_ACTIVATED",
            details=[{"field": "status", "issue": "User account is pending activation"}],
        )


class UserSoftDeleted(UnauthenticatedError):
    """User account soft-deleted."""
    
    def __init__(self):
        super().__init__(
            message="Authentication failed. Please check your credentials.",
            error_code="USER_SOFT_DELETED",
            details=[{"field": "credentials", "issue": "Invalid email or password"}],
        )


class FamilySoftDeleted(UnauthenticatedError):
    """User's family soft-deleted."""
    
    def __init__(self):
        super().__init__(
            message="Authentication failed. Please check your credentials.",
            error_code="FAMILY_SOFT_DELETED",
            details=[{"field": "credentials", "issue": "Invalid email or password"}],
        )


class TokenExpired(UnauthenticatedError):
    """JWT token expired."""
    
    def __init__(self):
        super().__init__(
            message="Token has expired. Please login again.",
            error_code="TOKEN_EXPIRED",
            details=[{"field": "token", "issue": "Token has expired"}],
        )


class InvalidToken(UnauthenticatedError):
    """Invalid JWT token."""
    
    def __init__(self):
        super().__init__(
            message="Invalid token. Please login again.",
            error_code="INVALID_TOKEN",
            details=[{"field": "token", "issue": "Invalid token"}],
        )


class ResetTokenInvalid(UnauthenticatedError):
    """Invalid or expired password reset token."""
    
    def __init__(self):
        super().__init__(
            message="Password reset token is invalid or has expired. Please request a new one.",
            error_code="RESET_TOKEN_INVALID",
            details=[{"field": "reset_token", "issue": "Reset token is invalid or expired"}],
        )


class ResetTokenExpired(UnauthenticatedError):
    """Password reset token expired."""
    
    def __init__(self):
        super().__init__(
            message="Password reset token has expired. Please request a new one.",
            error_code="RESET_TOKEN_EXPIRED",
            details=[{"field": "reset_token", "issue": "Reset token has expired"}],
        )


class ResetRequestRateLimited(ValidationError):
    """Too many password reset requests."""
    
    def __init__(self):
        super().__init__(
            message="Too many password reset requests. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            details=[{"field": "email", "issue": "Too many reset requests. Please wait before requesting again."}],
        )
