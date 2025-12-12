"""Family dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.auth.utils import decode_token
from src.auth.exceptions import InvalidToken
from src.exceptions import ForbiddenError
from src.users.models import User


async def get_current_superadmin(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current user and verify they are SuperAdmin."""
    if not token:
        raise InvalidToken()
    
    # Decode token to get role and family_id
    payload = decode_token(token)
    if not payload:
        raise InvalidToken()
    
    role = payload.get("role", "").lower()
    family_id = payload.get("family_id")
    
    # SuperAdmin has role="superadmin" and family_id=null
    if role != "superadmin" or family_id is not None:
        raise ForbiddenError(
            message="Insufficient permissions. SuperAdmin access required.",
            error_code="INSUFFICIENT_PERMISSIONS",
            details=[{"field": "role", "issue": "SuperAdmin access required"}],
        )
    
    # Get user from database
    user = await get_current_user(token=token, session=session)
    return user


async def get_current_admin_or_member(
    family_id: UUID,
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current user and verify they can access the family (SuperAdmin or member of family)."""
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
        return user
    
    # FamilyAdmin/Member can only access their own family
    if token_family_id and str(family_id) == str(token_family_id):
        user = await get_current_user(token=token, session=session)
        return user
    
    # Not authorized
    raise ForbiddenError(
        message="Insufficient permissions. You cannot access this family.",
        error_code="INSUFFICIENT_PERMISSIONS",
        details=[{"field": "family_id", "issue": "You cannot access this family"}],
    )


# API Dependency Pattern (RULE 8.6.7)
class FamilyApiDep:
    """API dependency for family endpoints."""
    
    def __init__(self, session: AsyncSession):
        from src.families.service import FamilyService
        self.service = FamilyService(session)
        self.session = session
    
    async def list_families(self, query):
        """List families with pagination."""
        return await self.service.list_families(query)
    
    async def create_family(self, data, current_user_id: UUID):
        """Create a new family."""
        return await self.service.create_family(data, current_user_id)
    
    async def get_family_by_id(self, family_id: UUID, if_none_match: Optional[str] = None):
        """Get family by ID with ETag support."""
        # Service returns ServiceResponse - pass through to router
        return await self.service.get_family_by_id(family_id, if_none_match=if_none_match)
    
    async def update_family(self, family_id: UUID, data, current_user_id: UUID, if_match: Optional[str] = None):
        """Update family with ETag validation."""
        return await self.service.update_family(family_id, data, current_user_id, if_match=if_match)
    
    async def soft_delete_family(self, family_id: UUID, current_user_id: UUID, if_match: Optional[str] = None):
        """Soft delete family with ETag validation."""
        return await self.service.soft_delete_family(family_id, current_user_id, if_match=if_match)


def get_family_api(session: AsyncSession = Depends(get_session)) -> FamilyApiDep:
    """Dependency function to get FamilyApiDep instance."""
    return FamilyApiDep(session)


async def verify_family_access(
    family_id: UUID,
    token: Optional[str],
    session: AsyncSession,
) -> User:
    """Verify user can access the family."""
    return await get_current_admin_or_member(family_id, token=token, session=session)
