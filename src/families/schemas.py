"""Family schemas."""
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.schemas import PagedCollection


class FamilyCreate(BaseModel):
    """Family create request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Family name")
    
    model_config = ConfigDict(from_attributes=True)


class FamilyUpdate(BaseModel):
    """Family update request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Family name")
    
    model_config = ConfigDict(from_attributes=True)


class FamilyListQuery(BaseModel):
    """Query schema for listing families with pagination and filtering."""
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    status: Optional[str] = Field(None, description="Filter by status: Active, SoftDeleted")
    sort_by: str = Field("created_at", description="Sort field: name, created_at, status")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


class FamilyRead(BaseModel):
    """Family read response schema."""
    id: UUID
    name: str
    status: str  # "Active" or "SoftDeleted" (API format)
    is_del: bool
    created_at: datetime
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class FamilyPaginatedResponse(PagedCollection[FamilyRead]):
    """Paginated family response schema."""
    next_page: Optional[str] = None
    prev_page: Optional[str] = None
