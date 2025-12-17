"""User service."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.repository import UserRepository
from src.utils import generate_etag, format_last_modified
from src.exceptions import PreconditionRequiredError, PreconditionFailedError
from src.response import ServiceResponse
from src.users.schemas import (
    UserListQuery,
    UserListRead,
    UserDetailRead,
    UserPaginatedResponse,
    RoleSummary,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationValidationResponse,
    InvitationActivateRequest,
    InvitationActivateResponse,
    InvitationResendResponse,
    PasswordRules,
    UserActivationInfo,
    UserProfileRead,
    UserProfileUpdate,
    UserMeRead,
)
from src.users.exceptions import (
    UserNotFound,
    UserSoftDeleted,
    UserAlreadySoftDeleted,
    CannotDeleteSelf,
    FamilySoftDeletedForUsers,
    DuplicateEmail,
    InvalidInvitationToken,
    TokenExpired,
    UserAlreadyActivated,
    PasswordValidationFailed,
    PasswordReuseViolation,
    IncorrectPassword,
)
from src.users.constants import (
    USER_STATUS_API_ACTIVE,
    USER_STATUS_API_PENDING_ACTIVATION,
    USER_STATUS_API_SOFT_DELETED,
    FAMILY_STATUS_API_ACTIVE,
    FAMILY_STATUS_API_SOFT_DELETED,
)
from src.pagination import calculate_total_pages
from src.users.models import User
from src.roles.models import UserRole, Role
from src.families.models import Family
from src.auth.utils import get_password_hash, verify_password, create_access_token
from src.roles.repository import RoleRepository
from src.roles.models import UserRole
import secrets
import re
from datetime import timedelta


class UserService:
    """Service for user business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)
        self.session = session
    
    def _map_user_status_to_api(self, user: User) -> str:
        """Map database user status to API status format."""
        if user.is_del:
            return USER_STATUS_API_SOFT_DELETED
        if user.status == "pending":
            return USER_STATUS_API_PENDING_ACTIVATION
        if user.status == "active":
            return USER_STATUS_API_ACTIVE
        return USER_STATUS_API_SOFT_DELETED
    
    def _map_family_status_to_api(self, family: Optional[Family]) -> str:
        """Map database family status to API status format."""
        if not family:
            return FAMILY_STATUS_API_ACTIVE  # Default if no family
        if family.is_del:
            return FAMILY_STATUS_API_SOFT_DELETED
        return FAMILY_STATUS_API_ACTIVE
    
    def _calculate_activation_state_label(
        self, user: User, role_info: Optional[tuple]
    ) -> tuple[str, bool]:
        """Calculate activation_state_label and is_activation_expired."""
        status_api = self._map_user_status_to_api(user)
        
        if status_api == USER_STATUS_API_PENDING_ACTIVATION:
            # Check if invite expired
            is_expired = False
            if user.invite_expire_at:
                is_expired = user.invite_expire_at < datetime.now(timezone.utc)
            
            if is_expired:
                return "Invite Expired", True
            else:
                return "Pending Activation", False
        elif status_api == USER_STATUS_API_ACTIVE:
            return "Active", False
        else:
            return "Soft Deleted", False
    
    def _user_to_list_schema(
        self,
        user: User,
        user_role: Optional[UserRole],
        role: Optional[Role],
        family: Optional[Family],
    ) -> UserListRead:
        """Convert User model to UserListRead schema."""
        status_api = self._map_user_status_to_api(user)
        family_status = self._map_family_status_to_api(family)
        activation_label, is_expired = self._calculate_activation_state_label(user, (user_role, role, family))
        
        # Get roles_summary (single role per user)
        roles_summary = []
        if role:
            roles_summary = [role.name]
        
        return UserListRead(
            id=user.id,
            name=user.email,  # TODO: User model needs name field - using email as fallback
            email=user.email,
            status=status_api,
            invite_sent_at=user.invite_sent_at,
            invite_expire_at=user.invite_expire_at,
            activated_at=user.activated_at,
            is_del=user.is_del,
            roles_summary=roles_summary,
            activation_state_label=activation_label,
            is_activation_expired=is_expired,
            family_status=family_status,
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )
    
    def _user_to_detail_schema(
        self,
        user: User,
        user_role: Optional[UserRole],
        role: Optional[Role],
        family: Optional[Family],
        family_id: UUID,
        current_user_role: str,
        current_user_is_superadmin: bool,
    ) -> UserDetailRead:
        """Convert User model to UserDetailRead schema."""
        status_api = self._map_user_status_to_api(user)
        
        # Get roles_list (single role per user)
        roles_list = []
        if role:
            roles_list = [RoleSummary(id=role.id, name=role.name)]
        
        # Calculate allowed_role_management
        # True if (current user is SuperAdmin OR FamilyAdmin) AND target user is not SoftDeleted
        allowed_role_management = (
            (current_user_is_superadmin or current_user_role == "familyadmin")
            and not user.is_del
        )
        
        result = UserDetailRead(
            id=user.id,
            name=user.email,  # TODO: User model needs name field - using email as fallback
            email=user.email,
            family_id=family_id,  # Always use the family_id from path parameter
            status=status_api,
            activated_at=user.activated_at,
            invite_sent_at=user.invite_sent_at,
            invite_expire_at=user.invite_expire_at,
            invited_by=user.invited_by,
            is_del=user.is_del,
            roles_list=roles_list,
            allowed_role_management=allowed_role_management,
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )
        # Attach ETag and Last-Modified for router to set headers
        result._etag = generate_etag(user.updated_at)
        result._last_modified = format_last_modified(user.updated_at)
        return result
    
    async def list_users(
        self,
        family_id: UUID,
        query: UserListQuery,
    ) -> UserPaginatedResponse:
        """List users within a family with pagination, filtering, and sorting."""
        # Verify family exists and is not soft-deleted
        family = await self.repository.get_family_by_id(family_id)
        if not family or family.is_del:
            raise FamilySoftDeletedForUsers()
        
        # Get users with role information
        rows, total = await self.repository.list_by_family_with_pagination(
            family_id=family_id,
            page=query.page,
            page_size=query.page_size,
            status_filter=query.status,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Convert to response schemas
        user_reads = []
        for row in rows:
            user, user_role, role, family_from_row = row
            user_read = self._user_to_list_schema(user, user_role, role, family_from_row or family)
            user_reads.append(user_read)
        
        # Calculate pagination metadata
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build next_page and prev_page URLs
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/families/{family_id}/users?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                next_page += f"&status={query.status}"
        
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/families/{family_id}/users?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                prev_page += f"&status={query.status}"
        
        return UserPaginatedResponse(
            items=user_reads,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
    
    async def list_all_users(
        self,
        query: UserListQuery,
    ) -> UserPaginatedResponse:
        """List all users with pagination, filtering, and sorting."""
        # Get users with role information
        rows, total = await self.repository.list_all_with_pagination(
            page=query.page,
            page_size=query.page_size,
            status_filter=query.status,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        
        # Convert to response schemas
        user_reads = []
        for row in rows:
            user, user_role, role, family = row
            user_read = self._user_to_list_schema(user, user_role, role, family)
            user_reads.append(user_read)
        
        # Calculate pagination metadata
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build next_page and prev_page URLs
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/users?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                next_page += f"&status={query.status}"
        
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/users?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
            if query.status:
                prev_page += f"&status={query.status}"
        
        return UserPaginatedResponse(
            items=user_reads,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
    
    async def get_user_by_id(
        self,
        family_id: UUID,
        user_id: UUID,
        current_user_role: str,
        current_user_is_superadmin: bool,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[UserDetailRead]:
        """Get user details within a family with ETag support (business logic in service)."""
        # Verify family exists and is not soft-deleted
        family = await self.repository.get_family_by_id(family_id)
        if not family or family.is_del:
            raise FamilySoftDeletedForUsers()
        
        # Get user
        user = await self.repository.get_by_id_and_family(user_id, family_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # If soft-deleted, return 404 (not accessible)
        if user.is_del:
            raise UserNotFound(str(user_id))
        
        # Verify user belongs to this family (has role assignment to this family)
        role_info = await self.repository.get_user_role_info(user_id)
        if not role_info:
            raise UserNotFound(str(user_id))
        
        user_role, role, family_from_role = role_info
        
        # Verify user's family matches requested family_id
        if user_role.family_id != family_id:
            raise UserNotFound(str(user_id))
        
        # Generate ETag (business logic in service)
        etag = generate_etag(user.updated_at)
        last_modified = format_last_modified(user.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Return resource with ETag attached for router to set headers
        user_read = self._user_to_detail_schema(
            user, user_role, role, family_from_role or family, family_id,
            current_user_role, current_user_is_superadmin
        )
        return ServiceResponse(
            data=user_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": user_read._etag,
                "Last-Modified": user_read._last_modified,
            },
            response_type="standard",  # Router uses this to return StandardResponse
        )
    
    async def soft_delete_user(
        self,
        family_id: UUID,
        user_id: UUID,
        current_user_id: UUID,
        current_user_role: str,
        current_user_is_superadmin: bool,
        if_match: Optional[str] = None,
    ) -> UserDetailRead:
        """Soft delete user with cascade to documents and ETag validation (business logic in service)."""
        # Verify family exists and is not soft-deleted
        family = await self.repository.get_family_by_id(family_id)
        if not family or family.is_del:
            raise FamilySoftDeletedForUsers()
        
        # Get current user for ETag validation
        current_user = await self.repository.get_by_id_and_family(user_id, family_id)
        if not current_user:
            raise UserNotFound(str(user_id))
        
        # Cannot soft-delete if already soft-deleted
        if current_user.is_del:
            raise UserAlreadySoftDeleted()
        
        # ETag validation (business logic in service)
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for delete operations.",
                details=[{"field": "If-Match", "issue": "If-Match header is required"}],
            )
        
        current_etag = generate_etag(current_user.updated_at)
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. The resource was modified by another user.",
                details=[{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}],
            )
        
        # FamilyAdmin cannot soft-delete themselves
        if not current_user_is_superadmin and user_id == current_user_id:
            raise CannotDeleteSelf()
        
        # Verify user belongs to this family
        role_info = await self.repository.get_user_role_info(user_id)
        if not role_info:
            raise UserNotFound(str(user_id))
        
        user_role, role, family_from_role = role_info
        
        if user_role.family_id != family_id:
            raise UserNotFound(str(user_id))
        
        # Soft delete user
        current_user.is_del = True
        current_user.status = "inactive"  # Database uses lowercase
        current_user.deleted_at = datetime.now(timezone.utc)
        current_user.deleted_by = current_user_id
        current_user.updated_by = current_user_id
        # updated_at is set automatically by onupdate=func.now()
        
        # TODO: Cascade soft-delete to documents and User_Role mappings
        # This will be handled by the document feature (F-003)
        # For User_Role: Mark as deleted (is_del = True, deleted_at = now)
        user_role.is_del = True
        user_role.deleted_at = datetime.now(timezone.utc)
        user_role.deleted_by = current_user_id
        
        user = await self.repository.soft_delete(current_user)
        
        return self._user_to_detail_schema(
            user, user_role, role, family_from_role or family, family_id,
            current_user_role, current_user_is_superadmin
        )
    
    # ==================== Invitation Service Methods ====================
    
    def _generate_invite_token(self) -> str:
        """Generate secure random invitation token."""
        return secrets.token_urlsafe(32)
    
    def _validate_password(self, password: str, check_history: bool = False, user: Optional[User] = None) -> list[dict]:
        """Validate password against strong password policy.
        
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        # Minimum length
        if len(password) < 12:
            errors.append({"field": "password", "issue": "Password must be at least 12 characters long."})
        
        # Uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append({"field": "password", "issue": "Password must contain at least one uppercase letter."})
        
        # Lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append({"field": "password", "issue": "Password must contain at least one lowercase letter."})
        
        # Number
        if not re.search(r'\d', password):
            errors.append({"field": "password", "issue": "Password must contain at least one number."})
        
        # Special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append({"field": "password", "issue": "Password must contain at least one special character."})
        
        # Password history check (only for password changes, not initial activation)
        if check_history and user:
            # TODO: Implement password history check (last 5 passwords)
            # For now, skip this check - will be implemented when password history model is added
            pass
        
        return errors
    
    def _get_password_rules(self, disallow_last_5: bool = False) -> PasswordRules:
        """Get password rules for UI display."""
        return PasswordRules(
            min_length=12,
            uppercase=True,
            lowercase=True,
            number=True,
            special=True,
            disallow_last_5=disallow_last_5,
        )
    
    async def create_invitation(
        self,
        family_id: Optional[UUID],
        data: InvitationCreate,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
    ) -> InvitationCreateResponse:
        """Create user invitation and send invitation email (business logic in service)."""
        # For now, family_id is required (current data model requires UserRole with family_id)
        # TODO: Support SuperAdmin user creation without family_id if data model is updated
        if family_id is None:
            from src.exceptions import ValidationError
            raise ValidationError(
                message="family_id is required. SuperAdmin user creation without family_id is not yet supported.",
                error_code="VALIDATION_ERROR",
                details=[{"field": "family_id", "issue": "family_id is required"}],
            )
        
        # Verify family exists and is not soft-deleted
        family = await self.repository.get_family_by_id(family_id)
        if not family:
            from src.families.exceptions import FamilyNotFound
            raise FamilyNotFound(str(family_id))
        
        if family.is_del:
            from src.users.exceptions import FamilySoftDeletedForUsers
            raise FamilySoftDeletedForUsers()
        
        # Check if user with email already exists (case-insensitive)
        existing_user = await self.repository.get_by_email(data.email)
        if existing_user:
            raise DuplicateEmail(data.email)
        
        # Generate invitation token
        invite_token = self._generate_invite_token()
        now = datetime.now(timezone.utc)
        invite_expire_at = now + timedelta(hours=24)
        
        # Create user with PendingActivation status
        # Note: hash_password is NOT NULL, so we use a placeholder hash that will be replaced during activation
        # TODO: Make hash_password nullable in User model or use proper placeholder
        placeholder_hash = get_password_hash(secrets.token_urlsafe(32))  # Temporary hash
        new_user = User(
            email=data.email,
            hash_password=placeholder_hash,  # Placeholder until activation
            status="pending",  # Database uses lowercase
            invite_token=invite_token,
            invite_sent_at=now,
            invite_expire_at=invite_expire_at,
            invited_by=current_user_id,
            created_by=current_user_id,
            is_del=False,
        )
        
        user = await self.repository.create(new_user)
        
        # Determine role_id: use provided role_id or default to "member"
        role_id_to_use: UUID
        if data.role_id:
            # Validate that the provided role exists
            provided_role = await self.role_repository.get_by_id(data.role_id)
            if not provided_role:
                from src.exceptions import ValidationError
                raise ValidationError(
                    message=f"Role with ID {data.role_id} not found",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "role_id", "issue": f"Role ID {data.role_id} does not exist"}],
                )
            
            # Validate business rules for role assignment
            role_name = provided_role.name.lower()
            
            # SuperAdmin cannot be assigned to a family (must have family_id = NULL)
            # Since current implementation requires family_id, SuperAdmin creation is not supported
            if role_name == "superadmin":
                from src.exceptions import ValidationError
                raise ValidationError(
                    message="SuperAdmin role cannot be assigned to a family. SuperAdmin user creation without family_id is not yet supported.",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "role_id", "issue": "SuperAdmin role requires family_id to be null, which is not yet supported"}],
                )
            
            # FamilyAdmin and Member are valid for family assignments
            if role_name not in ["familyadmin", "member"]:
                from src.exceptions import ValidationError
                raise ValidationError(
                    message=f"Invalid role '{role_name}' for family assignment. Only 'familyadmin' and 'member' roles are allowed.",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "role_id", "issue": f"Role '{role_name}' is not valid for family assignments"}],
                )
            
            role_id_to_use = data.role_id
        else:
            # Default to "member" role if role_id not provided
            member_role = await self.role_repository.get_by_name("member")
            if not member_role:
                raise ValueError("Default 'member' role not found in database")
            role_id_to_use = member_role.id
        
        # Create UserRole with determined role_id
        user_role = UserRole(
            user_id=user.id,
            family_id=family_id,
            role_id=role_id_to_use,
            created_by=current_user_id,
            is_del=False,
        )
        await self.role_repository.create_user_role(user_role)
        
        # Send invitation email via Celery task
        from src.celery_worker import send_invitation_email_task
        send_invitation_email_task.delay(
            user_email=user.email,
            invitation_token=user.invite_token,
            family_name=family.name,
        )
        
        return InvitationCreateResponse(
            id=user.id,
            email=user.email,
            family_id=family_id,
            status="PendingActivation",
            invite_token=user.invite_token,
            invite_sent_at=user.invite_sent_at,
            invite_expire_at=user.invite_expire_at,
            invited_by=user.invited_by,
            created_at=user.created_at,
        )
    
    async def resend_invitation(
        self,
        user_id: UUID,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
        current_user_family_id: Optional[UUID],
    ) -> InvitationResendResponse:
        """Resend invitation email to a user with PendingActivation status (business logic in service)."""
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # User must have status = PendingActivation
        if user.status != "pending":
            from src.exceptions import ValidationError
            raise ValidationError(
                message="User status is not PendingActivation (cannot resend invitation).",
                error_code="BUSINESS_RULE_FAILED",
                details=[{"field": "status", "issue": "User status is not PendingActivation"}],
            )
        
        # Get user's family information for authorization check
        role_info = await self.repository.get_user_role_info(user_id)
        if not role_info:
            raise UserNotFound(str(user_id))
        
        user_role, role, family = role_info
        user_family_id = user_role.family_id if user_role else None
        
        # Authorization check: SuperAdmin can resend for any user, FamilyAdmin only for users in their own family
        if not current_user_is_superadmin:
            if not current_user_family_id or str(user_family_id) != str(current_user_family_id):
                from src.exceptions import ForbiddenError
                raise ForbiddenError(
                    message="Insufficient permissions. FamilyAdmin can only resend invitations for users in their own family.",
                    error_code="INSUFFICIENT_PERMISSIONS",
                    details=[{"field": "user_id", "issue": "You cannot resend invitation for this user"}],
                )
        
        # Check if family is soft-deleted
        if family and family.is_del:
            from src.users.exceptions import FamilySoftDeletedForUsers
            raise FamilySoftDeletedForUsers()
        
        # Generate new invitation token
        invite_token = self._generate_invite_token()
        now = datetime.now(timezone.utc)
        invite_expire_at = now + timedelta(hours=24)
        
        # Update user invitation fields
        user.invite_token = invite_token
        user.invite_sent_at = now
        user.invite_expire_at = invite_expire_at
        user.updated_at = now
        user.updated_by = current_user_id
        
        await self.session.commit()
        await self.session.refresh(user)
        
        # Send invitation email via Celery task
        from src.celery_worker import send_invitation_email_task
        family_name = family.name if family else None
        send_invitation_email_task.delay(
            user_email=user.email,
            invitation_token=user.invite_token,
            family_name=family_name,
        )
        
        return InvitationResendResponse(
            user_id=user.id,
            email=user.email,
            invite_token=user.invite_token,
            invite_sent_at=user.invite_sent_at,
            invite_expire_at=user.invite_expire_at,
        )
    
    async def validate_invitation(
        self,
        token: str,
    ) -> InvitationValidationResponse:
        """Validate invitation token and determine if account setup can proceed (business logic in service)."""
        # Get user by invitation token
        user = await self.repository.get_by_invite_token(token)
        
        if not user:
            # Token not found - return invalid response
            return InvitationValidationResponse(
                is_token_valid=False,
                is_token_expired=False,
                redirect_target="invite_expired",
                expired_reason="invalid",
            )
        
        # Check if user is soft-deleted
        if user.is_del:
            return InvitationValidationResponse(
                is_token_valid=False,
                is_token_expired=False,
                redirect_target="invite_expired",
                expired_reason="user_soft_deleted",
            )
        
        # Check if user status is PendingActivation
        if user.status != "pending":
            return InvitationValidationResponse(
                is_token_valid=False,
                is_token_expired=False,
                redirect_target="invite_expired",
                expired_reason="invalid",
            )
        
        # Check if family is soft-deleted
        # Get user's family through UserRole
        role_info = await self.repository.get_user_role_info(user.id)
        if role_info:
            user_role, role, family = role_info
            if family and family.is_del:
                return InvitationValidationResponse(
                    is_token_valid=False,
                    is_token_expired=False,
                    redirect_target="invite_expired",
                    expired_reason="family_soft_deleted",
                )
        
        # Check if token has expired
        now = datetime.now(timezone.utc)
        is_expired = user.invite_expire_at and user.invite_expire_at <= now
        
        if is_expired:
            return InvitationValidationResponse(
                is_token_valid=False,
                is_token_expired=True,
                redirect_target="invite_expired",
                expired_reason="expired",
            )
        
        # Token is valid
        family_id = None
        if role_info:
            user_role, role, family = role_info
            if user_role:
                family_id = user_role.family_id
        
        return InvitationValidationResponse(
            is_token_valid=True,
            is_token_expired=False,
            redirect_target="account_setup",
            user_id=user.id,
            email=user.email,
            family_id=family_id,
            status="PendingActivation",
            invite_expire_at=user.invite_expire_at,
            password_rules=self._get_password_rules(disallow_last_5=False),
        )
    
    async def activate_account(
        self,
        token: str,
        data: InvitationActivateRequest,
    ) -> InvitationActivateResponse:
        """Activate user account by setting name and password (business logic in service)."""
        # Validate invitation token (same validation as validate_invitation)
        user = await self.repository.get_by_invite_token(token)
        
        if not user:
            raise InvalidInvitationToken()
        
        if user.is_del:
            from src.users.exceptions import UserSoftDeleted
            raise UserSoftDeleted()
        
        if user.status != "pending":
            if user.status == "active":
                raise UserAlreadyActivated()
            raise InvalidInvitationToken()
        
        # Check if token has expired
        now = datetime.now(timezone.utc)
        if user.invite_expire_at and user.invite_expire_at <= now:
            raise TokenExpired()
        
        # Check if family is soft-deleted
        role_info = await self.repository.get_user_role_info(user.id)
        if role_info:
            user_role, role, family = role_info
            if family and family.is_del:
                from src.users.exceptions import FamilySoftDeletedForUsers
                raise FamilySoftDeletedForUsers()
        
        # Validate password (no history check for new users)
        password_errors = self._validate_password(data.password, check_history=False)
        if password_errors:
            raise PasswordValidationFailed(password_errors)
        
        # Get user's family and role for response
        family_id = None
        family_name = None
        user_role_name = "member"  # Default role
        
        if role_info:
            user_role, role, family = role_info
            if user_role:
                family_id = user_role.family_id
            if family:
                family_name = family.name
            if role:
                user_role_name = role.name
        
        # Update user: set password, status, activated_at, clear invite fields
        # Note: User model needs name field - storing name will be handled when model is updated
        # TODO: Add name field to User model and set it here: user.name = data.name
        user.hash_password = get_password_hash(data.password)
        user.status = "active"
        user.activated_at = now
        user.invite_token = None
        user.invite_expire_at = None
        user.updated_at = now
        # updated_by is set automatically
        
        await self.session.commit()
        await self.session.refresh(user)
        
        # Generate JWT token (user is automatically authenticated)
        token = create_access_token(
            user_id=str(user.id),
            role=user_role_name,
            family_id=str(family_id) if family_id else None,
        )
        
        return InvitationActivateResponse(
            token=token,
            expires_in=3600,  # 1 hour
            user=UserActivationInfo(
                id=user.id,
                email=user.email,
                name=data.name,  # Use provided name
                role=user_role_name,
                family_id=family_id,
                family_name=family_name or "",
            ),
            password_rules=self._get_password_rules(disallow_last_5=False),
        )
    
    # ==================== Profile Management Service Methods ====================
    
    async def get_current_user_profile(
        self,
        user_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[UserProfileRead]:
        """Get current authenticated user's profile with ETag support (business logic in service)."""
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # If soft-deleted, return 401 (force logout)
        if user.is_del:
            from src.users.exceptions import UserSoftDeleted
            raise UserSoftDeleted()
        
        # Get user's role and family information
        role_info = await self.repository.get_user_role_info(user_id)
        family_id = None
        family_name = None
        
        if role_info:
            user_role, role, family = role_info
            if user_role:
                family_id = user_role.family_id
            if family:
                # Check if family is soft-deleted (force logout)
                if family.is_del:
                    from src.users.exceptions import FamilySoftDeletedForUsers
                    raise FamilySoftDeletedForUsers()
                family_name = family.name
        
        # Generate ETag (business logic in service)
        etag = generate_etag(user.updated_at)
        last_modified = format_last_modified(user.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Map status to API format
        status_api = self._map_user_status_to_api(user)
        
        # can_edit_profile = true only if user.status = Active
        can_edit_profile = status_api == USER_STATUS_API_ACTIVE
        
        # Build profile response
        # Note: User model needs name field - using email as fallback for now
        # TODO: Add name field to User model
        profile_read = UserProfileRead(
            id=user.id,
            email=user.email,
            name=user.email,  # TODO: Use user.name when field is added
            status=status_api,
            family_id=family_id,
            family_name=family_name,
            can_edit_profile=can_edit_profile,
            password_rules=self._get_password_rules(disallow_last_5=True),  # For password changes
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )
        
        # Attach ETag for router to set headers
        profile_read._etag = etag
        profile_read._last_modified = last_modified
        
        return ServiceResponse(
            data=profile_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
            response_type="standard",  # Router uses this to return StandardResponse
        )
    
    async def get_current_user_me(
        self,
        user_id: UUID,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[UserMeRead]:
        """Get current authenticated user's details with full family and role objects (business logic in service)."""
        # Log the user_id being requested
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"get_current_user_me: Service called with user_id={user_id}")
        
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            error_msg = f"get_current_user_me: User not found with user_id={user_id}"
            logger.error(error_msg)
            raise UserNotFound(str(user_id))
        
        logger.info(f"get_current_user_me: Found user - id={user.id}, email={user.email}")
        
        # If soft-deleted, return 401 (force logout)
        if user.is_del:
            from src.users.exceptions import UserSoftDeleted
            raise UserSoftDeleted()
        
        # Get user's role and family information
        role_info = await self.repository.get_user_role_info(user_id)
        family_obj = None
        role_obj = None
        
        if role_info:
            user_role, role, family = role_info
            if family:
                # Check if family is soft-deleted (force logout)
                if family.is_del:
                    from src.users.exceptions import FamilySoftDeletedForUsers
                    raise FamilySoftDeletedForUsers()
                
                # Map family to FamilyRead schema
                from src.families.schemas import FamilyRead
                # Map family status to API format
                family_status_api = FAMILY_STATUS_API_SOFT_DELETED if family.is_del else FAMILY_STATUS_API_ACTIVE
                family_obj = FamilyRead(
                    id=family.id,
                    name=family.name,
                    status=family_status_api,
                    is_del=family.is_del,
                    created_at=family.created_at,
                    created_by=family.created_by,
                    updated_at=family.updated_at,
                    updated_by=family.updated_by,
                    deleted_at=family.deleted_at,
                    deleted_by=family.deleted_by,
                )
            
            if role:
                # Map role to RoleRead schema
                from src.roles.schemas import RoleRead
                role_obj = RoleRead(
                    id=role.id,
                    name=role.name,
                    permissions=role.permissions,
                )
        
        # Generate ETag (business logic in service)
        etag = generate_etag(user.updated_at)
        last_modified = format_last_modified(user.updated_at)
        
        # Check If-None-Match (business logic validation in service)
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified (business logic decision in service)
            return ServiceResponse(
                data=None,  # 304 has no body
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={
                    "ETag": etag,
                    "Last-Modified": last_modified,
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                response_type="fastapi",  # Router uses this to return FastAPI Response
            )
        
        # Map status to API format
        status_api = self._map_user_status_to_api(user)
        
        # Build UserMeRead response with full objects
        user_me_read = UserMeRead(
            id=user.id,
            email=user.email,
            name=user.email,  # TODO: Use user.name when field is added
            status=status_api,
            family=family_obj,
            role=role_obj,
            activated_at=user.activated_at,
            invite_sent_at=user.invite_sent_at,
            invite_expire_at=user.invite_expire_at,
            invited_by=user.invited_by,
            is_del=user.is_del,
            password_rules=self._get_password_rules(disallow_last_5=True),
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )
        
        # Attach ETag for router to set headers
        user_me_read._etag = etag
        user_me_read._last_modified = last_modified
        
        return ServiceResponse(
            data=user_me_read,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
            response_type="standard",  # Router uses this to return StandardResponse
        )
    
    async def update_current_user_profile(
        self,
        user_id: UUID,
        data: UserProfileUpdate,
        if_match: Optional[str] = None,
    ) -> UserProfileRead:
        """Update current authenticated user's profile (name and/or password) with ETag validation (business logic in service)."""
        # Get user
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # If soft-deleted, return 401 (force logout)
        if user.is_del:
            from src.users.exceptions import UserSoftDeleted
            raise UserSoftDeleted()
        
        # Get user's role and family information
        role_info = await self.repository.get_user_role_info(user_id)
        family_id = None
        family_name = None
        
        if role_info:
            user_role, role, family = role_info
            if user_role:
                family_id = user_role.family_id
            if family:
                # Check if family is soft-deleted (force logout)
                if family.is_del:
                    from src.users.exceptions import FamilySoftDeletedForUsers
                    raise FamilySoftDeletedForUsers()
                family_name = family.name
        
        # ETag validation (business logic in service) - REQUIRED per spec
        if not if_match:
            raise PreconditionRequiredError(
                message="If-Match header required for update operations.",
                details=[{"field": "If-Match", "issue": "If-Match header is required"}],
            )
        
        current_etag = generate_etag(user.updated_at)
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. The resource was modified by another user.",
                details=[{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}],
            )
        
        # User must have status = Active (cannot update if PendingActivation or SoftDeleted)
        status_api = self._map_user_status_to_api(user)
        if status_api != USER_STATUS_API_ACTIVE:
            from src.exceptions import ValidationError
            raise ValidationError(
                message="User status is not Active (cannot edit).",
                error_code="BUSINESS_RULE_FAILED",
                details=[{"field": "status", "issue": "User status is not Active (cannot edit)"}],
            )
        
        # Validate that at least one field is being updated
        if data.name is None and data.password is None:
            from src.exceptions import ValidationError
            raise ValidationError(
                message="At least one field (name or password) must be provided for update.",
                error_code="VALIDATION_ERROR",
                details=[{"field": "name/password", "issue": "At least one field must be provided"}],
            )
        
        # Handle password update
        if data.password is not None:
            # Current password is required when updating password
            if not data.current_password:
                from src.exceptions import ValidationError
                raise ValidationError(
                    message="current_password is required when updating password.",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "current_password", "issue": "current_password is required when updating password"}],
                )
            
            # Verify current password
            if not verify_password(data.current_password, user.hash_password):
                raise IncorrectPassword()
            
            # Validate new password (with history check)
            password_errors = self._validate_password(data.password, check_history=True, user=user)
            if password_errors:
                raise PasswordValidationFailed(password_errors)
            
            # Update password
            user.hash_password = get_password_hash(data.password)
        
        # Update user name if provided
        # Note: User model needs name field - for now we'll store it when model is updated
        # TODO: Add name field to User model and set it here: user.name = data.name
        if data.name is not None:
            # Name update logic here (when User model has name field)
            pass
        
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = user_id
        
        await self.session.commit()
        await self.session.refresh(user)
        
        # Map status to API format
        status_api = self._map_user_status_to_api(user)
        can_edit_profile = status_api == USER_STATUS_API_ACTIVE
        
        # Build profile response
        # Use updated name from request if provided, otherwise use existing (email as fallback for now)
        display_name = data.name if data.name is not None else user.email  # TODO: Use user.name when field is added
        profile_read = UserProfileRead(
            id=user.id,
            email=user.email,
            name=display_name,
            status=status_api,
            family_id=family_id,
            family_name=family_name,
            can_edit_profile=can_edit_profile,
            password_rules=self._get_password_rules(disallow_last_5=True),
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )
        
        # Attach ETag for router
        profile_read._etag = generate_etag(user.updated_at)
        profile_read._last_modified = format_last_modified(user.updated_at)
        
        return profile_read
