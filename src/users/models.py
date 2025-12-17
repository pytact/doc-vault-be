"""User models."""
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from src.database import Base


class User(Base):
    """User model for user accounts with invite/activation workflow."""
    
    __tablename__ = "users"
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    
    # Business Fields
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    hash_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    
    # Invite Workflow Fields
    invite_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    invite_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invite_expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invited_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Password Reset Workflow Fields
    reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    reset_token_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Soft Delete Fields
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
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    deleted_by: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    # Note: Self-referential relationships for audit fields
    # invited_by_user: relationship to User who sent invitation
    # created_by_user: relationship to User who created this record
    # updated_by_user: relationship to User who last updated this record
    # deleted_by_user: relationship to User who soft-deleted this record
    # These relationships are optional and may not be needed for basic operations
    
    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'inactive')",
            name="ck_users_status_valid"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"
