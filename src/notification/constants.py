"""Notification constants for expiry reminder system."""

# Error Messages
ERROR_NOTIFICATION_NOT_FOUND = "Notification not found"
ERROR_DOCUMENT_NOT_FOUND = "Document associated with notification not found"
ERROR_FAMILY_DELETED = "Family associated with document has been soft-deleted"
ERROR_DOCUMENT_DELETED = "Document associated with notification has been soft-deleted"
ERROR_INSUFFICIENT_PERMISSIONS = "You do not have permission to access notifications"
ERROR_NOTIFICATION_ACCESS_DENIED = "You do not have permission to mark this notification as read"

# Success Messages
SUCCESS_NOTIFICATIONS_RETRIEVED = "Notifications retrieved successfully"
SUCCESS_NOTIFICATION_MARKED_READ = "Notification marked as read successfully"
SUCCESS_NOTIFICATION_MARKED_UNREAD = "Notification marked as unread successfully"
SUCCESS_ALL_NOTIFICATIONS_MARKED_READ = "All notifications marked as read successfully"
SUCCESS_ALL_NOTIFICATIONS_MARKED_UNREAD = "All notifications marked as unread successfully"
SUCCESS_UPCOMING_EXPIRIES_RETRIEVED = "Upcoming expiries retrieved successfully"

# Error Codes
ERROR_CODE_NOTIFICATION_NOT_FOUND = "NOTIFICATION_NOT_FOUND"
ERROR_CODE_DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
ERROR_CODE_FAMILY_DELETED = "FAMILY_DELETED"
ERROR_CODE_DOCUMENT_DELETED = "DOCUMENT_DELETED"
ERROR_CODE_INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
ERROR_CODE_NOTIFICATION_ACCESS_DENIED = "NOTIFICATION_ACCESS_DENIED"

# Reminder Types
REMINDER_TYPE_30D = "30d"
REMINDER_TYPE_7D = "7d"
REMINDER_TYPE_0D = "0d"

# Reminder Schedule Status
STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_CANCELLED = "cancelled"

# Message Types
MESSAGE_TYPE_EXPIRY_30D = "expiry_30d"
MESSAGE_TYPE_EXPIRY_7D = "expiry_7d"
MESSAGE_TYPE_EXPIRY_0D = "expiry_0d"

# Roles
ROLE_OWNER = "owner"
ROLE_FAMILYADMIN = "familyadmin"

# Upcoming Expiries
UPCOMING_EXPIRIES_DAYS = 30

