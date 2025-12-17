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


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr = Field(..., description="User email address")
    
    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequestResponse(BaseModel):
    """Password reset request response schema."""
    message: str = Field(..., description="Success message")
    
    model_config = ConfigDict(from_attributes=True)


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    reset_token: str = Field(..., description="Password reset token from email")
    password: str = Field(..., min_length=12, description="New password (minimum 12 characters)")
    
    model_config = ConfigDict(from_attributes=True)


class PasswordResetConfirmResponse(BaseModel):
    """Password reset confirmation response schema."""
    message: str = Field(..., description="Success message")
    
    model_config = ConfigDict(from_attributes=True)
