"""Role exceptions."""
from uuid import UUID
from src.exceptions import NotFoundError, ValidationError, BadRequestError


class RoleNotFound(NotFoundError):
    """Role not found."""
    
    def __init__(self, role_id: str):
        super().__init__(
            resource="Role",
            resource_id=role_id,
        )


class InvalidRoleId(ValidationError):
    """Invalid role ID."""
    
    def __init__(self, role_id: str):
        super().__init__(
            message="One or more role IDs are invalid.",
            error_code="VALIDATION_ERROR",
            details=[{"field": "role_ids", "issue": f"Invalid role ID: {role_id}"}],
        )


class MultipleRolesNotAllowed(ValidationError):
    """Multiple roles not allowed - users have exactly one role at a time."""
    
    def __init__(self):
        super().__init__(
            message="Users have exactly one role at a time. The role_ids array must contain exactly one role ID.",
            error_code="VALIDATION_ERROR",
            details=[{"field": "role_ids", "issue": "Users have exactly one role at a time. Must contain exactly one role ID."}],
        )
