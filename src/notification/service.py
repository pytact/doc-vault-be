"""Notification service."""
from uuid import UUID
from typing import Optional, List
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.notification.repository import NotificationRepository
from src.notification.models import InAppNotification, ReminderSchedule
from src.documents.models import Document
from src.taxonomy.models import Category, Subcategory
from src.families.models import Family
from src.notification.schemas import (
    NotificationRead,
    NotificationPaginatedResponse,
    NotificationMarkReadResponse,
    NotificationMarkAllReadResponse,
    NotificationStatusUpdateRequest,
    UpcomingExpiryItem,
    UpcomingExpiriesResponse,
)
from src.notification.exceptions import (
    NotificationNotFound,
    DocumentNotFound,
    DocumentDeleted,
    FamilyDeleted,
    NotificationPermissionDenied,
    NotificationAccessDenied,
)
from src.notification.constants import (
    ROLE_OWNER,
    ROLE_FAMILYADMIN,
    UPCOMING_EXPIRIES_DAYS,
    REMINDER_TYPE_30D,
    REMINDER_TYPE_7D,
    REMINDER_TYPE_0D,
    MESSAGE_TYPE_EXPIRY_30D,
    MESSAGE_TYPE_EXPIRY_7D,
    MESSAGE_TYPE_EXPIRY_0D,
)
from src.pagination import calculate_total_pages
from src.auth.utils import decode_token
from src.users.models import User
from src.response import ServiceResponse
from src.utils import generate_etag, format_last_modified
from fastapi import status


