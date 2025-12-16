"""User repository."""
from uuid import UUID
from typing import Optional, Tuple, List
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.users.models import User
from src.roles.models import UserRole, Role
from src.families.models import Family


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
        from sqlalchemy.orm import selectinload
        
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