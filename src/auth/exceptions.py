"""Authentication exceptions."""
from src.exceptions import UnauthenticatedError


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