class NotificationService:
    """Service for notification business logic."""
    
    def __init__(self, session: AsyncSession):
        self.repository = NotificationRepository(session)
        self.session = session
    
    def _get_user_role_and_family(self, token: Optional[str]) -> tuple[Optional[str], Optional[UUID]]:
        """Extract role and family_id from JWT token (business logic in service)."""
        if not token:
            return None, None
        
        payload = decode_token(token)
        if not payload:
            return None, None
        
        role = payload.get("role", "").lower()
        family_id_str = payload.get("family_id")
        family_id = UUID(family_id_str) if family_id_str else None
        
        return role, family_id
    
    def _validate_notification_access(self, user_role: Optional[str]) -> None:
        """Validate user has permission to access notifications.
        
        Blocks superadmin and only allows familyadmin and member roles.
        """
        if user_role == "superadmin":
            raise NotificationPermissionDenied(
                "SuperAdmin role cannot access notifications"
            )
        if user_role not in [ROLE_OWNER, ROLE_FAMILYADMIN, "member"]:
            raise NotificationPermissionDenied(
                "Only Member and FamilyAdmin roles can access notifications"
            )
    
    async def _get_category_name(self, category_id: UUID) -> str:
        """Get category name by ID."""
        result = await self.session.execute(
            select(Category)
            .where(
                Category.id == category_id,
                Category.is_del == False,
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            return "Unknown Category"
        return category.name
    
    async def _get_subcategory_name(self, subcategory_id: UUID) -> str:
        """Get subcategory name by ID."""
        result = await self.session.execute(
            select(Subcategory)
            .where(
                Subcategory.id == subcategory_id,
                Subcategory.is_del == False,
            )
        )
        subcategory = result.scalar_one_or_none()
        if not subcategory:
            return "Unknown Subcategory"
        return subcategory.name
    
    async def _build_notification_read(
        self, notification: InAppNotification
    ) -> NotificationRead:
        """Build NotificationRead from InAppNotification with dynamic metadata resolution."""
        # Get document
        document = await self.repository.get_document_by_id(notification.document_id)
        if not document:
            raise DocumentNotFound(str(notification.document_id))
        
        # Check if document is soft-deleted
        if document.is_del:
            raise DocumentDeleted(str(notification.document_id))
        
        # Check if family is soft-deleted
        family_result = await self.session.execute(
            select(Family)
            .where(
                Family.id == document.family_id,
                Family.is_del == False,
            )
        )
        family = family_result.scalar_one_or_none()
        if not family:
            raise FamilyDeleted(str(document.family_id))
        
        # Get category and subcategory names (dynamic resolution)
        category_name = await self._get_category_name(document.category_id)
        subcategory_name = await self._get_subcategory_name(document.subcategory_id)
        
        # Build response
        return NotificationRead(
            id=notification.id,
            document_id=notification.document_id,
            document_title=document.title,  # Dynamic resolution
            expiry_date=document.expiry_date,  # Dynamic resolution
            category=category_name,  # Dynamic resolution
            subcategory=subcategory_name,  # Dynamic resolution
            document_link=f"/v1/documents/{notification.document_id}",
            reminder_type=notification.reminder_type,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
            is_read=notification.read_at is not None,
        )
    
    async def list_notifications(
        self,
        user: User,
        query,
        token: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ) -> ServiceResponse[NotificationPaginatedResponse]:
        """List notifications for user with pagination and sorting.
        
        Business Rules:
        - SuperAdmin is blocked from accessing notifications
        - FamilyAdmin: Shows ALL notifications for ALL documents in their family
        - Member/Owner: Shows only notifications for documents they own in their family
        - family_id from token is always validated and used for filtering
        """
        # Get user role and family_id from token
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate access (blocks superadmin)
        self._validate_notification_access(user_role)
        
        # Always require family_id from token for filtering
        if not family_id:
            raise NotificationPermissionDenied(
                "Valid family_id is required in token to access notifications"
            )
        
        # Get notifications based on role
        if user_role == ROLE_FAMILYADMIN:
            # FamilyAdmin: Show ALL notifications for ALL documents in their family
            notifications, total = await self.repository.list_by_family_with_pagination(
                family_id=family_id,
                page=query.page,
                page_size=query.page_size,
                sort_by=query.sort_by,
                sort_order=query.sort_order,
            )
        elif user_role in [ROLE_OWNER, "member"]:
            # Member/Owner: Show only notifications for documents they own
            notifications, total = await self.repository.list_by_user_with_pagination(
                user_id=user.id,
                family_id=family_id,
                page=query.page,
                page_size=query.page_size,
                sort_by=query.sort_by,
                sort_order=query.sort_order,
            )
        else:
            raise NotificationPermissionDenied(
                "Invalid role for accessing notifications"
            )
        
        # Generate ETag from latest notification's updated_at (if any)
        etag = None
        last_modified = None
        if notifications:
            latest_notification = notifications[0]  # Already sorted DESC by created_at
            etag = generate_etag(latest_notification.updated_at)
            last_modified = format_last_modified(latest_notification.updated_at)
            
            # Check If-None-Match (business logic validation in service)
            if if_none_match:
                # Remove quotes if present
                if_none_match_clean = if_none_match.strip('"')
                if if_none_match_clean == etag:
                    # Return 304 Not Modified (business logic decision in service)
                    return ServiceResponse(
                        data=None,  # 304 has no body
                        status_code=status.HTTP_304_NOT_MODIFIED,
                        headers={
                            "ETag": f'"{etag}"',
                            "Last-Modified": last_modified,
                        },
                        response_type="fastapi",  # Router uses this to return FastAPI Response
                    )
        
        # Build response items with dynamic metadata resolution
        items = []
        for notification in notifications:
            try:
                notification_read = await self._build_notification_read(notification)
                items.append(notification_read)
            except (DocumentNotFound, DocumentDeleted, FamilyDeleted):
                # Skip notifications with deleted documents/families
                continue
        
        # Calculate pagination
        total_pages = calculate_total_pages(total, query.page_size)
        
        # Build next_page and prev_page URLs
        next_page = None
        if query.page < total_pages:
            next_page = f"/v1/notifications?page={query.page + 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
        
        prev_page = None
        if query.page > 1:
            prev_page = f"/v1/notifications?page={query.page - 1}&page_size={query.page_size}&sort_by={query.sort_by}&sort_order={query.sort_order}"
        
        response_data = NotificationPaginatedResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page,
        )
        
        # Prepare headers
        headers = {}
        if etag:
            headers["ETag"] = f'"{etag}"'
        if last_modified:
            headers["Last-Modified"] = last_modified
        
        return ServiceResponse(
            data=response_data,
            headers=headers,
        )
    
    async def update_notification_read_status(
        self,
        notification_id: UUID,
        user: User,
        status_request: NotificationStatusUpdateRequest,
        token: Optional[str] = None,
        if_match: Optional[str] = None,
    ) -> ServiceResponse[NotificationMarkReadResponse]:
        """Update notification read status (mark as read or unread) with ETag validation."""
        # Get user role and family_id from token
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate access
        self._validate_notification_access(user_role)
        
        # Get notification
        notification = await self.repository.get_by_id(notification_id)
        if not notification:
            raise NotificationNotFound(str(notification_id))
        
        # Verify user has permission to update the notification
        # FamilyAdmin: Can update notifications for members in the same family
        # Member/Owner: Can only update their own notifications
        if user_role == ROLE_FAMILYADMIN:
            # FamilyAdmin: Verify notification's document belongs to the same family
            if not family_id:
                raise NotificationPermissionDenied(
                    "Valid family_id is required in token to update notifications"
                )
            
            # Get the document associated with the notification
            document = await self.repository.get_document_by_id(notification.document_id)
            if not document:
                raise DocumentNotFound(str(notification.document_id))
            
            # Check if document belongs to the same family
            if document.family_id != family_id:
                raise NotificationAccessDenied(
                    "You do not have permission to update this notification"
                )
        else:
            # Member/Owner: Must own the notification
            if notification.user_id != user.id:
                raise NotificationAccessDenied(
                    "You do not have permission to update this notification"
                )
        
        # ETag validation (business logic in service) - REQUIRED for PATCH operations
        if not if_match:
            from src.exceptions import PreconditionRequiredError
            raise PreconditionRequiredError(
                message="If-Match header is required for update operations",
                details=[{"field": "etag", "issue": "If-Match header is required"}],
            )
        
        # Validate ETag (business logic in service)
        current_etag = generate_etag(notification.updated_at)
        # Remove quotes if present
        if_match_clean = if_match.strip('"')
        if if_match_clean != current_etag:
            from src.exceptions import PreconditionFailedError
            raise PreconditionFailedError(
                message="Resource has been modified since retrieval. Please fetch the latest version and retry.",
                details=[{"field": "etag", "issue": "Resource version mismatch"}],
            )
        
        # Update read status
        updated_notification = await self.repository.update_read_status(
            notification_id, user.id, status_request.is_read
        )
        if not updated_notification:
            raise NotificationNotFound(str(notification_id))
        
        # Generate new ETag after update
        new_etag = generate_etag(updated_notification.updated_at)
        
        response_data = NotificationMarkReadResponse(
            id=updated_notification.id,
            read_at=updated_notification.read_at,
            is_read=updated_notification.read_at is not None,
        )
        
        return ServiceResponse(
            data=response_data,
            headers={
                "ETag": f'"{new_etag}"',
            },
        )
    
    async def update_all_notifications_read_status(
        self,
        user: User,
        status_request: NotificationStatusUpdateRequest,
        token: Optional[str] = None,
    ) -> NotificationMarkAllReadResponse:
        """Update read status for all notifications for user (mark all as read or unread)."""
        # Get user role from token
        user_role, _ = self._get_user_role_and_family(token)
        
        # Validate access
        self._validate_notification_access(user_role)
        
        # Update all notifications read status
        marked_count = await self.repository.update_all_read_status(
            user.id, status_request.is_read
        )
        
        return NotificationMarkAllReadResponse(marked_count=marked_count)
    
    async def get_upcoming_expiries(
        self,
        user: User,
        token: Optional[str] = None,
    ) -> UpcomingExpiriesResponse:
        """Get documents expiring in next 30 days for dashboard widget.
        
        Business Rules:
        - SuperAdmin is blocked from accessing upcoming expiries
        - FamilyAdmin: Shows ALL upcoming expiries for ALL documents in their family
        - Member/Owner: Shows only upcoming expiries for documents they own in their family
        - family_id from token is always validated and used for filtering
        """
        # Get user role and family_id from token
        user_role, family_id = self._get_user_role_and_family(token)
        
        # Validate access (blocks superadmin)
        self._validate_notification_access(user_role)
        
        # Always require family_id from token for filtering
        if not family_id:
            raise NotificationPermissionDenied(
                "Valid family_id is required in token to access upcoming expiries"
            )
        
        # Get documents based on role
        if user_role == ROLE_FAMILYADMIN:
            # FamilyAdmin: Show ALL upcoming expiries for ALL documents in their family
            documents = await self.repository.get_upcoming_expiries_for_familyadmin(family_id)
        elif user_role in [ROLE_OWNER, "member"]:
            # Member/Owner: Show only upcoming expiries for documents they own
            documents = await self.repository.get_upcoming_expiries_for_owner(
                user_id=user.id,
                family_id=family_id,
            )
        else:
            raise NotificationPermissionDenied(
                "Invalid role for accessing upcoming expiries"
            )
        
        # Build response items with dynamic metadata resolution
        today = date.today()
        items = []
        for document in documents:
            # Skip if document is soft-deleted
            if document.is_del:
                continue
            
            # Check if family is soft-deleted
            family_result = await self.session.execute(
                select(Family)
                .where(
                    Family.id == document.family_id,
                    Family.is_del == False,
                )
            )
            family = family_result.scalar_one_or_none()
            if not family:
                continue
            
            # Calculate days until expiry
            if document.expiry_date:
                days_until_expiry = (document.expiry_date - today).days
                
                # Get category and subcategory names (dynamic resolution)
                category_name = await self._get_category_name(document.category_id)
                subcategory_name = await self._get_subcategory_name(document.subcategory_id)
                
                items.append(UpcomingExpiryItem(
                    document_id=document.id,
                    document_title=document.title,  # Dynamic resolution
                    expiry_date=document.expiry_date,
                    category=category_name,  # Dynamic resolution
                    subcategory=subcategory_name,  # Dynamic resolution
                    days_until_expiry=days_until_expiry,
                ))
        
        return UpcomingExpiriesResponse(upcoming_expiries=items)
    
    # ==================== ReminderSchedule Methods ====================
    
    async def create_reminder_schedules_for_document(
        self,
        document_id: UUID,
        expiry_date: date,
    ) -> None:
        """Create ReminderSchedule records when document expiry_date is set/updated.
        
        Business Rules:
        - Cancels existing pending schedules for the document
        - Finds Owner and FamilyAdmin(s) for the document
        - Creates schedules based on days remaining until expiry:
          * 30d schedule: Only if expiry_date >= 30 days from today
          * 7d schedule: Only if expiry_date >= 7 days from today
          * 0d schedule: Always created if expiry_date >= today
        - Only creates schedules if expiry_date is valid and in the future
        
        Args:
            document_id: Document ID
            expiry_date: Document expiry date
        """
        # Validate expiry_date is not in the past
        today = date.today()
        if expiry_date < today:
            # Don't create schedules for expired documents
            return
        
        # Get document to validate it exists
        document = await self.repository.get_document_by_id(document_id)
        if not document:
            return
        
        # Cancel existing pending schedules
        await self.repository.cancel_pending_schedules_for_document(document_id)
        
        # Get Owner and FamilyAdmins
        users = await self.repository.get_owner_and_familyadmins_for_document(document_id)
        
        if not users:
            return
        
        # Create reminder schedules
        await self.repository.create_reminder_schedules(
            document_id=document_id,
            expiry_date=expiry_date,
            users=users,
        )
    
    async def send_expiry_email(
        self,
        user: User,
        document: Document,
        reminder_type: str,
    ) -> bool:
        """Send expiry reminder email to user.
        
        Args:
            user: User to send email to
            document: Document that is expiring
            reminder_type: Reminder type ('30d', '7d', '0d')
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        from src.infra.email import send_email, load_email_template
        from src.config import settings
        
        # Calculate days until expiry
        today = date.today()
        if not document.expiry_date:
            return False
        
        days_until_expiry = (document.expiry_date - today).days
        
        # Get category and subcategory names
        category_name = await self._get_category_name(document.category_id)
        subcategory_name = await self._get_subcategory_name(document.subcategory_id)
        
        # Build document link
        document_link = f"{settings.frontend_url}/documents/{document.id}"
        
        # Determine email subject based on reminder type
        if reminder_type == REMINDER_TYPE_30D:
            subject = f"Document Expiring Soon: {document.title} (30 days)"
            days_text = "30 days"
        elif reminder_type == REMINDER_TYPE_7D:
            subject = f"Document Expiring Soon: {document.title} (7 days)"
            days_text = "7 days"
        elif reminder_type == REMINDER_TYPE_0D:
            subject = f"Document Expiring Today: {document.title}"
            days_text = "today"
        else:
            subject = f"Document Expiry Reminder: {document.title}"
            days_text = f"{days_until_expiry} days"
        
        # Load email template
        try:
            template = load_email_template("expiry_reminder.html")
        except FileNotFoundError:
            # Fallback to simple text email if template not found
            text_body = f"""
Your document "{document.title}" is expiring in {days_text}.

Document Details:
- Title: {document.title}
- Category: {category_name}
- Subcategory: {subcategory_name}
- Expiry Date: {document.expiry_date.strftime('%Y-%m-%d')}
- Days Until Expiry: {days_until_expiry}

View document: {document_link}

Please renew this document before it expires.
"""
            return send_email(
                to_email=user.email,
                subject=subject,
                html_body=f"<html><body><pre>{text_body}</pre></body></html>",
                text_body=text_body,
            )
        
        # Replace template variables
        html_body = template.replace("{{ document_title }}", document.title)
        html_body = html_body.replace("{{ expiry_date }}", document.expiry_date.strftime('%Y-%m-%d'))
        html_body = html_body.replace("{{ days_until_expiry }}", str(days_until_expiry))
        html_body = html_body.replace("{{ days_text }}", days_text)
        html_body = html_body.replace("{{ document_link }}", document_link)
        html_body = html_body.replace("{{ category }}", category_name)
        html_body = html_body.replace("{{ subcategory }}", subcategory_name)
        
        # Create plain text version
        text_body = f"""
Your document "{document.title}" is expiring in {days_text}.

Document Details:
- Title: {document.title}
- Category: {category_name}
- Subcategory: {subcategory_name}
- Expiry Date: {document.expiry_date.strftime('%Y-%m-%d')}
- Days Until Expiry: {days_until_expiry}

View document: {document_link}

Please renew this document before it expires.
"""
        
        return send_email(
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
    
    async def create_in_app_notification(
        self,
        document_id: UUID,
        user_id: UUID,
        reminder_type: str,
    ) -> InAppNotification:
        """Create InAppNotification record.
        
        Args:
            document_id: Document ID
            user_id: User ID
            reminder_type: Reminder type ('30d', '7d', '0d')
        
        Returns:
            InAppNotification: Created notification
        """
        # Map reminder_type to message_type
        message_type_map = {
            REMINDER_TYPE_30D: MESSAGE_TYPE_EXPIRY_30D,
            REMINDER_TYPE_7D: MESSAGE_TYPE_EXPIRY_7D,
            REMINDER_TYPE_0D: MESSAGE_TYPE_EXPIRY_0D,
        }
        message_type = message_type_map.get(reminder_type, MESSAGE_TYPE_EXPIRY_30D)
        
        notification = InAppNotification(
            user_id=user_id,
            document_id=document_id,
            reminder_type=reminder_type,
            message_type=message_type,
            read_at=None,
            is_del=False,
        )
        
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        
        return notification
    
    async def process_pending_reminders(self) -> dict:
        """Process pending ReminderSchedule records and send notifications.
        
        This method is called by the Celery scheduler task.
        
        Business Rules:
        - Queries pending schedules where send_at <= NOW()
        - For each schedule:
          - Validates document exists and is not deleted
          - Validates user role is eligible (Owner or FamilyAdmin)
          - Creates InAppNotification
          - Sends email notification
          - Updates ReminderSchedule status to 'sent'
        
        Returns:
            dict: Processing statistics
        """
        stats = {
            "processed": 0,
            "created_notifications": 0,
            "sent_emails": 0,
            "errors": 0,
            "skipped": 0,
        }
        
        # Get pending schedules due now
        schedules = await self.repository.get_pending_schedules_due_now()
        
        for schedule in schedules:
            try:
                stats["processed"] += 1
                
                # Get document
                document = await self.repository.get_document_by_id(schedule.document_id)
                if not document or document.is_del:
                    # Document not found or deleted - skip
                    stats["skipped"] += 1
                    # Mark schedule as cancelled
                    schedule.status = "cancelled"
                    await self.session.commit()
                    continue
                
                # Check if family is soft-deleted
                family_result = await self.session.execute(
                    select(Family)
                    .where(
                        Family.id == document.family_id,
                        Family.is_del == False,
                    )
                )
                family = family_result.scalar_one_or_none()
                if not family:
                    # Family deleted - skip
                    stats["skipped"] += 1
                    schedule.status = "cancelled"
                    await self.session.commit()
                    continue
                
                # Get user
                user_result = await self.session.execute(
                    select(User)
                    .where(
                        User.id == schedule.user_id,
                        User.is_del == False,
                    )
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    # User not found or deleted - skip
                    stats["skipped"] += 1
                    schedule.status = "cancelled"
                    await self.session.commit()
                    continue
                
                # Validate user role (Owner or FamilyAdmin)
                # Check if user is owner
                is_owner = document.owner_id == user.id
                
                # Check if user is FamilyAdmin in document's family
                from src.roles.models import UserRole, Role
                familyadmin_result = await self.session.execute(
                    select(UserRole)
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        UserRole.user_id == user.id,
                        UserRole.family_id == document.family_id,
                        Role.name == "familyadmin",
                        UserRole.is_del == False,
                        UserRole.deleted_at.is_(None),
                    )
                )
                is_familyadmin = familyadmin_result.scalar_one_or_none() is not None
                
                if not (is_owner or is_familyadmin):
                    # User is not eligible - skip
                    stats["skipped"] += 1
                    schedule.status = "cancelled"
                    await self.session.commit()
                    continue
                
                # Create InAppNotification
                notification = await self.create_in_app_notification(
                    document_id=schedule.document_id,
                    user_id=schedule.user_id,
                    reminder_type=schedule.reminder_type,
                )
                stats["created_notifications"] += 1
                
                # Send email
                email_sent = await self.send_expiry_email(
                    user=user,
                    document=document,
                    reminder_type=schedule.reminder_type,
                )
                if email_sent:
                    stats["sent_emails"] += 1
                
                # Mark schedule as sent
                await self.repository.mark_schedule_as_sent(schedule.id)
                
            except Exception as e:
                # Log error but continue processing other schedules
                stats["errors"] += 1
                print(f"Error processing reminder schedule {schedule.id}: {str(e)}")
                # Mark schedule as cancelled to prevent retry loops
                try:
                    schedule.status = "cancelled"
                    await self.session.commit()
                except Exception:
                    pass
        
        return stats

