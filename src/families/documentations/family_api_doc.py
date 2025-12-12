"""Family API documentation."""
from typing import ClassVar


class FamilyApiDocs:
    """API documentation for Family endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "List all families with pagination, filtering, and sorting (SuperAdmin only)",
        "description": (
            "Retrieves a paginated list of all families. Only SuperAdmin can access this endpoint. "
            "Supports filtering by status (Active, SoftDeleted), sorting by name, created_at, or status, "
            "and pagination. Soft-deleted families are included based on the status filter."
        ),
    }
    
    create: ClassVar[dict] = {
        "summary": "Create a new family (SuperAdmin only)",
        "description": (
            "Creates a new family with the specified name. Only SuperAdmin can create families. "
            "Family name must be unique system-wide (case-insensitive). Family is created with "
            "status=Active. Returns the created family with all audit fields."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Get family details",
        "description": (
            "Retrieves details of a specific family. SuperAdmin can access any family. "
            "FamilyAdmin and Member can only access their own family (family_id from token must match). "
            "If family is SoftDeleted, returns 404 (not accessible)."
        ),
    }
    
    update: ClassVar[dict] = {
        "summary": "Update family name (SuperAdmin only)",
        "description": (
            "Updates the name of a family. Only SuperAdmin can update families. "
            "Family name must be unique system-wide (case-insensitive). "
            "Cannot update if family is SoftDeleted. Requires If-Match header for ETag validation."
        ),
    }
    
    soft_delete: ClassVar[dict] = {
        "summary": "Soft delete family with cascade to users and documents (SuperAdmin only)",
        "description": (
            "Soft deletes a family, which cascades to all users in the family and all documents. "
            "Only SuperAdmin can soft-delete families. Soft-delete cascades to: all users in the family "
            "(set status=SoftDeleted), all User_Role mappings (removed), all documents in the family "
            "(soft-deleted), and all pending invitations (invalidated). Cannot soft-delete if already "
            "SoftDeleted. Operation is irreversible (no restore). Requires If-Match header for ETag validation."
        ),
    }
