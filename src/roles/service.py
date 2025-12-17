"""Role service."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from src.roles.repository import RoleRepository
from src.users.repository import UserRepository
from src.families.repository import FamilyRepository
from src.roles.schemas import (
    RoleRead,
    RoleListResponse,
    UserRoleUpdateRequest,
    UserRoleUpdateResponse,
    UserRoleSummary,
)
from src.roles.exceptions import (
    RoleNotFound,
    InvalidRoleId,
    MultipleRolesNotAllowed,
)
from src.roles.models import Role, UserRole
from src.users.models import User
from src.families.models import Family
from src.users.exceptions import UserNotFound, FamilySoftDeletedForUsers
from src.families.exceptions import FamilyNotFound
from src.response import ServiceResponse
from src.utils import generate_etag, format_last_modified


class RoleService:
    """Service for role business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = RoleRepository(session)
        self.user_repository = UserRepository(session)
        self.family_repository = FamilyRepository(session)
        self.session = session
    
    async def list_roles(
        self,
    ) -> RoleListResponse:
        """List all available predefined roles (global)."""
        roles = await self.repository.get_all()
        
        role_reads = [
            RoleRead(
                id=role.id,
                name=role.name,
                permissions=role.permissions,
            )
            for role in roles
        ]
        
        return RoleListResponse(items=role_reads)
    
    async def update_user_roles(
        self,
        family_id: UUID,
        user_id: UUID,
        data: UserRoleUpdateRequest,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
        if_match: Optional[str] = None,
    ) -> ServiceResponse[UserRoleUpdateResponse]:
        """Update user roles within a family (replace existing roles) with ETag validation (business logic in service)."""
        # Verify family exists and is not soft-deleted
        family = await self.family_repository.get_by_id(family_id)
        if not family:
            raise FamilyNotFound(str(family_id))
        
        if family.is_del:
            raise FamilySoftDeletedForUsers()
        
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFound(str(user_id))
        
        # If soft-deleted, return 404
        if user.is_del:
            raise UserNotFound(str(user_id))
        
        # ETag validation (business logic in service) - REQUIRED per spec
        if not if_match:
            from src.exceptions import PreconditionRequiredError
            raise PreconditionRequiredError(
                message="If-Match header required for update operations.",
                details=[{"field": "If-Match", "issue": "If-Match header is required"}],
            )
        
        from src.utils import generate_etag
        from src.exceptions import PreconditionFailedError
        current_etag = generate_etag(user.updated_at)
        if if_match != current_etag:
            raise PreconditionFailedError(
                message="Resource version mismatch. The resource was modified by another user.",
                details=[{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}],
            )
        
        # User must have status = Active or PendingActivation (cannot update roles if SoftDeleted)
        if user.is_del:
            from src.exceptions import ValidationError
            raise ValidationError(
                message="User is SoftDeleted (cannot update roles).",
                error_code="BUSINESS_RULE_FAILED",
                details=[{"field": "user", "issue": "User is SoftDeleted (cannot update roles)"}],
            )
        
        # Validate role_ids: must contain exactly one role ID (single role per user) or empty array (remove all roles)
        if len(data.role_ids) > 1:
            raise MultipleRolesNotAllowed()
        
        # Validate all role IDs exist (if any provided)
        roles = []
        for role_id in data.role_ids:
            role = await self.repository.get_by_id(role_id)
            if not role:
                raise InvalidRoleId(str(role_id))
            roles.append(role)
        
        # Get ALL user roles for this family (including soft-deleted) to handle all cases
        all_existing_roles = await self.repository.get_all_user_roles_by_user_and_family(user_id, family_id)
        
        # Filter to get active roles
        active_roles = [r for r in all_existing_roles if not r.is_del and r.deleted_at is None]
        
        # If no roles provided, soft delete all existing active roles
        if not roles:
            for active_role in active_roles:
                await self.repository.delete_user_role(active_role, current_user_id)
            role_summaries = []
        else:
            # We should only have one role (validated above)
            new_role = roles[0]
            
            if active_roles:
                # Update the first active role
                existing_role = active_roles[0]
                updated_role = await self.repository.update_user_role(
                    existing_role, new_role.id, current_user_id
                )
                
                # Soft delete any additional active roles
                for extra_role in active_roles[1:]:
                    await self.repository.delete_user_role(extra_role, current_user_id)
                
                role_summaries = [
                    UserRoleSummary(
                        id=new_role.id,
                        name=new_role.name,
                    )
                ]
            elif all_existing_roles:
                # We have soft-deleted roles, reactivate and update the first one
                existing_role = all_existing_roles[0]
                updated_role = await self.repository.update_user_role(
                    existing_role, new_role.id, current_user_id
                )
                
                # Soft delete any other roles (active or deleted)
                for extra_role in all_existing_roles[1:]:
                    if not extra_role.is_del:
                        await self.repository.delete_user_role(extra_role, current_user_id)
                
                role_summaries = [
                    UserRoleSummary(
                        id=new_role.id,
                        name=new_role.name,
                    )
                ]
            else:
                # No existing role at all, create new one
                user_role = UserRole(
                    user_id=user_id,
                    family_id=family_id,
                    role_id=new_role.id,
                    created_by=current_user_id,
                    is_del=False,
                )
                await self.repository.create_user_role(user_role)
                role_summaries = [
                    UserRoleSummary(
                        id=new_role.id,
                        name=new_role.name,
                    )
                ]
        
        # After update, fetch the updated user to get new updated_at for ETag
        updated_user = await self.user_repository.get_by_id(user_id)
        if not updated_user:
            raise UserNotFound(str(user_id))
        
        # Generate new ETag from updated user's updated_at (business logic in service)
        new_etag = generate_etag(updated_user.updated_at)
        last_modified = format_last_modified(updated_user.updated_at)
        
        # Build response
        response_data = UserRoleUpdateResponse(
            user_id=user_id,
            family_id=family_id,
            roles=role_summaries,
        )
        
        # Return ServiceResponse with ETag headers (business logic in service)
        return ServiceResponse(
            data=response_data,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": f'"{new_etag}"',
                "Last-Modified": last_modified,
            },
        )
