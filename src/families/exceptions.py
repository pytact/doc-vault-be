"""Family exceptions."""
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError, ValidationError


class FamilyNotFound(NotFoundError):
    """Family not found."""
    
    def __init__(self, family_id: str):
        super().__init__(
            resource="Family",
            resource_id=family_id,
        )


class DuplicateFamilyName(ConflictError):
    """Family name already exists."""
    
    def __init__(self, name: str):
        super().__init__(
            message="Family name must be unique.",
            error_code="DUPLICATE_FAMILY_NAME",
            details=[{"field": "name", "issue": "A family with this name already exists."}],
        )


class FamilySoftDeleted(ValidationError):
    """Family is soft-deleted and cannot be accessed."""
    
    def __init__(self):
        super().__init__(
            message="Family is soft-deleted and cannot be accessed.",
            error_code="BUSINESS_RULE_FAILED",
            details=[{"field": "family", "issue": "Family is soft-deleted"}],
        )


class FamilyAlreadySoftDeleted(ValidationError):
    """Family is already soft-deleted."""
    
    def __init__(self):
        super().__init__(
            message="Family is already soft-deleted.",
            error_code="BUSINESS_RULE_FAILED",
            details=[{"field": "family", "issue": "Family is already soft-deleted"}],
        )


class CannotUpdateSoftDeletedFamily(ValidationError):
    """Cannot update soft-deleted family."""
    
    def __init__(self):
        super().__init__(
            message="Cannot update family. Family is soft-deleted.",
            error_code="BUSINESS_RULE_FAILED",
            details=[{"field": "family", "issue": "Family is soft-deleted"}],
        )
