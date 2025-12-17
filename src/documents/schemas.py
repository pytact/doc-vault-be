"""Document schemas."""
from uuid import UUID
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.schemas import PagedCollection


# ==================== Request Schemas ====================

class DocumentCreate(BaseModel):
    """Document create request schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    category_id: UUID = Field(..., description="Category ID (UUID)")
    subcategory_id: UUID = Field(..., description="Subcategory ID (UUID)")
    expiry_date: Optional[date] = Field(None, description="Optional expiry date (ISO 8601 format YYYY-MM-DD). Omit this field if not needed.")
    details_json: Optional[dict] = Field(None, description="Optional free-form metadata (JSON object). Omit this field if not needed, or send null.")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    """Document update request schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Document title")
    category_id: Optional[UUID] = Field(None, description="Category ID (UUID)")
    subcategory_id: Optional[UUID] = Field(None, description="Subcategory ID (UUID)")
    expiry_date: Optional[date] = Field(None, description="Optional expiry date (ISO 8601 format YYYY-MM-DD). Use null to clear expiry date")
    details_json: Optional[dict] = Field(None, description="Free-form metadata (JSON object). Use null to clear details")
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Query Schemas ====================

class DocumentListQuery(BaseModel):
    """Query schema for listing documents with pagination and filtering."""
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    category_id: Optional[UUID] = Field(None, description="Filter by category ID (exact match)")
    subcategory_id: Optional[UUID] = Field(None, description="Filter by subcategory ID (exact match)")
    owner_user_id: Optional[UUID] = Field(None, description="Filter by owner user ID (exact match)")
    expiry_date: Optional[date] = Field(None, description="Filter by expiry date (ISO 8601 format YYYY-MM-DD)")
    search: Optional[str] = Field(None, description="Search by title + category/subcategory names (case-insensitive partial match). details_json is NOT searchable")
    sort_by: str = Field("created_at", description="Sort field: created_at, updated_at, title, expiry_date")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentFileQuery(BaseModel):
    """Query schema for document file preview/download."""
    mode: str = Field("preview", description="File access mode: preview or download")
    
    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate file access mode."""
        if v not in ["preview", "download"]:
            raise ValueError("mode must be 'preview' or 'download'")
        return v
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Response Schemas ====================

class DocumentRead(BaseModel):
    """Document read response schema."""
    id: UUID
    family_id: UUID
    owner_user_id: UUID = Field(..., alias="owner_id")  # Map owner_id to owner_user_id
    title: str
    category_id: UUID
    subcategory_id: UUID
    expiry_date: Optional[date] = None
    details_json: Optional[dict] = Field(None, alias="details")  # Map details to details_json
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_del: bool
    created_at: datetime
    updated_at: Optional[datetime] = None  # Optional per RULE 8.3.5
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    permission: Optional[str] = None  # "owner", "editor", "viewer" - computed field
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both owner_id and owner_user_id
    )


class DocumentPaginatedResponse(PagedCollection[DocumentRead]):
    """Paginated document response schema."""
    next_page: Optional[str] = None
    prev_page: Optional[str] = None


# ==================== File Upload Response Schemas ====================

class FileUploadResponse(BaseModel):
    """File upload response schema."""
    file_path: str
    file_url: Optional[str] = None  # Optional CDN URL
    file_size: int
    content_type: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Document Assignment Request Schemas ====================

class AssignmentItem(BaseModel):
    """Single assignment item in bulk request."""
    user_id: UUID = Field(..., description="User ID to assign access to")
    access_type: str = Field(..., description="Access type: viewer or editor")
    
    @field_validator("access_type")
    @classmethod
    def validate_access_type(cls, v: str) -> str:
        """Validate access type."""
        # Strip whitespace
        v = v.strip() if isinstance(v, str) else v
        
        # Check for empty string
        if not v:
            raise ValueError("access_type cannot be empty. Must be 'viewer' or 'editor'")
        
        # Validate allowed values
        if v not in ["viewer", "editor"]:
            raise ValueError(f"access_type must be 'viewer' or 'editor', got '{v}'")
        return v
    
    model_config = ConfigDict(from_attributes=True)


class DocumentAssignmentCreate(BaseModel):
    """Request schema for creating document assignments."""
    assignments: list[AssignmentItem] = Field(..., min_length=1, max_length=100, description="Array of assignment objects")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentAssignmentUpdate(BaseModel):
    """Request schema for updating a document assignment."""
    access_type: str = Field(..., description="Access type: viewer or editor")
    
    @field_validator("access_type")
    @classmethod
    def validate_access_type(cls, v: str) -> str:
        """Validate access type."""
        # Strip whitespace
        v = v.strip() if isinstance(v, str) else v
        
        # Check for empty string
        if not v:
            raise ValueError("access_type cannot be empty. Must be 'viewer' or 'editor'")
        
        # Validate allowed values
        if v not in ["viewer", "editor"]:
            raise ValueError(f"access_type must be 'viewer' or 'editor', got '{v}'")
        return v
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Document Assignment Query Schemas ====================

class DocumentAssignmentListQuery(BaseModel):
    """Query schema for listing document assignments with pagination and filtering."""
    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    access_type: Optional[str] = Field(None, description="Filter by access type: viewer, editor")
    sort_by: str = Field("assigned_at", description="Sort field: assigned_at, updated_at, access_type")
    sort_order: str = Field("desc", description="Sort order: asc or desc")
    
    @field_validator("access_type")
    @classmethod
    def validate_access_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate access type filter."""
        if v is not None and v not in ["viewer", "editor"]:
            raise ValueError("access_type must be 'viewer' or 'editor'")
        return v
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort field."""
        if v not in ["assigned_at", "updated_at", "access_type"]:
            raise ValueError("sort_by must be 'assigned_at', 'updated_at', or 'access_type'")
        return v
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Document Assignment Response Schemas ====================

class UserSummary(BaseModel):
    """User summary for assignment response."""
    id: UUID
    name: str  # Using email as name (User model doesn't have name field)
    email: str
    family_id: UUID
    status: str  # "Active", "PendingActivation", "SoftDeleted" (API format)
    
    model_config = ConfigDict(from_attributes=True)


class DocumentAssignmentRead(BaseModel):
    """Document assignment response schema."""
    id: UUID
    document_id: UUID
    assign_to_user_id: UUID = Field(..., alias="assign_to")  # Map assign_to to assign_to_user_id
    owner_id: UUID
    user: UserSummary
    access_type: str  # "viewer" or "editor"
    assigned_at: datetime = Field(..., alias="created_at")  # Map created_at to assigned_at
    updated_at: datetime
    is_del: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both assign_to and assign_to_user_id
    )


class DocumentAssignmentPaginatedResponse(PagedCollection[DocumentAssignmentRead]):
    """Paginated assignment response schema."""
    next_page: Optional[str] = None
    prev_page: Optional[str] = None


class BulkAssignmentResponse(BaseModel):
    """Response schema for bulk assignment creation."""
    created: list[DocumentAssignmentRead] = Field(default_factory=list, description="Newly created assignments")
    updated: list[DocumentAssignmentRead] = Field(default_factory=list, description="Updated assignments")
    failed: list[dict] = Field(default_factory=list, description="Failed assignments with error details")
    
    model_config = ConfigDict(from_attributes=True)
