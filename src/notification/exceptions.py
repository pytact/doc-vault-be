"""Notification exceptions."""
from src.exceptions import NotFoundError, ForbiddenError
from src.notification.constants import (
    ERROR_CODE_NOTIFICATION_NOT_FOUND,
    ERROR_CODE_DOCUMENT_NOT_FOUND,
    ERROR_CODE_FAMILY_DELETED,
    ERROR_CODE_DOCUMENT_DELETED,
    ERROR_CODE_INSUFFICIENT_PERMISSIONS,
    ERROR_CODE_NOTIFICATION_ACCESS_DENIED,
    ERROR_NOTIFICATION_NOT_FOUND,
    ERROR_DOCUMENT_NOT_FOUND,
    ERROR_FAMILY_DELETED,
    ERROR_DOCUMENT_DELETED,
    ERROR_INSUFFICIENT_PERMISSIONS,
    ERROR_NOTIFICATION_ACCESS_DENIED,
)


class NotificationNotFound(NotFoundError):
    """Notification not found exception."""
    
    def __init__(self, notification_id: str):
        super().__init__(
            resource="Notification",
            resource_id=notification_id
        )


class DocumentNotFound(NotFoundError):
    """Document not found exception."""
    
    def __init__(self, document_id: str):
        super().__init__(
            resource="Document",
            resource_id=document_id
        )


class DocumentDeleted(NotFoundError):
    """Document deleted exception (410 Gone)."""
    
    def __init__(self, document_id: str):
        super().__init__(
            status_code=410,
            resource="Document",
            resource_id=document_id,
            message=ERROR_DOCUMENT_DELETED
        )
        self.error_code = ERROR_CODE_DOCUMENT_DELETED


class FamilyDeleted(NotFoundError):
    """Family deleted exception (410 Gone)."""
    
    def __init__(self, family_id: str):
        super().__init__(
            status_code=410,
            resource="Family",
            resource_id=family_id,
            message=ERROR_FAMILY_DELETED
        )
        self.error_code = ERROR_CODE_FAMILY_DELETED


class NotificationPermissionDenied(ForbiddenError):
    """Notification permission denied exception."""
    
    def __init__(self, message: str = ERROR_INSUFFICIENT_PERMISSIONS):
        super().__init__(
            message=message,
            error_code=ERROR_CODE_INSUFFICIENT_PERMISSIONS,
            details=[{"field": "role", "issue": message}]
        )


class NotificationAccessDenied(ForbiddenError):
    """Notification access denied exception (user doesn't own notification)."""
    
    def __init__(self, message: str = ERROR_NOTIFICATION_ACCESS_DENIED):
        super().__init__(
            message=message,
            error_code=ERROR_CODE_NOTIFICATION_ACCESS_DENIED,
            details=[{"field": "notification", "issue": message}]
        )

