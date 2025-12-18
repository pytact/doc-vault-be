"""Role dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.auth.dependencies import get_current_user, oauth2_scheme
from src.auth.utils import decode_token
from src.auth.exceptions import InvalidToken
from src.exceptions import ForbiddenError
from src.roles.service import RoleService
from src.users.models import User
from src.users.dependencies import get_current_admin


# API Dependency Pattern (RULE 8.6.7)
class RoleApiDep:
    """API dependency for role endpoints."""
    
    def __init__(self, session: AsyncSession):
        self.service = RoleService(session)
        self.session = session
    
    async def list_roles(self):
        """List all available roles."""
        return await self.service.list_roles()
    
    async def update_user_roles(
        self,
        family_id: UUID,
        user_id: UUID,
        data,
        current_user_id: UUID,
        current_user_is_superadmin: bool,
        if_match: Optional[str] = None,
    ):
        """Update user roles within a family."""
        return await self.service.update_user_roles(
            family_id, user_id, data, current_user_id, current_user_is_superadmin,
            if_match=if_match
        )


def get_role_api(session: AsyncSession = Depends(get_session)) -> RoleApiDep:
    """Dependency function to get RoleApiDep instance."""
    return RoleApiDep(session)
