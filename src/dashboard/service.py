"""Dashboard analytics service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.dashboard.repository import DashboardRepository
from src.dashboard.schemas import AnalyticsDashboardResponse


class DashboardService:
    """Service for dashboard analytics business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = DashboardRepository(session)
        self.session = session
    
    async def get_dashboard_analytics(
        self,
        if_none_match: Optional[str] = None,
    ) -> AnalyticsDashboardResponse:
        """Get platform-wide dashboard summary metrics.
        
        Business Rules:
        1. All counts are computed across all families and users in the system
        2. Counts include both active and soft-deleted entities
        3. Metrics are computed at request time (not cached, but may be optimized for performance)
        4. SuperAdmin cannot see document details or metadata (only counts)
        """
        # Get all metrics in parallel (if possible) or sequentially
        total_families = await self.repository.get_total_families()
        active_families = await self.repository.get_active_families()
        soft_deleted_families = await self.repository.get_soft_deleted_families()
        
        total_users = await self.repository.get_total_users()
        active_users = await self.repository.get_active_users()
        soft_deleted_users = await self.repository.get_soft_deleted_users()
        
        total_documents = await self.repository.get_total_documents()
        
        return AnalyticsDashboardResponse(
            total_families=total_families,
            total_users=total_users,
            total_documents=total_documents,
            active_families=active_families,
            active_users=active_users,
            soft_deleted_families=soft_deleted_families,
            soft_deleted_users=soft_deleted_users,
        )
