"""Family constants."""

# Error Messages
ERROR_FAMILY_NOT_FOUND = "Family not found"
ERROR_DUPLICATE_FAMILY_NAME = "A family with this name already exists."
ERROR_FAMILY_ALREADY_SOFT_DELETED = "Family is already soft-deleted"
ERROR_FAMILY_SOFT_DELETED = "Family is soft-deleted and cannot be accessed"
ERROR_CANNOT_UPDATE_SOFT_DELETED = "Cannot update family. Family is soft-deleted."

# Success Messages
SUCCESS_FAMILY_CREATED = "Family created successfully"
SUCCESS_FAMILY_RETRIEVED = "Family retrieved successfully"
SUCCESS_FAMILIES_RETRIEVED = "Families retrieved successfully"
SUCCESS_FAMILY_UPDATED = "Family updated successfully"
SUCCESS_FAMILY_SOFT_DELETED = "Family soft-deleted successfully"

# Error Codes
ERROR_CODE_FAMILY_NOT_FOUND = "FAMILY_NOT_FOUND"
ERROR_CODE_DUPLICATE_FAMILY_NAME = "DUPLICATE_FAMILY_NAME"
ERROR_CODE_FAMILY_ALREADY_SOFT_DELETED = "BUSINESS_RULE_FAILED"
ERROR_CODE_FAMILY_SOFT_DELETED = "FAMILY_NOT_FOUND"
ERROR_CODE_CANNOT_UPDATE_SOFT_DELETED = "BUSINESS_RULE_FAILED"

# Status Values (Database)
FAMILY_STATUS_ACTIVE = "active"
FAMILY_STATUS_INACTIVE = "inactive"

# Status Values (API - mapped from database)
FAMILY_STATUS_API_ACTIVE = "Active"
FAMILY_STATUS_API_SOFT_DELETED = "SoftDeleted"

# Sort Fields
SORT_FIELD_NAME = "name"
SORT_FIELD_CREATED_AT = "created_at"
SORT_FIELD_STATUS = "status"

# Sort Orders
SORT_ORDER_ASC = "asc"
SORT_ORDER_DESC = "desc"
