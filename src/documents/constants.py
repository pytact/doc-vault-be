"""Document constants."""

# Error Messages
ERROR_DOCUMENT_NOT_FOUND = "Document not found"
ERROR_DOCUMENT_ALREADY_SOFT_DELETED = "Document is already soft-deleted"
ERROR_DOCUMENT_SOFT_DELETED = "Document is soft-deleted and cannot be accessed"
ERROR_CANNOT_UPDATE_SOFT_DELETED = "Cannot update document. Document is soft-deleted."
ERROR_CANNOT_DELETE_SOFT_DELETED = "Cannot delete document. Document is already soft-deleted."
ERROR_INSUFFICIENT_PERMISSIONS = "Insufficient permissions to access this document"
ERROR_FILE_TOO_LARGE = "File exceeds maximum size of 5MB"
ERROR_UNSUPPORTED_MEDIA_TYPE = "File must be PDF format (application/pdf)"
ERROR_DOCUMENT_ALREADY_HAS_FILE = "Document already has a file. Use PUT to replace it."
ERROR_CATEGORY_SUBCATEGORY_MISMATCH = "Subcategory does not belong to the selected category"
ERROR_DOCUMENT_ALREADY_EXISTS = "A document already exists for this user in the specified category and subcategory"
ERROR_FILE_NOT_UPLOADED = "Document file has not been uploaded"
ERROR_ETAG_MISMATCH = "Resource has been modified since retrieval. Please fetch the latest version and retry."
ERROR_ETAG_REQUIRED = "If-Match header is required for this operation"

# Success Messages
SUCCESS_DOCUMENT_CREATED = "Document created successfully"
SUCCESS_DOCUMENT_RETRIEVED = "Document retrieved successfully"
SUCCESS_DOCUMENTS_RETRIEVED = "Documents retrieved successfully"
SUCCESS_DOCUMENT_UPDATED = "Document updated successfully"
SUCCESS_DOCUMENT_DELETED = "Document deleted successfully"
SUCCESS_FILE_REPLACED = "File replaced successfully"

# Error Codes
ERROR_CODE_DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
ERROR_CODE_INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
ERROR_CODE_FILE_TOO_LARGE = "FILE_TOO_LARGE"
ERROR_CODE_UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
ERROR_CODE_DOCUMENT_ALREADY_HAS_FILE = "RESOURCE_CONFLICT"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_CODE_CATEGORY_SUBCATEGORY_MISMATCH = "VALIDATION_ERROR"
ERROR_CODE_DOCUMENT_ALREADY_EXISTS = "RESOURCE_CONFLICT"
ERROR_CODE_FILE_NOT_UPLOADED = "DOCUMENT_NOT_FOUND"
ERROR_CODE_ETAG_MISMATCH = "PRECONDITION_FAILED"
ERROR_CODE_ETAG_REQUIRED = "PRECONDITION_REQUIRED"

# File Constraints
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPE = "application/pdf"

# Permission Types
PERMISSION_OWNER = "owner"
PERMISSION_EDITOR = "editor"
PERMISSION_VIEWER = "viewer"

# Sort Fields
SORT_FIELD_CREATED_AT = "created_at"
SORT_FIELD_UPDATED_AT = "updated_at"
SORT_FIELD_TITLE = "title"
SORT_FIELD_EXPIRY_DATE = "expiry_date"

# Sort Orders
SORT_ORDER_ASC = "asc"
SORT_ORDER_DESC = "desc"

# File Access Modes
FILE_MODE_PREVIEW = "preview"
FILE_MODE_DOWNLOAD = "download"

# ==================== Document Assignment Constants ====================

# Error Messages
ERROR_ASSIGNMENT_NOT_FOUND = "Assignment for the specified user not found or has been deleted."
ERROR_SELF_ASSIGNMENT_BLOCKED = "Cannot assign access to document owner. Owners already have full access."
ERROR_USER_NOT_IN_FAMILY = "User is not in the same Family as the document."
ERROR_ASSIGNMENT_PERMISSION_DENIED = "You do not have permission to manage document assignments."
ERROR_CANNOT_ASSIGN_TO_DELETED_DOCUMENT = "Cannot assign access to a soft-deleted document."

# Success Messages
SUCCESS_ASSIGNMENTS_RETRIEVED = "Assignments retrieved successfully"
SUCCESS_ASSIGNMENTS_PROCESSED = "Assignments processed successfully"
SUCCESS_ASSIGNMENT_UPDATED = "Assignment updated successfully"
SUCCESS_ASSIGNMENT_DELETED = "Assignment removed successfully"

# Error Codes
ERROR_CODE_ASSIGNMENT_NOT_FOUND = "ASSIGNMENT_NOT_FOUND"
ERROR_CODE_SELF_ASSIGNMENT_BLOCKED = "SELF_ASSIGNMENT_BLOCKED"
ERROR_CODE_USER_NOT_IN_FAMILY = "USER_NOT_IN_FAMILY"
ERROR_CODE_ASSIGNMENT_PERMISSION_DENIED = "INSUFFICIENT_PERMISSIONS"

# Access Types
ACCESS_TYPE_VIEWER = "viewer"
ACCESS_TYPE_EDITOR = "editor"

# Sort Fields for Assignments
SORT_FIELD_ASSIGNED_AT = "assigned_at"
SORT_FIELD_UPDATED_AT = "updated_at"
SORT_FIELD_ACCESS_TYPE = "access_type"
