"""User API documentation."""
from typing import ClassVar


class UserApiDocs:
    """API documentation for User endpoints."""
    
    list: ClassVar[dict] = {
        "summary": "List users within a family with pagination, filtering, and sorting",
        "description": (
            "Retrieves a paginated list of users within a family. SuperAdmin can list users in any family. "
            "FamilyAdmin can only list users in their own family (family_id from token must match). "
            "Member role cannot list users. Supports filtering by status (Active, PendingActivation, SoftDeleted), "
            "sorting by name, email, status, or created_at, and pagination. Soft-deleted users are included "
            "based on the status filter. If family is SoftDeleted, returns 404 (not accessible)."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Get user details within a family",
        "description": (
            "Retrieves details of a specific user within a family. SuperAdmin can access users in any family. "
            "FamilyAdmin can only access users in their own family (family_id from token must match). "
            "Member role cannot access user details. If user is SoftDeleted, returns 404 (not accessible). "
            "If family is SoftDeleted, returns 404 (not accessible). Includes role information and "
            "allowed_role_management flag indicating if current user can manage roles."
        ),
    }
    
    soft_delete: ClassVar[dict] = {
        "summary": "Soft delete user with cascade to documents (SuperAdmin or FamilyAdmin)",
        "description": (
            "Soft deletes a user, which cascades to all user-owned documents and User_Role mappings. "
            "SuperAdmin can soft-delete users in any family. FamilyAdmin can soft-delete users in their own "
            "family (family_id from token must match), but cannot soft-delete themselves. Soft-delete cascades to: "
            "all user-owned documents (soft-deleted), all User_Role mappings (removed), and invite tokens "
            "invalidated (if PendingActivation). Cannot soft-delete if user is already SoftDeleted. "
            "Cannot soft-delete if family is SoftDeleted. Operation is irreversible (no restore). "
            "Requires If-Match header for ETag validation."
        ),
    }
    
    create_invitation: ClassVar[dict] = {
        "summary": "Create user invitation and send invitation email",
        "description": (
            "Creates a new user invitation and sends invitation email. SuperAdmin can invite users to any family. "
            "FamilyAdmin can only invite users to their own family (family_id from token must match). "
            "User is created with status = PendingActivation. Invitation token is generated (unique, secure random string). "
            "invite_expire_at is set to 24 hours after invite_sent_at. Email must be unique system-wide (case-insensitive). "
            "Cannot invite if family is SoftDeleted. If user already exists with same email, returns 409 Conflict. "
            "Invitation email is sent via SMTP (handled by email service)."
        ),
    }
    
    validate_invitation: ClassVar[dict] = {
        "summary": "Validate invitation token and determine if account setup can proceed",
        "description": (
            "Validates invitation token and determines if account setup can proceed. This is a public endpoint "
            "(no authentication required). Token is valid if: user exists with matching invite_token, user status "
            "is PendingActivation, invite_expire_at > NOW, user is not soft-deleted, and family is not soft-deleted. "
            "Returns redirect_target to guide UI: 'account_setup' if valid, 'invite_expired' if invalid/expired. "
            "Must not expose existence of accounts via error messages (generic error for invalid tokens)."
        ),
    }
    
    activate_invitation: ClassVar[dict] = {
        "summary": "Activate user account by setting name and password",
        "description": (
            "Activates user account by setting name and password. This is a public endpoint (no authentication required, "
            "uses invitation token). Token must be valid and not expired (same validation as GET /v1/invitations/validate). "
            "User must have status = PendingActivation (if already Active, returns error). Password must meet strong password "
            "policy: minimum 12 characters, at least one uppercase letter, lowercase letter, number, and special character. "
            "Password reuse check does NOT apply to initial activation (new users have no password history). "
            "On success: sets user.name, user.hash_password, user.status = Active, user.activated_at = NOW, "
            "clears invite_token and invite_expire_at, and generates and returns JWT token (user is automatically authenticated). "
            "Token is single-use (cannot be used again after activation)."
        ),
    }
    
    get_profile: ClassVar[dict] = {
        "summary": "Get user profile by user ID",
        "description": (
            "Retrieves user profile information by user_id. Users can access their own profile (user_id matches JWT sub). "
            "SuperAdmin can access any user's profile. FamilyAdmin can access users in their own family only. "
            "Member can only access their own profile. Returns user details including email, name, status, family information, "
            "password rules, and audit fields. Email is immutable and read-only. If user is SoftDeleted mid-session, returns 401 and forces logout. "
            "If family is SoftDeleted mid-session, returns 401 and forces logout. can_edit_profile = true only if user.status = Active. "
            "Password rules are returned for UI display (for change password modal). Supports ETag for conditional requests."
        ),
    }
    
    update_profile: ClassVar[dict] = {
        "summary": "Update current authenticated user's profile (name and/or password)",
        "description": (
            "Updates current authenticated user's profile. All authenticated users can update their own profile. "
            "SuperAdmin can update any user's profile. FamilyAdmin can update users in their own family only. "
            "Email cannot be updated (immutable field). Both name and password can be updated. "
            "When updating password, current_password is required. Password must meet strong password policy: "
            "minimum 12 characters, at least one uppercase letter, lowercase letter, number, and special character. "
            "Cannot match any of the last 5 passwords. User must have status = Active "
            "(cannot update if PendingActivation or SoftDeleted). If user is SoftDeleted mid-session, returns 401 and forces logout. "
            "If family is SoftDeleted mid-session, returns 401 and forces logout. Requires If-Match header for ETag validation "
            "to prevent concurrent modification conflicts."
        ),
    }