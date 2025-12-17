"""Document Assignment API documentation."""
from typing import ClassVar


class DocumentAssignmentApiDocs:
    """API documentation for Document Assignment endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to list document assignments with pagination",
        "description": (
            "Retrieves a paginated list of assignments for a document. Returns normalized assignments "
            "(one per user with effective access_type - editor overrides viewer). Only document Owner "
            "(user where current_user.id == document.owner_id) or FamilyAdmin (role 'familyadmin') can "
            "view assignments. Supports filtering by access_type and sorting by assigned_at, updated_at, "
            "or access_type."
        ),
    }
    
    create: ClassVar[dict] = {
        "summary": "Purpose of this API is to create document assignments",
        "description": (
            "Creates one or more assignments for a document (bulk assignment). Supports array input for "
            "multiple users. If assignment already exists, updates to new access_type. Editor assignment "
            "overrides existing viewer assignment. Self-assignment is blocked. Only document Owner "
            "(user where current_user.id == document.owner_id) or FamilyAdmin (role 'familyadmin') can "
            "create assignments. Triggers notifications for assigned users."
        ),
    }
    
    update: ClassVar[dict] = {
        "summary": "Purpose of this API is to update a document assignment",
        "description": (
            "Updates a specific assignment by user ID (changes access_type). Updating viewer to editor "
            "upgrades the assignment. Updating editor to viewer retains editor (no change). "
            "Self-assignment update is blocked. Only document Owner (user where current_user.id == "
            "document.owner_id) or FamilyAdmin (role 'familyadmin') can update assignments. Supports "
            "optional If-Match header for concurrency control. Triggers notification for affected user."
        ),
    }
    
    delete: ClassVar[dict] = {
        "summary": "Purpose of this API is to remove a document assignment",
        "description": (
            "Removes a specific assignment by user ID. Access is immediately revoked. Only document Owner "
            "(user where current_user.id == document.owner_id) or FamilyAdmin (role 'familyadmin') can "
            "remove assignments. Supports optional If-Match header for concurrency control. Triggers "
            "notification for affected user."
        ),
    }

