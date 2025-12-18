"""Notification dependencies."""
from uuid import UUID
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.notification.service import NotificationService
from src.users.models import User


# API Dependency Pattern (RULE 8.6.7)
class NotificationApiDep:
    """API dependency for notification endpoints."""
    
    def __init__(self, session: AsyncSession):
        self.service = NotificationService(session)
        self.session = session
    
    async def list_notifications(
        self,
        user: User,
        query,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ):
        """List notifications with pagination and sorting."""
        return await self.service.list_notifications(user, query, token=token, if_none_match=if_none_match)
    
    async def update_notification_read_status(
        self,
        notification_id: UUID,
        user: User,
        status_request,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ):
        """Update notification read status (mark as read or unread)."""
        return await self.service.update_notification_read_status(
            notification_id, user, status_request, token=token, if_match=if_match
        )
    
    async def update_all_notifications_read_status(
        self,
        user: User,
        status_request,
        token: Optional[str] = None,
    ):
        """Update read status for all notifications (mark all as read or unread)."""
        return await self.service.update_all_notifications_read_status(
            user, status_request, token=token
        )
    
    async def get_upcoming_expiries(
        self,
        user: User,
        token: Optional[str] = None,
    ):
        """Get upcoming expiries for dashboard widget."""
        return await self.service.get_upcoming_expiries(user, token=token)


def get_notification_api(
    session: AsyncSession = Depends(get_session)
) -> NotificationApiDep:
    """Dependency function to get NotificationApiDep instance."""
    return NotificationApiDep(session)

