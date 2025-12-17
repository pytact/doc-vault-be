"""Notification API documentation."""
from typing import ClassVar


class NotificationApiDocs:
    """API documentation for Notification endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to retrieve paginated list of expiry notifications for the current authenticated user",
        "description": (
            "Retrieves a paginated list of expiry notifications for the current authenticated user. "
            "Only Owner and FamilyAdmin roles can access notifications. Owner sees notifications for "
            "documents they own. FamilyAdmin sees notifications for all documents within their family. "
            "Supports pagination (page, page_size) and sorting by created_at (asc/desc). Notification "
            "text (document_title, category, subcategory) is resolved dynamically from current Document "
            "metadata. Soft-deleted documents and families are excluded. Returns notifications sorted "
            "by createdAt DESC by default. Supports cache validation via If-None-Match header."
        ),
    }
    
    mark_read: ClassVar[dict] = {
        "summary": "Purpose of this API is to update read status of a single notification (mark as read or unread) for the current authenticated user",
        "description": (
            "Updates the read status of a single notification for the current authenticated user. Accepts "
            "a request body with 'is_read' boolean field: set to true to mark as read, false to mark as unread. "
            "Only Owner and FamilyAdmin roles can update notification status. User must own the notification to "
            "update it. Marking an already-read notification as read (or unread as unread) is idempotent (no error). "
            "Requires If-Match header for ETag validation to prevent concurrent modifications. Returns "
            "notification ID, read_at timestamp (null if unread), and is_read status. Returns 404 if notification "
            "not found or user doesn't own the notification."
        ),
    }
    
    mark_all_read: ClassVar[dict] = {
        "summary": "Purpose of this API is to update read status for all notifications (mark all as read or unread) for the current authenticated user",
        "description": (
            "Updates the read status for all notifications for the current authenticated user. Accepts "
            "a request body with 'is_read' boolean field: set to true to mark all unread notifications as read, "
            "false to mark all read notifications as unread. Only Owner and FamilyAdmin roles can update "
            "notification status. Marking already-read notifications as read (or unread as unread) is idempotent "
            "(no error). Returns count of notifications whose status was updated. This operation is efficient "
            "and processes all notifications in a single transaction."
        ),
    }
    
    upcoming_expiries: ClassVar[dict] = {
        "summary": "Purpose of this API is to retrieve list of documents expiring within the next 30 days for dashboard widget display",
        "description": (
            "Retrieves list of documents expiring within the next 30 days for dashboard widget display. "
            "Only Owner and FamilyAdmin roles can access upcoming expiries. Owner sees only documents "
            "where document.owner_id = current_user.id. FamilyAdmin sees all documents where "
            "document.family_id = current_user.family_id. Documents without expiry_date are excluded. "
            "Soft-deleted documents and families are excluded. Response includes days_until_expiry "
            "calculated as expiry_date - current_date. Document metadata (title, category, subcategory) "
            "is resolved dynamically from current Document metadata."
        ),
    }

