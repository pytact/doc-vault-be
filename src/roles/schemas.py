"""Role schemas."""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoleRead(BaseModel):
    """Response schema for role."""
    id: UUID
    name: str
    permissions: dict  # JSON permission blob
    
    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    """Response schema for role list."""
    items: list[RoleRead]
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdateRequest(BaseModel):
    """Request schema for updating user roles."""
    role_ids: list[UUID] = Field(..., description="Array of role IDs to assign (must contain exactly one role ID)", min_length=0)
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleSummary(BaseModel):
    """Role summary in user role update response."""
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdateResponse(BaseModel):
    """Response schema for user role update."""
    user_id: UUID
    family_id: UUID
    roles: list[UserRoleSummary]  # List of assigned roles (single role per user)
    
    model_config = ConfigDict(from_attributes=True)
