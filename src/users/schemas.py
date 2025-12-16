"""User schemas."""
from uuid import UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.schemas import PagedCollection

if TYPE_CHECKING:
    from src.families.schemas import FamilyRead
    from src.roles.schemas import RoleRead


class UserListQuery(BaseModel):
    """Query schema for listing users with pagination and filtering."""
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    status: Optional[str] = Field(None, description="Filter by status: Active, PendingActivation, SoftDeleted")
    sort_by: str = Field("created_at", description="Sort field: name, email, status, created_at")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


class RoleSummary(BaseModel):
    """Role summary for user list response."""
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class UserListRead(BaseModel):
    """User list item response schema."""
    id: UUID
    name: str  # Note: User model doesn't have name field - using email as fallback
    email: str
    status: str  # "Active", "PendingActivation", or "SoftDeleted" (API format)
    invite_sent_at: Optional[datetime] = None
    invite_expire_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    is_del: bool
    roles_summary: list[str]  # List of role names (single role per user)
    activation_state_label: str  # Derived label from status + invite_expire_at
    is_activation_expired: bool  # True if invite expired (for PendingActivation only)
    family_status: str  # Family status (Active, SoftDeleted)
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserDetailRead(BaseModel):
    """User detail response schema."""
    id: UUID
    name: str  # Note: User model doesn't have name field - using email as fallback
    email: str
    family_id: UUID  # Required - always present since we're getting user within a family
    status: str  # "Active", "PendingActivation", or "SoftDeleted" (API format)
    activated_at: Optional[datetime] = None
    invite_sent_at: Optional[datetime] = None
    invite_expire_at: Optional[datetime] = None
    invited_by: Optional[UUID] = None
    is_del: bool
    roles_list: list[RoleSummary]  # List of roles with id and name (single role per user)
    allowed_role_management: bool  # True if current user can manage roles
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserPaginatedResponse(PagedCollection[UserListRead]):
    """Paginated user response schema."""
    next_page: Optional[str] = None
    prev_page: Optional[str] = None


# ==================== Invitation Schemas ====================

class InvitationCreate(BaseModel):
    """Request schema for creating user invitation."""
    email: str = Field(..., description="User email address", max_length=254)
    family_id: Optional[UUID] = Field(None, description="Family ID (null for SuperAdmin creation)")
    role_id: Optional[UUID] = Field(None, description="Role ID")
    
    model_config = ConfigDict(from_attributes=True)


class InvitationCreateResponse(BaseModel):
    """Response schema for invitation creation."""
    id: UUID
    email: str
    family_id: UUID
    status: str  # "PendingActivation"
    invite_token: str
    invite_sent_at: datetime
    invite_expire_at: datetime
    invited_by: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvitationResendRequest(BaseModel):
    """Request schema for resending invitation."""
    user_id: UUID = Field(..., description="User ID to resend invitation for")
    
    model_config = ConfigDict(from_attributes=True)


class InvitationResendResponse(BaseModel):
    """Response schema for resending invitation."""
    user_id: UUID
    email: str
    invite_token: str
    invite_sent_at: datetime
    invite_expire_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PasswordRules(BaseModel):
    """Password rules for account setup."""
    min_length: int
    uppercase: bool
    lowercase: bool
    number: bool
    special: bool
    disallow_last_5: bool
    
    model_config = ConfigDict(from_attributes=True)


class InvitationValidationResponse(BaseModel):
    """Response schema for invitation validation."""
    is_token_valid: bool
    is_token_expired: bool
    redirect_target: str  # "account_setup" or "invite_expired"
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    family_id: Optional[UUID] = None
    status: Optional[str] = None
    invite_expire_at: Optional[datetime] = None
    password_rules: Optional[PasswordRules] = None
    expired_reason: Optional[str] = None  # "expired", "invalid", "family_soft_deleted", "user_soft_deleted"
    
    model_config = ConfigDict(from_attributes=True)


class InvitationActivateRequest(BaseModel):
    """Request schema for activating account."""
    name: str = Field(..., description="User name", min_length=1, max_length=255)
    password: str = Field(..., description="User password", min_length=12)
    
    model_config = ConfigDict(from_attributes=True)


class UserActivationInfo(BaseModel):
    """User information in activation response."""
    id: UUID
    email: str
    name: str
    role: str
    family_id: UUID  # Note: Can be null for SuperAdmin, but activation always creates family-scoped user
    family_name: str
    
    model_config = ConfigDict(from_attributes=True)


class InvitationActivateResponse(BaseModel):
    """Response schema for account activation."""
    token: str
    expires_in: int  # Token expiration time in seconds (3600 = 1 hour)
    user: UserActivationInfo
    password_rules: PasswordRules
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Profile Management Schemas ====================

class UserMeRead(BaseModel):
    """Response schema for current user's details with full related objects."""
    id: UUID
    email: str
    name: str
    status: str  # "Active", "PendingActivation", or "SoftDeleted"
    family: Optional["FamilyRead"] = None  # Full family object
    role: Optional["RoleRead"] = None  # Full role object
    activated_at: Optional[datetime] = None
    invite_sent_at: Optional[datetime] = None
    invite_expire_at: Optional[datetime] = None
    invited_by: Optional[UUID] = None
    is_del: bool
    password_rules: "PasswordRules"
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileRead(BaseModel):
    """Response schema for current user profile."""
    id: UUID
    email: str
    name: str
    status: str  # "Active", "PendingActivation", or "SoftDeleted"
    family_id: Optional[UUID] = None
    family_name: Optional[str] = None
    can_edit_profile: bool
    password_rules: PasswordRules
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Request schema for updating user profile."""
    name: Optional[str] = Field(None, description="User name", min_length=1, max_length=255)
    password: Optional[str] = Field(None, description="New password", min_length=12)
    current_password: Optional[str] = Field(None, description="Current password (required when updating password)", min_length=1)
    
    model_config = ConfigDict(from_attributes=True)


# Resolve forward references after all schemas are defined
def _resolve_forward_refs():
    """Resolve forward references for UserMeRead."""
    from src.families.schemas import FamilyRead
    from src.roles.schemas import RoleRead
    
    UserMeRead.model_rebuild()


# Call at module level to resolve forward references
_resolve_forward_refs()
