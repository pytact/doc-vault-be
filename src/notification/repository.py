"""Notification repository."""
from uuid import UUID
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.notification.models import InAppNotification, ReminderSchedule
from src.documents.models import Document
from src.users.models import User
from src.taxonomy.models import Category, Subcategory
from src.families.models import Family
from src.roles.models import UserRole, Role


class NotificationRepository:
    """Repository for notification database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, notification_id: UUID
    ) -> Optional[InAppNotification]:
        """Get notification by ID."""
        result = await self.session.execute(
            select(InAppNotification)
            .where(
                InAppNotification.id == notification_id,
                InAppNotification.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_user_with_pagination(
        self,
        user_id: UUID,
        family_id: UUID,
        page: int,
        page_size: int,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[InAppNotification], int]:
        """List notifications for Member/Owner with pagination and sorting.
        
        Only shows notifications for documents owned by the user and within their family.
        
        Args:
            user_id: User ID (must be document owner)
            family_id: Family ID from token (for filtering)
            page: Page number
            page_size: Page size
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
        """
        # Build base query - filter by:
        # 1. Notifications for this user
        # 2. Documents owned by this user
        # 3. Documents in the user's family (from token)
        query = (
            select(InAppNotification)
            .join(Document, InAppNotification.document_id == Document.id)
            .where(
                InAppNotification.user_id == user_id,
                Document.owner_id == user_id,  # Only documents owned by user
                Document.family_id == family_id,  # Only documents in user's family
                InAppNotification.is_del == False,
                Document.is_del == False,
            )
        )
        
        # Apply sorting
        if sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(InAppNotification.created_at.desc())
            else:
                query = query.order_by(InAppNotification.created_at.asc())
        
        # Count total
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return list(notifications), total
    
    async def list_by_family_with_pagination(
        self,
        family_id: UUID,
        page: int,
        page_size: int,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[InAppNotification], int]:
        """List all notifications for all documents in a family (FamilyAdmin view).
        
        Shows all notifications for all documents in the family, regardless of
        who owns the document or who the notification is for.
        
        Args:
            family_id: Family ID from token
            page: Page number
            page_size: Page size
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
        """
        # Build base query - show ALL notifications for ALL documents in the family
        query = (
            select(InAppNotification)
            .join(Document, InAppNotification.document_id == Document.id)
            .where(
                Document.family_id == family_id,  # Only documents in this family
                InAppNotification.is_del == False,
                Document.is_del == False,
            )
        )
        
        # Apply sorting
        if sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(InAppNotification.created_at.desc())
            else:
                query = query.order_by(InAppNotification.created_at.asc())
        
        # Count total
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return list(notifications), total
    
    async def update_read_status(
        self, notification_id: UUID, user_id: UUID, is_read: bool
    ) -> Optional[InAppNotification]:
        """Update notification read status (mark as read or unread).
        
        Note: Permission validation should be done in the service layer.
        This method only performs the update operation.
        """
        notification = await self.get_by_id(notification_id)
        if not notification:
            return None
        
        from datetime import timezone
        
        # Update read status based on is_read flag
        if is_read:
            # Mark as read - set read_at to current timestamp
            if notification.read_at is None:
                notification.read_at = datetime.now(timezone.utc)
                await self.session.commit()
                await self.session.refresh(notification)
        else:
            # Mark as unread - clear read_at
            if notification.read_at is not None:
                notification.read_at = None
                await self.session.commit()
                await self.session.refresh(notification)
        
        return notification
    
    async def update_all_read_status(
        self, user_id: UUID, is_read: bool
    ) -> int:
        """Update read status for all notifications for user (mark all as read or unread)."""
        from datetime import timezone
        
        if is_read:
            # Mark all unread notifications as read
            result = await self.session.execute(
                select(InAppNotification)
                .where(
                    InAppNotification.user_id == user_id,
                    InAppNotification.is_del == False,
                    InAppNotification.read_at.is_(None),
                )
            )
            notifications = result.scalars().all()
            
            count = 0
            for notification in notifications:
                notification.read_at = datetime.now(timezone.utc)
                count += 1
            
            if count > 0:
                await self.session.commit()
            
            return count
        else:
            # Mark all read notifications as unread
            result = await self.session.execute(
                select(InAppNotification)
                .where(
                    InAppNotification.user_id == user_id,
                    InAppNotification.is_del == False,
                    InAppNotification.read_at.isnot(None),
                )
            )
            notifications = result.scalars().all()
            
            count = 0
            for notification in notifications:
                notification.read_at = None
                count += 1
            
            if count > 0:
                await self.session.commit()
            
            return count
    
    async def get_upcoming_expiries_for_owner(
        self, user_id: UUID, family_id: UUID
    ) -> List[Document]:
        """Get documents expiring in next 30 days for owner.
        
        Only returns documents owned by the user and within their family.
        
        Args:
            user_id: User ID (must be document owner)
            family_id: Family ID from token (for filtering)
        """
        today = date.today()
        thirty_days_later = today + timedelta(days=30)
        
        result = await self.session.execute(
            select(Document)
            .where(
                Document.owner_id == user_id,  # Only documents owned by user
                Document.family_id == family_id,  # Only documents in user's family
                Document.expiry_date.isnot(None),
                Document.expiry_date >= today,
                Document.expiry_date <= thirty_days_later,
                Document.is_del == False,
            )
            .order_by(Document.expiry_date.asc())
        )
        return list(result.scalars().all())
    
    async def get_upcoming_expiries_for_familyadmin(
        self, family_id: UUID
    ) -> List[Document]:
        """Get documents expiring in next 30 days for FamilyAdmin (all family documents)."""
        today = date.today()
        thirty_days_later = today + timedelta(days=30)
        
        result = await self.session.execute(
            select(Document)
            .where(
                Document.family_id == family_id,
                Document.expiry_date.isnot(None),
                Document.expiry_date >= today,
                Document.expiry_date <= thirty_days_later,
                Document.is_del == False,
            )
            .order_by(Document.expiry_date.asc())
        )
        return list(result.scalars().all())
    
    async def get_document_by_id(
        self, document_id: UUID
    ) -> Optional[Document]:
        """Get document by ID."""
        result = await self.session.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.is_del == False,
            )
        )
        return result.scalar_one_or_none()
    
    # ==================== ReminderSchedule Methods ====================
    
    async def cancel_pending_schedules_for_document(
        self, document_id: UUID
    ) -> int:
        """Cancel all pending ReminderSchedule records for a document.
        
        Returns:
            int: Number of schedules cancelled
        """
        result = await self.session.execute(
            select(ReminderSchedule)
            .where(
                ReminderSchedule.document_id == document_id,
                ReminderSchedule.status == "pending",
            )
        )
        schedules = result.scalars().all()
        
        count = 0
        for schedule in schedules:
            schedule.status = "cancelled"
            count += 1
        
        if count > 0:
            await self.session.commit()
        
        return count
    
    async def get_owner_and_familyadmins_for_document(
        self, document_id: UUID
    ) -> List[User]:
        """Get Owner and FamilyAdmin users who should receive reminders for a document.
        
        Returns:
            List[User]: List of users (Owner + FamilyAdmins) who should receive notifications
        """
        # Get document to find owner_id and family_id
        document = await self.get_document_by_id(document_id)
        if not document:
            return []
        
        users = []
        
        # Add Owner
        owner_result = await self.session.execute(
            select(User)
            .where(
                User.id == document.owner_id,
                User.is_del == False,
            )
        )
        owner = owner_result.scalar_one_or_none()
        if owner:
            users.append(owner)
        
        # Add FamilyAdmins (users with FamilyAdmin role in the document's family)
        familyadmin_result = await self.session.execute(
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                UserRole.family_id == document.family_id,
                Role.name == "familyadmin",
                UserRole.is_del == False,
                UserRole.deleted_at.is_(None),
                User.is_del == False,
            )
        )
        familyadmins = familyadmin_result.scalars().all()
        
        # Add FamilyAdmins (avoid duplicates if owner is also FamilyAdmin)
        for familyadmin in familyadmins:
            if familyadmin.id != document.owner_id:  # Don't add owner twice
                users.append(familyadmin)
        
        return users
    
    async def create_reminder_schedules(
        self,
        document_id: UUID,
        expiry_date: date,
        users: List[User],
    ) -> List[ReminderSchedule]:
        """Create ReminderSchedule records for multiple users.
        
        Creates schedules based on days remaining until expiry:
        - 30d schedule: Only if expiry_date >= 30 days from today
        - 7d schedule: Only if expiry_date >= 7 days from today
        - 0d schedule: Always created if expiry_date >= today
        
        Args:
            document_id: Document ID
            expiry_date: Document expiry date
            users: List of users to create schedules for
        
        Returns:
            List[ReminderSchedule]: Created schedule records
        """
        from datetime import timedelta, timezone
        
        schedules = []
        today = date.today()
        days_remaining = (expiry_date - today).days
        
        # Get current UTC datetime for comparison
        now_utc = datetime.now(timezone.utc)
        today_utc = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        
        # Calculate send_at dates
        send_at_30d = datetime.combine(
            expiry_date - timedelta(days=30),
            datetime.min.time(),
            tzinfo=timezone.utc
        )
        send_at_7d = datetime.combine(
            expiry_date - timedelta(days=7),
            datetime.min.time(),
            tzinfo=timezone.utc
        )
        send_at_0d = datetime.combine(
            expiry_date,
            datetime.min.time(),
            tzinfo=timezone.utc
        )
        
        for user in users:
            # Create 30d schedule only if:
            # - At least 30 days remaining AND
            # - send_at_30d is today or in the future (not in the past)
            if days_remaining >= 30 and send_at_30d >= today_utc:
                schedule_30d = ReminderSchedule(
                    document_id=document_id,
                    user_id=user.id,
                    reminder_type="30d",
                    send_at=send_at_30d,
                    status="pending",
                )
                schedules.append(schedule_30d)
                self.session.add(schedule_30d)
            
            # Create 7d schedule only if:
            # - At least 7 days remaining AND
            # - send_at_7d is today or in the future (not in the past)
            if days_remaining >= 7 and send_at_7d >= today_utc:
                schedule_7d = ReminderSchedule(
                    document_id=document_id,
                    user_id=user.id,
                    reminder_type="7d",
                    send_at=send_at_7d,
                    status="pending",
                )
                schedules.append(schedule_7d)
                self.session.add(schedule_7d)
            
            # Create 0d schedule if expiry_date is today or in the future
            if days_remaining >= 0 and send_at_0d >= today_utc:
                schedule_0d = ReminderSchedule(
                    document_id=document_id,
                    user_id=user.id,
                    reminder_type="0d",
                    send_at=send_at_0d,
                    status="pending",
                )
                schedules.append(schedule_0d)
                self.session.add(schedule_0d)
        
        if schedules:
            await self.session.commit()
            
            # Refresh all schedules to get IDs
            for schedule in schedules:
                await self.session.refresh(schedule)
        
        return schedules
    
    async def get_pending_schedules_due_now(
        self,
    ) -> List[ReminderSchedule]:
        """Get all pending ReminderSchedule records where send_at <= NOW().
        
        Returns:
            List[ReminderSchedule]: Pending schedules that are due to be sent
        """
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        
        result = await self.session.execute(
            select(ReminderSchedule)
            .where(
                ReminderSchedule.status == "pending",
                ReminderSchedule.send_at <= now,
            )
            .order_by(ReminderSchedule.send_at.asc())
        )
        return list(result.scalars().all())
    
    async def mark_schedule_as_sent(
        self, schedule_id: UUID
    ) -> Optional[ReminderSchedule]:
        """Mark a ReminderSchedule as sent.
        
        Args:
            schedule_id: ReminderSchedule ID
        
        Returns:
            Optional[ReminderSchedule]: Updated schedule or None if not found
        """
        from datetime import datetime, timezone
        
        result = await self.session.execute(
            select(ReminderSchedule)
            .where(ReminderSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            return None
        
        schedule.status = "sent"
        schedule.sent_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(schedule)
        
        return schedule

