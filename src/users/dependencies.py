"""User dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.auth.utils import decode_token
from src.auth.exceptions import InvalidToken
from src.exceptions import ForbiddenError
from src.users.models import User
from src.families.dependencies import get_current_admin_or_member


async def get_current_admin(
    family_id: UUID,
    token: Optional[str],
    session: AsyncSession,
) -> tuple[User, str, bool]:
    """Get current user and verify they are SuperAdmin or FamilyAdmin (not Member).
    
    Returns:
        tuple: (user, role, is_superadmin)
    """
    if not token:
        raise InvalidToken()
    
    # Decode token to get role and family_id
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    role = payload.get("role", "").lower()
    token_family_id = payload.get("family_id")
    
    # SuperAdmin can access any family
    if role == "superadmin" and token_family_id is None:
        user = await get_current_user(token=token, session=session)
        return (user, role, True)
    
    # FamilyAdmin can access their own family
    if role == "familyadmin" and token_family_id and str(family_id) == str(token_family_id):
        user = await get_current_user(token=token, session=session)
        return (user, role, False)
    
    # Member cannot access (403)
    raise ForbiddenError(
        message="Insufficient permissions. SuperAdmin or FamilyAdmin access required.",
        error_code="INSUFFICIENT_PERMISSIONS",
        details=[{"field": "role", "issue": "SuperAdmin or FamilyAdmin access required"}],
    )


# API Dependency Pattern (RULE 8.6.7)
class UserApiDep:
    """API dependency for user endpoints."""
    
    def __init__(self, session: AsyncSession):
        from src.users.service import UserService
        self.service = UserService(session)
        self.session = session
    
    async def list_users(self, family_id: UUID, query):
        """List users within a family."""
        return await self.service.list_users(family_id, query)
    
    async def get_user_by_id(
        self,
        family_id: UUID,
        user_id: UUID,
        current_user_role: str,
        current_user_is_superadmin: bool,
        if_none_match: Optional[str] = None,
    ):
        """Get user by ID with ETag support."""
        # Service returns ServiceResponse - pass through to router
        return await self.service.get_user_by_id(
            family_id, user_id, current_user_role, current_user_is_superadmin,
            if_none_match=if_none_match
        )
    
    async def soft_delete_user(
        self,
        family_id: UUID,
        user_id: UUID,
        current_user_id: UUID,
        current_user_role: str,
        current_user_is_superadmin: bool,
        if_match: Optional[str] = None,
    ):
        """Soft delete user with ETag validation."""
        return await self.service.soft_delete_user(
            family_id, user_id, current_user_id,
            current_user_role, current_user_is_superadmin,
            if_match=if_match
        )
    
    async def create_invitation(
        self,
        family_id: Optional[UUID],
        data,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
    ):
        """Create user invitation."""
        return await self.service.create_invitation(
            family_id, data, current_user_id, current_user_is_superadmin
        )
    
    async def validate_invitation(
        self,
        token: str,
    ):
        """Validate invitation token."""
        return await self.service.validate_invitation(token)
    
    async def activate_account(
        self,
        token: str,
        data,
    ):
        """Activate user account."""
        return await self.service.activate_account(token, data)
    
    async def get_current_user_profile(
        self,
        user_id: UUID,
        if_none_match: Optional[str] = None,
    ):
        """Get current user profile with ETag support."""
        return await self.service.get_current_user_profile(user_id, if_none_match=if_none_match)
    
    async def update_current_user_profile(
        self,
        user_id: UUID,
        data,
        if_match: Optional[str] = None,
    ):
        """Update current user profile with ETag validation."""
        return await self.service.update_current_user_profile(user_id, data, if_match=if_match)
    
    async def change_password(
        self,
        user_id: UUID,
        data,
    ):
        """Change current user password."""
        return await self.service.change_password(user_id, data)
    
    async def resend_invitation(
        self,
        user_id: UUID,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
        current_user_family_id: Optional[UUID],
    ):
        """Resend invitation for a user."""
        return await self.service.resend_invitation(
            user_id, current_user_id, current_user_is_superadmin, current_user_family_id
        )


def get_user_api(session: AsyncSession = Depends(get_session)) -> UserApiDep:
    """Dependency function to get UserApiDep instance."""
    return UserApiDep(session)
