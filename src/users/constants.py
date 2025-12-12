"""User constants."""

# Error Messages
ERROR_USER_NOT_FOUND = "User not found"
ERROR_USER_ALREADY_SOFT_DELETED = "User is already soft-deleted"
ERROR_USER_SOFT_DELETED = "User is soft-deleted and cannot be accessed"
ERROR_CANNOT_DELETE_SELF = "You cannot soft-delete yourself."
ERROR_FAMILY_SOFT_DELETED = "Family is soft-deleted and cannot be accessed"

# Success Messages
SUCCESS_USER_RETRIEVED = "User retrieved successfully"
SUCCESS_USERS_RETRIEVED = "Users retrieved successfully"
SUCCESS_USER_SOFT_DELETED = "User soft-deleted successfully"

# Error Codes
ERROR_CODE_USER_NOT_FOUND = "USER_NOT_FOUND"
ERROR_CODE_USER_ALREADY_SOFT_DELETED = "BUSINESS_RULE_FAILED"
ERROR_CODE_USER_SOFT_DELETED = "USER_NOT_FOUND"
ERROR_CODE_CANNOT_DELETE_SELF = "INSUFFICIENT_PERMISSIONS"
ERROR_CODE_FAMILY_SOFT_DELETED = "FAMILY_NOT_FOUND"

# Status Values (Database)
USER_STATUS_PENDING = "pending"
USER_STATUS_ACTIVE = "active"
USER_STATUS_INACTIVE = "inactive"

# Status Values (API - mapped from database)
USER_STATUS_API_ACTIVE = "Active"
USER_STATUS_API_PENDING_ACTIVATION = "PendingActivation"
USER_STATUS_API_SOFT_DELETED = "SoftDeleted"

# Family Status Values (API)
FAMILY_STATUS_API_ACTIVE = "Active"
FAMILY_STATUS_API_SOFT_DELETED = "SoftDeleted"

# Sort Fields
SORT_FIELD_NAME = "name"
SORT_FIELD_EMAIL = "email"
SORT_FIELD_STATUS = "status"
SORT_FIELD_CREATED_AT = "created_at"

# Sort Orders
SORT_ORDER_ASC = "asc"
SORT_ORDER_DESC = "desc"
