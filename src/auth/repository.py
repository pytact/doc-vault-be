"""Authentication repository."""
from uuid import UUID
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.users.models import User
from src.roles.models import UserRole, Role
from src.families.models import Family


class AuthRepository:
    """Repository for authentication database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_email(
        self, email: str
    ) -> Optional[User]:
        """Get user by email (not soft-deleted, case-insensitive)."""
        result = await self.session.execute(
            select(User)
            .where(
                User.email.ilike(email),  # Case-insensitive email lookup
                User.is_del == False,  # Not soft-deleted
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_role_info(
        self, user_id: UUID
    ) -> Optional[Tuple[UserRole, Role, Optional[Family]]]:
        """Get user's role information with Role and Family."""
        result = await self.session.execute(
            select(UserRole, Role, Family)
            .join(Role, UserRole.role_id == Role.id)
            .outerjoin(Family, UserRole.family_id == Family.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_del == False,  # Not soft-deleted
                UserRole.deleted_at.is_(None),  # Active role assignment
            )
        )
        row = result.first()
        if row:
            return (row[0], row[1], row[2])  # UserRole, Role, Family
        return None
    
    async def get_user_by_id(
        self, user_id: UUID
    ) -> Optional[User]:
        """Get user by ID (not soft-deleted)."""
        result = await self.session.execute(
            select(User)
            .where(
                User.id == user_id,
                User.is_del == False,  # Not soft-deleted
            )
        )
        return result.scalar_one_or_none()
