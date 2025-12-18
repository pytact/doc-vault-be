"""Dashboard dependencies."""
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.families.dependencies import get_current_superadmin
from src.users.models import User
from src.dashboard.service import DashboardService


# API Dependency Pattern (RULE 8.6.7)
class DashboardApiDep:
    """API dependency for dashboard endpoints."""
    
    def __init__(self, session: AsyncSession):
        self.service = DashboardService(session)
        self.session = session
    
    async def get_dashboard_analytics(
        self,
        if_none_match: Optional[str] = None,
    ):
        """Get platform-wide dashboard analytics."""
        return await self.service.get_dashboard_analytics(if_none_match=if_none_match)


def get_dashboard_api(session: AsyncSession = Depends(get_session)) -> DashboardApiDep:
    """Dependency function to get DashboardApiDep instance."""
    return DashboardApiDep(session)

