"""User exceptions."""
from uuid import UUID
from src.exceptions import NotFoundError, ForbiddenError, ValidationError, UnauthenticatedError


class UserNotFound(NotFoundError):
    """User not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="User",
            resource_id=user_id,
        )


class UserSoftDeleted(UnauthenticatedError):
    """User is soft-deleted and cannot be accessed."""
    
    def __init__(self):
        super().__init__(
            message="User is soft-deleted and cannot be accessed.",
            error_code="USER_SOFT_DELETED",
            details=[{"field": "user", "issue": "User is soft-deleted"}],
        )


class UserAlreadySoftDeleted(ValidationError):
    """User is already soft-deleted."""
    
    def __init__(self):
        super().__init__(
            message="User is already soft-deleted.",
            error_code="BUSINESS_RULE_FAILED",
            details=[{"field": "user", "issue": "User is already soft-deleted"}],
        )


class CannotDeleteSelf(ForbiddenError):
    """Cannot soft-delete yourself."""
    
    def __init__(self):
        super().__init__(
            message="Operation not allowed.",
            error_code="INSUFFICIENT_PERMISSIONS",
            details=[{"field": "user", "issue": "You cannot soft-delete yourself."}],
        )


class FamilySoftDeletedForUsers(UnauthenticatedError):
    """Family is soft-deleted and cannot be accessed."""
    
    def __init__(self):
        super().__init__(
            message="Family is soft-deleted and cannot be accessed.",
            error_code="FAMILY_SOFT_DELETED",
            details=[{"field": "family", "issue": "Family is soft-deleted"}],
        )


# ==================== Invitation Exceptions ====================

from src.exceptions import ConflictError, UnauthenticatedError, BadRequestError


class DuplicateEmail(ConflictError):
    """Email already exists (case-insensitive)."""
    
    def __init__(self, email: str):
        super().__init__(
            message="Email must be unique.",
            error_code="DUPLICATE_EMAIL",
            details=[{"field": "email", "issue": "A user with this email already exists."}],
        )


class InvalidInvitationToken(UnauthenticatedError):
    """Invitation token is invalid, expired, or already used."""
    
    def __init__(self):
        super().__init__(
            message="Invitation token is invalid, expired, or already used.",
            error_code="INVALID_TOKEN",
            details=[{"field": "invite_token", "issue": "Invitation token is invalid, expired, or already used."}],
        )


class TokenExpired(UnauthenticatedError):
    """Invitation token has expired."""
    
    def __init__(self):
        super().__init__(
            message="Invitation token has expired.",
            error_code="TOKEN_EXPIRED",
            details=[{"field": "invite_token", "issue": "Invitation token has expired."}],
        )


class UserAlreadyActivated(UnauthenticatedError):
    """User status is already Active (token already used)."""
    
    def __init__(self):
        super().__init__(
            message="User account is already activated.",
            error_code="USER_ALREADY_ACTIVATED",
            details=[{"field": "invite_token", "issue": "User account is already activated."}],
        )


class PasswordValidationFailed(ValidationError):
    """Password does not meet strong password requirements."""
    
    def __init__(self, details: list[dict]):
        super().__init__(
            message="Password does not meet security requirements.",
            error_code="PASSWORD_VALIDATION_FAILED",
            details=details,
        )


class PasswordReuseViolation(ValidationError):
    """New password matches one of the last 5 passwords."""
    
    def __init__(self):
        super().__init__(
            message="Password reuse is not allowed for security reasons.",
            error_code="PASSWORD_REUSE_VIOLATION",
            details=[{"field": "new_password", "issue": "Password cannot be one of your last 5 passwords."}],
        )


class IncorrectPassword(UnauthenticatedError):
    """Current password is incorrect."""
    
    def __init__(self):
        super().__init__(
            message="Password change failed. Please verify your current password.",
            error_code="INCORRECT_PASSWORD",
            details=[{"field": "current_password", "issue": "Current password is incorrect."}],
        )
