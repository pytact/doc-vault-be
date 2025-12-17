"""Notification models for expiry reminder system."""
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from src.database import Base


class ReminderSchedule(Base):
    """ReminderSchedule model for storing scheduled reminders (30d, 7d, 0d) per document-user pair.
    
    Created when document expiry_date is set, processed by daily scheduler at 00:00 UTC.
    """
    
    __tablename__ = "reminder_schedules"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # Foreign Keys
    document_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Business Fields
    reminder_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )
    send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    
    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    
    # Table-level constraints
    __table_args__ = (
        # Partial unique index: (document_id, user_id, reminder_type) WHERE status = 'pending'
        # Ensures only one pending schedule per (document, user, type)
        Index(
            "uq_reminder_schedules_document_user_type_pending",
            "document_id",
            "user_id",
            "reminder_type",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        # CHECK constraint on reminder_type: Must be one of: '30d', '7d', '0d'
        CheckConstraint(
            "reminder_type IN ('30d', '7d', '0d')",
            name="ck_reminder_schedules_reminder_type_valid"
        ),
        # CHECK constraint on status: Must be one of: 'pending', 'sent', 'cancelled'
        CheckConstraint(
            "status IN ('pending', 'sent', 'cancelled')",
            name="ck_reminder_schedules_status_valid"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ReminderSchedule(id={self.id}, document_id={self.document_id}, user_id={self.user_id}, reminder_type={self.reminder_type}, status={self.status})>"


class InAppNotification(Base):
    """InAppNotification model for storing user-visible notifications with read/unread state.
    
    Created by scheduler when reminder schedule is processed. Auto-expires after 90 days via is_del flag.
    """
    
    __tablename__ = "in_app_notifications"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Business Fields
    reminder_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_del: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    
    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    
    # Table-level constraints
    __table_args__ = (
        # CHECK constraint on reminder_type: Must be one of: '30d', '7d', '0d'
        CheckConstraint(
            "reminder_type IN ('30d', '7d', '0d')",
            name="ck_in_app_notifications_reminder_type_valid"
        ),
        # No unique constraint: User can have multiple notifications for the same document
        # (different reminder types or multiple expiry_date changes)
    )
    
    def __repr__(self) -> str:
        return f"<InAppNotification(id={self.id}, user_id={self.user_id}, document_id={self.document_id}, reminder_type={self.reminder_type}, is_del={self.is_del})>"

