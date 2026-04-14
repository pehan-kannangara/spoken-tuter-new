"""
Auth API Schemas - Pydantic models for authentication endpoints
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    role: Literal["learner", "teacher", "recruiter", "admin"] = Field(
        default="learner",
        description="User role"
    )
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: str
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token TTL in seconds")
    user: UserResponse = Field(..., description="Authenticated user data")


class SimpleTokenResponse(BaseModel):
    """Simple token response for refresh endpoint"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token TTL in seconds")


class VerifyTokenResponse(BaseModel):
    """Response schema for token verification"""
    valid: bool = Field(..., description="Token validity")
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error code or message")
    detail: Optional[str] = None
    status_code: int = Field(..., description="HTTP status code")
