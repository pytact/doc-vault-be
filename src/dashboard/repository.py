"""Dashboard repository."""
from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.users.models import User
from src.families.models import Family
from src.roles.models import Role, UserRole
from src.documents.models import Document, DocumentAssign
from src.notification.models import ReminderSchedule


class DashboardRepository:
    """Repository for dashboard database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ==================== User Operations ====================
    
    async def get_user_with_role_info(
        self, user_id: UUID
    ) -> Optional[Tuple[User, Optional[UserRole], Optional[Role], Optional[Family]]]:
        """Get user with role information (eager loading relationships)."""
        result = await self.session.execute(
            select(User, UserRole, Role, Family)
            .outerjoin(UserRole, and_(
                User.id == UserRole.user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .outerjoin(Role, UserRole.role_id == Role.id)
            .outerjoin(Family, UserRole.family_id == Family.id)
            .where(User.id == user_id)
        )
        row = result.first()
        if row:
            return (row[0], row[1], row[2], row[3])  # User, UserRole, Role, Family
        return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID (including soft-deleted for SuperAdmin)."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_users_by_ids(
        self, user_ids: List[UUID]
    ) -> List[User]:
        """Get multiple users by IDs."""
        result = await self.session.execute(
            select(User).where(User.id.in_(user_ids))
        )
        return list(result.scalars().all())
    
    async def soft_delete_user(
        self, user_id: UUID, deleted_by: UUID
    ) -> None:
        """Soft delete user."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_del=True,
                deleted_at=now,
                deleted_by=deleted_by,
                updated_at=now,
                updated_by=deleted_by,
            )
        )
        await self.session.commit()
    
    async def reactivate_user(
        self, user_id: UUID, updated_by: UUID
    ) -> None:
        """Reactivate soft-deleted user."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_del=False,
                deleted_at=None,
                deleted_by=None,
                updated_at=now,
                updated_by=updated_by,
            )
        )
        await self.session.commit()
    
    # ==================== Family Operations ====================
    
    async def get_family_by_id(self, family_id: UUID) -> Optional[Family]:
        """Get family by ID (including soft-deleted for SuperAdmin)."""
        result = await self.session.execute(
            select(Family).where(Family.id == family_id)
        )
        return result.scalar_one_or_none()
    
    # ==================== Role Operations ====================
    
    async def get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        result = await self.session.execute(
            select(Role).where(
                Role.id == role_id,
                Role.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_user_role(self, user_id: UUID) -> Optional[UserRole]:
        """Get active UserRole for user."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_role_for_family(
        self, user_id: UUID, family_id: UUID
    ) -> Optional[UserRole]:
        """Get UserRole for user and family (including soft-deleted)."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.family_id == family_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def soft_delete_user_role(
        self, user_role: UserRole, deleted_by: UUID
    ) -> None:
        """Soft delete UserRole."""
        now = datetime.now(timezone.utc)
        user_role.is_del = True
        user_role.deleted_at = now
        user_role.deleted_by = deleted_by
        user_role.updated_at = now
        user_role.updated_by = deleted_by
        await self.session.commit()
    
    async def create_or_reactivate_user_role(
        self, user_id: UUID, family_id: UUID, role_id: UUID, updated_by: UUID
    ) -> UserRole:
        """Create or reactivate UserRole for user in family."""
        # Check if UserRole exists (including soft-deleted)
        existing = await self.get_user_role_for_family(user_id, family_id)
        
        if existing:
            # Reactivate and update
            now = datetime.now(timezone.utc)
            existing.is_del = False
            existing.deleted_at = None
            existing.deleted_by = None
            existing.role_id = role_id
            existing.updated_at = now
            existing.updated_by = updated_by
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            new_user_role = UserRole(
                user_id=user_id,
                family_id=family_id,
                role_id=role_id,
                created_by=updated_by,
                updated_by=updated_by,
                is_del=False,
            )
            self.session.add(new_user_role)
            await self.session.commit()
            await self.session.refresh(new_user_role)
            return new_user_role
    
    # ==================== Document Operations ====================
    
    async def get_documents_by_owner(self, owner_id: UUID) -> List[Document]:
        """Get all documents owned by user (including soft-deleted)."""
        result = await self.session.execute(
            select(Document).where(Document.owner_id == owner_id)
        )
        return list(result.scalars().all())
    
    async def update_document_family(
        self, document_id: UUID, new_family_id: UUID, updated_by: UUID
    ) -> None:
        """Update document's family_id."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                family_id=new_family_id,
                updated_at=now,
                updated_by=updated_by,
            )
        )
        await self.session.commit()
    
    async def bulk_update_document_family(
        self, document_ids: List[UUID], new_family_id: UUID, updated_by: UUID
    ) -> None:
        """Bulk update documents' family_id."""
        if not document_ids:
            return
        
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Document)
            .where(Document.id.in_(document_ids))
            .values(
                family_id=new_family_id,
                updated_at=now,
                updated_by=updated_by,
            )
        )
        await self.session.commit()
    
    async def soft_delete_documents_by_owner(
        self, owner_id: UUID, deleted_by: UUID
    ) -> None:
        """Soft delete all documents owned by user."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Document)
            .where(
                Document.owner_id == owner_id,
                Document.is_del == False,
            )
            .values(
                is_del=True,
                deleted_at=now,
                deleted_by=deleted_by,
                updated_at=now,
                updated_by=deleted_by,
            )
        )
        await self.session.commit()
    
    # ==================== Document Assignment Operations ====================
    
    async def get_assignments_by_user(self, user_id: UUID) -> List[DocumentAssign]:
        """Get all document assignments for user (active only)."""
        result = await self.session.execute(
            select(DocumentAssign)
            .where(
                DocumentAssign.assign_to == user_id,
                DocumentAssign.is_del == False,
                DocumentAssign.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
    
    async def delete_assignments_by_user(
        self, user_id: UUID, deleted_by: UUID
    ) -> int:
        """Soft delete all document assignments for user.
        
        Returns:
            int: Number of assignments deleted
        """
        assignments = await self.get_assignments_by_user(user_id)
        
        if not assignments:
            return 0
        
        now = datetime.now(timezone.utc)
        count = 0
        for assignment in assignments:
            assignment.is_del = True
            assignment.deleted_at = now
            assignment.deleted_by = deleted_by
            assignment.updated_at = now
            assignment.updated_by = deleted_by
            count += 1
        
        await self.session.commit()
        return count
    
    # ==================== Reminder Schedule Operations ====================
    
    async def get_schedules_by_user(self, user_id: UUID) -> List[ReminderSchedule]:
        """Get all reminder schedules for user (pending only)."""
        result = await self.session.execute(
            select(ReminderSchedule)
            .where(
                ReminderSchedule.user_id == user_id,
                ReminderSchedule.status == "pending",
            )
        )
        return list(result.scalars().all())
    
    async def cancel_schedules_by_user(self, user_id: UUID) -> int:
        """Cancel all pending reminder schedules for user.
        
        Returns:
            int: Number of schedules cancelled
        """
        schedules = await self.get_schedules_by_user(user_id)
        
        if not schedules:
            return 0
        
        count = 0
        for schedule in schedules:
            schedule.status = "cancelled"
            count += 1
        
        await self.session.commit()
        return count
    
    # ==================== Analytics Operations ====================
    
    async def get_total_families(self) -> int:
        """Get total number of families (including soft-deleted)."""
        result = await self.session.execute(
            select(func.count(Family.id))
        )
        return result.scalar() or 0
    
    async def get_active_families(self) -> int:
        """Get number of active families."""
        result = await self.session.execute(
            select(func.count(Family.id))
            .where(
                Family.is_del == False,
            )
        )
        return result.scalar() or 0
    
    async def get_soft_deleted_families(self) -> int:
        """Get number of soft-deleted families."""
        result = await self.session.execute(
            select(func.count(Family.id))
            .where(Family.is_del == True)
        )
        return result.scalar() or 0
    
    async def get_total_users(self) -> int:
        """Get total number of users (including soft-deleted)."""
        result = await self.session.execute(
            select(func.count(User.id))
        )
        return result.scalar() or 0
    
    async def get_active_users(self) -> int:
        """Get number of active users."""
        result = await self.session.execute(
            select(func.count(User.id))
            .where(
                User.is_del == False,
            )
        )
        return result.scalar() or 0
    
    async def get_soft_deleted_users(self) -> int:
        """Get number of soft-deleted users."""
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.is_del == True)
        )
        return result.scalar() or 0
    
    async def get_total_documents(self) -> int:
        """Get total number of documents (including soft-deleted)."""
        result = await self.session.execute(
            select(func.count(Document.id))
        )
        return result.scalar() or 0

