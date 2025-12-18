"""Dashboard schemas."""
from pydantic import BaseModel, Field, ConfigDict


# ==================== Analytics Dashboard Schemas ====================

class AnalyticsDashboardResponse(BaseModel):
    """Response schema for analytics dashboard."""
    total_families: int = Field(..., ge=0, description="Total number of families (including soft-deleted)")
    total_users: int = Field(..., ge=0, description="Total number of users (including soft-deleted)")
    total_documents: int = Field(..., ge=0, description="Total number of documents (including soft-deleted)")
    active_families: int = Field(..., ge=0, description="Number of active (non-soft-deleted) families")
    active_users: int = Field(..., ge=0, description="Number of active (non-soft-deleted) users")
    soft_deleted_families: int = Field(..., ge=0, description="Number of soft-deleted families")
    soft_deleted_users: int = Field(..., ge=0, description="Number of soft-deleted users")
    
    model_config = ConfigDict(from_attributes=True)

