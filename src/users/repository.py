"""User repository."""
from uuid import UUID
from typing import Optional, Tuple, List
from datetime import datetime, timezone
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from src.users.models import User
from src.roles.models import UserRole, Role
from src.families.models import Family
from src.documents.models import Document, DocumentAssign
from src.notification.models import ReminderSchedule, InAppNotification


class UserRepository:
    """Repository for user database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_and_family(
        self, user_id: UUID, family_id: UUID
    ) -> Optional[User]:
        """Get user by ID and family ID."""
        result = await self.session.execute(
            select(User)
            .where(
                User.id == user_id,
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
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            )
        )
        row = result.first()
        if row:
            return (row[0], row[1], row[2])  # UserRole, Role, Family
        return None
    
    async def list_by_family_with_pagination(
        self,
        family_id: UUID,
        page: int,
        page_size: int,
        status_filter: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Tuple[User, Optional[UserRole], Optional[Role], Optional[Family]]], int]:
        """List users by family with pagination, filtering, sorting, and role information."""
        # Build base query with joins - filter by family_id through UserRole
        query = (
            select(User, UserRole, Role, Family)
            .join(UserRole, and_(
                UserRole.user_id == User.id,
                UserRole.family_id == family_id,  # Filter by family_id
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            ))
            .outerjoin(Role, UserRole.role_id == Role.id)
            .outerjoin(Family, UserRole.family_id == Family.id)
        )
        
        # Apply status filter (map API status to database status)
        if status_filter:
            if status_filter == "Active":
                query = query.where(
                    User.is_del == False,
                    User.status == "active",
                )
            elif status_filter == "PendingActivation":
                query = query.where(
                    User.is_del == False,
                    User.status == "pending",
                )
            elif status_filter == "SoftDeleted":
                query = query.where(User.is_del == True)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = None
        if sort_by == "name":
            # Note: User model doesn't have name field - sort by email
            sort_column = User.email
        elif sort_by == "email":
            sort_column = User.email
        elif sort_by == "status":
            sort_column = User.status
        elif sort_by == "created_at":
            sort_column = User.created_at
        
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        return list(rows), total
    
    async def list_all_with_pagination(
        self,
        page: int,
        page_size: int,
        status_filter: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Tuple[User, Optional[UserRole], Optional[Role], Optional[Family]]], int]:
        """List all users with pagination, filtering, sorting, and role information.
        
        Returns users with their first active role (if any), ordered by created_at.
        """
        # Build base query with joins - get first active role per user
        # Use a window function to get the first active UserRole for each user (by created_at)
        # Create a subquery that ranks UserRoles by created_at for each user
        ranked_roles = (
            select(
                UserRole.id,
                UserRole.user_id,
                func.row_number()
                .over(
                    partition_by=UserRole.user_id,
                    order_by=UserRole.created_at.asc()
                )
                .label('rn')
            )
            .where(
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            )
            .subquery()
        )
        
        # Get only the first role (rn = 1) for each user
        first_role_subquery = (
            select(ranked_roles.c.id, ranked_roles.c.user_id)
            .where(ranked_roles.c.rn == 1)
            .subquery()
        )
        
        # Start from User table and left join to get role information
        query = (
            select(User, UserRole, Role, Family)
            .select_from(User)
            .outerjoin(
                first_role_subquery,
                User.id == first_role_subquery.c.user_id
            )
            .outerjoin(
                UserRole,
                and_(
                    UserRole.id == first_role_subquery.c.id,
                    UserRole.is_del == False,
                    UserRole.deleted_at.is_(None),
                )
            )
            .outerjoin(Role, UserRole.role_id == Role.id)
            .outerjoin(Family, UserRole.family_id == Family.id)
        )
        
        # Apply status filter (map API status to database status)
        if status_filter:
            if status_filter == "Active":
                query = query.where(
                    User.is_del == False,
                    User.status == "active",
                )
            elif status_filter == "PendingActivation":
                query = query.where(
                    User.is_del == False,
                    User.status == "pending",
                )
            elif status_filter == "SoftDeleted":
                query = query.where(User.is_del == True)
        
        # Count total (before pagination) - count distinct users
        count_query = select(func.count(User.id.distinct())).select_from(User)
        if status_filter:
            if status_filter == "Active":
                count_query = count_query.where(
                    User.is_del == False,
                    User.status == "active",
                )
            elif status_filter == "PendingActivation":
                count_query = count_query.where(
                    User.is_del == False,
                    User.status == "pending",
                )
            elif status_filter == "SoftDeleted":
                count_query = count_query.where(User.is_del == True)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = None
        if sort_by == "name":
            # Note: User model doesn't have name field - sort by email
            sort_column = User.email
        elif sort_by == "email":
            sort_column = User.email
        elif sort_by == "status":
            sort_column = User.status
        elif sort_by == "created_at":
            sort_column = User.created_at
        
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        return list(rows), total
    
    async def get_family_by_id(
        self, family_id: UUID
    ) -> Optional[Family]:
        """Get family by ID."""
        result = await self.session.execute(
            select(Family)
            .where(Family.id == family_id)
        )
        return result.scalar_one_or_none()
    
    async def soft_delete(
        self, user: User
    ) -> User:
        """Soft delete a user."""
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_email(
        self, email: str
    ) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        result = await self.session.execute(
            select(User)
            .where(func.lower(User.email) == func.lower(email))
        )
        return result.scalar_one_or_none()
    
    async def get_by_invite_token(
        self, invite_token: str
    ) -> Optional[User]:
        """Get user by invitation token with family relationship."""
        result = await self.session.execute(
            select(User)
            .where(User.invite_token == invite_token)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self, user: User
    ) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    # ==================== SuperAdmin User Management Methods ====================
    
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
    
    async def get_all_active_user_roles(self, user_id: UUID) -> List[UserRole]:
        """Get all active UserRoles for user."""
        result = await self.session.execute(
            select(UserRole)
            .where(
                UserRole.user_id == user_id,
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
    
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
    
    async def get_user_role_by_user_id(
        self, user_id: UUID
    ) -> Optional[UserRole]:
        """Get UserRole for user (including soft-deleted)."""
        result = await self.session.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .order_by(UserRole.created_at.desc())  # Get most recent
        )
        return result.scalar_one_or_none()
    
    async def reactivate_user_role(
        self, user_role: UserRole, updated_by: UUID
    ) -> None:
        """Reactivate soft-deleted UserRole."""
        now = datetime.now(timezone.utc)
        user_role.is_del = False
        user_role.deleted_at = None
        user_role.deleted_by = None
        user_role.updated_at = now
        user_role.updated_by = updated_by
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
    
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
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
    
    async def create_user_role(
        self, user_id: UUID, family_id: UUID, role_id: UUID, created_by: UUID, updated_by: UUID
    ) -> UserRole:
        """Create a new UserRole for user in family."""
        new_user_role = UserRole(
            user_id=user_id,
            family_id=family_id,
            role_id=role_id,
            created_by=created_by,
            updated_by=updated_by,
            is_del=False,
        )
        self.session.add(new_user_role)
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
        await self.session.refresh(new_user_role)
        return new_user_role
    
    async def get_documents_by_owner(self, owner_id: UUID) -> List:
        """Get all documents owned by user (including soft-deleted)."""
        result = await self.session.execute(
            select(Document).where(Document.owner_id == owner_id)
        )
        return list(result.scalars().all())
    
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
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
    
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
    
    async def get_assignments_by_user(self, user_id: UUID) -> List:
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
        
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
        return count
    
    async def get_schedules_by_user(self, user_id: UUID) -> List:
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
        
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
        return count
    
    async def get_notifications_by_user(self, user_id: UUID) -> List:
        """Get all in-app notifications for user (not soft-deleted)."""
        result = await self.session.execute(
            select(InAppNotification)
            .where(
                InAppNotification.user_id == user_id,
                InAppNotification.is_del == False,
            )
        )
        return list(result.scalars().all())
    
    async def delete_notifications_by_user(self, user_id: UUID) -> int:
        """Soft delete all in-app notifications for user.
        
        Returns:
            int: Number of notifications deleted
        """
        notifications = await self.get_notifications_by_user(user_id)
        
        if not notifications:
            return 0
        
        count = 0
        for notification in notifications:
            notification.is_del = True
            count += 1
        
        # Don't commit here - let the caller commit the transaction
        await self.session.flush()
        return count