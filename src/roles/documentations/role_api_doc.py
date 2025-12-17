"""Role API documentation."""
from typing import ClassVar


class RoleApiDocs:
    """API documentation for Role endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to list all available predefined roles (global)",
        "description": (
            "Retrieves all available predefined roles (global, not family-scoped). Roles are: superadmin, familyadmin, member. "
            "Roles are predefined and not editable via API. Permissions are JSON objects imported from permission system. "
            "All authenticated users can view available roles. Roles are used for user role assignment within families."
        ),
    }
    
    update_user_roles: ClassVar[dict] = {
        "summary": "Purpose of this API is to update user roles within a family (replace existing roles)",
        "description": (
            "Updates user roles within a family (replaces existing roles). SuperAdmin can update roles for users in any family. "
            "FamilyAdmin can update roles for users in their own family (family_id from token must match). Member role cannot "
            "update user roles. Replaces all existing User_Role mappings for the user in the specified family. Empty role_ids "
            "array removes all roles (allowed). Users have exactly one role at a time (not multiple roles). User must have "
            "status = Active or PendingActivation (cannot update roles if SoftDeleted). Cannot update roles if family is "
            "SoftDeleted. Cannot update roles if user is SoftDeleted. All role IDs must be valid (exist in roles table). "
            "Role assignments are family-scoped (User_Role includes family_id). Requires If-Match header for ETag validation."
        ),
    }

