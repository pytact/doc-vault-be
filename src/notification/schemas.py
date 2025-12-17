"""Notification schemas for expiry reminder system."""
from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from src.schemas import PagedCollection


# ==================== Query Schemas ====================

class NotificationListQuery(BaseModel):
    """Query schema for listing notifications with pagination and sorting."""
    
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    sort_by: str = Field("created_at", description="Sort field: created_at (only allowed value)")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Request Schemas ====================

class NotificationStatusUpdateRequest(BaseModel):
    """Request schema for updating notification read status."""
    
    is_read: bool = Field(..., description="Set to true to mark as read, false to mark as unread")
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Response Schemas ====================

class NotificationRead(BaseModel):
    """Notification read response schema."""
    
    id: UUID
    document_id: UUID
    document_title: str = Field(..., min_length=1, max_length=255)
    expiry_date: Optional[date] = None
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: str = Field(..., min_length=1, max_length=100)
    document_link: str = Field(..., description="Relative URL format: /v1/documents/{document_id}")
    reminder_type: str = Field(..., description="Enum: 30d, 7d, 0d (case-sensitive)")
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_read: bool
    
    model_config = ConfigDict(from_attributes=True)


class NotificationPaginatedResponse(PagedCollection[NotificationRead]):
    """Paginated notification response."""
    
    next_page: Optional[str] = Field(None, description="URL for next page (or null)")
    prev_page: Optional[str] = Field(None, description="URL for previous page (or null)")
    
    model_config = ConfigDict(from_attributes=True)


class NotificationMarkReadResponse(BaseModel):
    """Response schema for marking notification as read/unread."""
    
    id: UUID
    read_at: Optional[datetime] = Field(None, description="Timestamp when marked as read, null if unread")
    is_read: bool = Field(..., description="Current read status")
    
    model_config = ConfigDict(from_attributes=True)


class NotificationMarkAllReadResponse(BaseModel):
    """Response schema for marking all notifications as read."""
    
    marked_count: int = Field(..., ge=0, description="Number of notifications marked as read")
    
    model_config = ConfigDict(from_attributes=True)


class UpcomingExpiryItem(BaseModel):
    """Upcoming expiry item schema for dashboard widget."""
    
    document_id: UUID
    document_title: str = Field(..., min_length=1, max_length=255)
    expiry_date: date
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: str = Field(..., min_length=1, max_length=100)
    days_until_expiry: int = Field(..., ge=0, le=30, description="Number of days until expiry (0-30)")
    
    model_config = ConfigDict(from_attributes=True)


class UpcomingExpiriesResponse(BaseModel):
    """Response schema for upcoming expiries."""
    
    upcoming_expiries: list[UpcomingExpiryItem]
    
    model_config = ConfigDict(from_attributes=True)

