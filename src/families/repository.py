"""Family repository."""
from uuid import UUID
from typing import Optional, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.families.models import Family


class FamilyRepository:
    """Repository for family database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, family_id: UUID
    ) -> Optional[Family]:
        """Get family by ID."""
        result = await self.session.execute(
            select(Family)
            .where(Family.id == family_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(
        self, name: str
    ) -> Optional[Family]:
        """Get family by name (case-insensitive, not soft-deleted)."""
        result = await self.session.execute(
            select(Family)
            .where(
                Family.name.ilike(name),
                Family.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_with_pagination(
        self,
        page: int,
        page_size: int,
        status_filter: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[list[Family], int]:
        """List families with pagination, filtering, and sorting."""
        # Build base query
        query = select(Family)
        
        # Apply status filter (map API status to database status)
        if status_filter:
            if status_filter == "Active":
                query = query.where(
                    Family.is_del == False,
                    Family.status == "active",
                )
            elif status_filter == "SoftDeleted":
                query = query.where(Family.is_del == True)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply sorting
        sort_column = None
        if sort_by == "name":
            sort_column = Family.name
        elif sort_by == "created_at":
            sort_column = Family.created_at
        elif sort_by == "status":
            sort_column = Family.status
        
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
        items = result.scalars().all()
        
        return list(items), total
    
    async def create(
        self, family: Family
    ) -> Family:
        """Create a new family."""
        self.session.add(family)
        await self.session.commit()
        await self.session.refresh(family)
        return family
    
    async def update(
        self, family: Family
    ) -> Family:
        """Update an existing family."""
        await self.session.commit()
        await self.session.refresh(family)
        return family
    
    async def soft_delete(
        self, family: Family
    ) -> Family:
        """Soft delete a family."""
        await self.session.commit()
        await self.session.refresh(family)
        return family
