"""Role repository."""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession
from src.roles.models import Role, UserRole


class RoleRepository:
    """Repository for role database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_name(
        self, name: str
    ) -> Optional[Role]:
        """Get role by name (not soft-deleted)."""
        result = await self.session.execute(
            select(Role)
            .where(
                Role.name == name,
                Role.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
    ) -> list[Role]:
        """Get all roles (not soft-deleted)."""
        result = await self.session.execute(
            select(Role)
            .where(Role.is_del == False)
            .order_by(Role.name)
        )
        return list(result.scalars().all())
    
    async def get_by_id(
        self, role_id: UUID
    ) -> Optional[Role]:
        """Get role by ID (not soft-deleted)."""
        result = await self.session.execute(
            select(Role)
            .where(
                Role.id == role_id,
                Role.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_role_by_user_and_family(
        self, user_id: UUID, family_id: UUID
    ) -> Optional[UserRole]:
        """Get user role by user_id and family_id (not soft-deleted)."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.family_id == family_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_roles_by_user_and_family(
        self, user_id: UUID, family_id: UUID
    ) -> list[UserRole]:
        """Get all user roles by user_id and family_id (not soft-deleted)."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.family_id == family_id,
                UserRole.is_del.is_(false()),
                UserRole.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
    
    async def get_all_user_roles_by_user_and_family(
        self, user_id: UUID, family_id: UUID
    ) -> list[UserRole]:
        """Get ALL user roles by user_id and family_id (including soft-deleted)."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.family_id == family_id,
            )
        )
        return list(result.scalars().all())
    
    async def create_user_role(
        self, user_role: UserRole
    ) -> UserRole:
        """Create a new user role assignment."""
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role
    
    async def update_user_role(
        self, user_role: UserRole, role_id: UUID, updated_by: UUID
    ) -> UserRole:
        """Update an existing user role assignment (change role_id)."""
        user_role.role_id = role_id
        user_role.updated_by = updated_by
        user_role.is_del = False
        user_role.deleted_at = None
        user_role.deleted_by = None
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role
    
    async def delete_user_role(
        self, user_role: UserRole, deleted_by: UUID
    ) -> None:
        """Soft delete a user role assignment."""
        user_role.is_del = True
        user_role.deleted_at = datetime.now(timezone.utc)
        user_role.deleted_by = deleted_by
        user_role.updated_by = deleted_by
        await self.session.commit()
        await self.session.refresh(user_role)

