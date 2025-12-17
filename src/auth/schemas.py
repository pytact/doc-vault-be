"""Authentication schemas."""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    """User information in login response."""
    id: UUID
    email: str
    name: str  # Note: User model may need name field, using email as fallback
    role: str
    family_id: Optional[UUID] = None
    family_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Login response schema."""
    token: str
    expires_in: int
    user: UserInfo
    
    model_config = ConfigDict(from_attributes=True)


class LogoutResponse(BaseModel):
    """Logout response schema (no data)."""
    pass


class TokenRequest(BaseModel):
    """OAuth2-compatible token request schema (uses Form fields)."""
    username: str = Field(..., description="Username (email address) for OAuth2 compatibility")
    password: str = Field(..., description="User password")
    
    model_config = ConfigDict(from_attributes=True)
