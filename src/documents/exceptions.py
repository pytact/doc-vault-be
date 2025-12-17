"""Document exceptions."""
from uuid import UUID
from fastapi import status
from src.exceptions import (
    NotFoundError,
    ForbiddenError,
    ValidationError,
    BadRequestError,
    ConflictError,
    AppException,
)
from src.documents.constants import (
    ERROR_DOCUMENT_NOT_FOUND,
    ERROR_INSUFFICIENT_PERMISSIONS,
    ERROR_FILE_TOO_LARGE,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
    ERROR_DOCUMENT_ALREADY_HAS_FILE,
    ERROR_CATEGORY_SUBCATEGORY_MISMATCH,
    ERROR_DOCUMENT_ALREADY_EXISTS,
    ERROR_FILE_NOT_UPLOADED,
    ERROR_ETAG_MISMATCH,
    ERROR_ETAG_REQUIRED,
    ERROR_CODE_DOCUMENT_NOT_FOUND,
    ERROR_CODE_INSUFFICIENT_PERMISSIONS,
    ERROR_CODE_FILE_TOO_LARGE,
    ERROR_CODE_UNSUPPORTED_MEDIA_TYPE,
    ERROR_CODE_DOCUMENT_ALREADY_HAS_FILE,
    ERROR_CODE_VALIDATION_ERROR,
    ERROR_CODE_CATEGORY_SUBCATEGORY_MISMATCH,
    ERROR_CODE_DOCUMENT_ALREADY_EXISTS,
    ERROR_CODE_FILE_NOT_UPLOADED,
    ERROR_CODE_ETAG_MISMATCH,
    ERROR_CODE_ETAG_REQUIRED,
)


class DocumentNotFound(NotFoundError):
    """Document not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            resource="Document",
            resource_id=document_id,
        )


class DocumentPermissionDenied(ForbiddenError):
    """Insufficient permissions to access document."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_INSUFFICIENT_PERMISSIONS,
            error_code=ERROR_CODE_INSUFFICIENT_PERMISSIONS,
            details=[{"field": "document", "issue": ERROR_INSUFFICIENT_PERMISSIONS}],
        )


class FileTooLarge(AppException):
    """File exceeds maximum size (413 Payload Too Large)."""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            message=ERROR_FILE_TOO_LARGE,
            error_code=ERROR_CODE_FILE_TOO_LARGE,
            details=[
                {
                    "field": "file",
                    "issue": f"File size {file_size} bytes exceeds maximum size of {max_size} bytes",
                }
            ],
        )


class UnsupportedMediaType(AppException):
    """File format is not supported (415 Unsupported Media Type)."""
    
    def __init__(self, mime_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            message=ERROR_UNSUPPORTED_MEDIA_TYPE,
            error_code=ERROR_CODE_UNSUPPORTED_MEDIA_TYPE,
            details=[
                {
                    "field": "file",
                    "issue": f"File format {mime_type} is not supported. Only PDF (application/pdf) is allowed.",
                }
            ],
        )


class DocumentAlreadyHasFile(ConflictError):
    """Document already has a file uploaded."""
    
    def __init__(self):
        super().__init__(
            message=ERROR_DOCUMENT_ALREADY_HAS_FILE,
            error_code=ERROR_CODE_DOCUMENT_ALREADY_HAS_FILE,
            details=[{"field": "document", "issue": ERROR_DOCUMENT_ALREADY_HAS_FILE}],
        )


class CategorySubcategoryMismatch(ValidationError):
    """Subcategory does not belong to the selected category."""
    
    def __init__(self):
        super().__init__(
            message="Category-subcategory pairing validation failed.",
            error_code=ERROR_CODE_CATEGORY_SUBCATEGORY_MISMATCH,
            details=[
                {
                    "field": "subcategory_id",
                    "issue": ERROR_CATEGORY_SUBCATEGORY_MISMATCH,
                }
            ],
        )


class DocumentAlreadyExists(ConflictError):
    """Document already exists for user in this category and subcategory."""
    
    def __init__(self, category_id: UUID, subcategory_id: UUID):
        super().__init__(
            message=ERROR_DOCUMENT_ALREADY_EXISTS,
            error_code=ERROR_CODE_DOCUMENT_ALREADY_EXISTS,
            details=[
                {
                    "field": "category_id",
                    "issue": f"A document already exists for this user in category {category_id} and subcategory {subcategory_id}. You can update the existing document instead of creating a new one.",
                }
            ],
        )


class FileNotUploaded(NotFoundError):
    """Document file has not been uploaded."""
    
    def __init__(self, document_id: str):
        super().__init__(
            resource="Document file",
            resource_id=document_id,
        )


class ETagMismatch(ValidationError):
    """ETag mismatch - resource has been modified."""
    
    def __init__(self):
        super().__init__(
            message="Resource version mismatch. The resource was modified by another user.",
            error_code=ERROR_CODE_ETAG_MISMATCH,
            details=[{"field": "etag", "issue": ERROR_ETAG_MISMATCH}],
        )


class ETagRequired(BadRequestError):
    """If-Match header is required for this operation."""
    
    def __init__(self):
        super().__init__(
            message="If-Match header is required for this operation.",
            error_code=ERROR_CODE_ETAG_REQUIRED,
            details=[{"field": "If-Match", "issue": ERROR_ETAG_REQUIRED}],
        )


# ==================== Document Assignment Exceptions ====================

class AssignmentNotFound(NotFoundError):
    """Assignment not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="Assignment",
            resource_id=user_id,
        )


class SelfAssignmentBlocked(ConflictError):
    """Cannot assign access to document owner."""
    
    def __init__(self):
        from src.documents.constants import (
            ERROR_SELF_ASSIGNMENT_BLOCKED,
            ERROR_CODE_SELF_ASSIGNMENT_BLOCKED,
        )
        super().__init__(
            message=ERROR_SELF_ASSIGNMENT_BLOCKED,
            error_code=ERROR_CODE_SELF_ASSIGNMENT_BLOCKED,
            details=[{"field": "user_id", "issue": "Cannot assign access to document owner. Owners already have full access."}],
        )


class UserNotInFamily(ConflictError):
    """User is not in the same Family as the document."""
    
    def __init__(self, user_id: str):
        from src.documents.constants import (
            ERROR_USER_NOT_IN_FAMILY,
            ERROR_CODE_USER_NOT_IN_FAMILY,
        )
        super().__init__(
            message=ERROR_USER_NOT_IN_FAMILY,
            error_code=ERROR_CODE_USER_NOT_IN_FAMILY,
            details=[{"field": "user_id", "issue": f"User {user_id} is not in the same Family as the document."}],
        )


class AssignmentPermissionDenied(ForbiddenError):
    """Insufficient permissions to manage document assignments."""
    
    def __init__(self):
        from src.documents.constants import (
            ERROR_ASSIGNMENT_PERMISSION_DENIED,
            ERROR_CODE_ASSIGNMENT_PERMISSION_DENIED,
        )
        super().__init__(
            message=ERROR_ASSIGNMENT_PERMISSION_DENIED,
            error_code=ERROR_CODE_ASSIGNMENT_PERMISSION_DENIED,
            details=[{"field": "user", "issue": "Only document Owner (user where current_user.id == document.owner_id) or FamilyAdmin (role 'familyadmin') can manage assignments."}],
        )
