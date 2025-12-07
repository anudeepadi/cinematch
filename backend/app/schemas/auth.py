from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for access token response"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: int
    exp: datetime
    iat: datetime


class AuthResponse(BaseModel):
    """Schema for authentication response with user info"""
    access_token: str
    token_type: str = "bearer"
    user: "UserBasicResponse"


class UserBasicResponse(BaseModel):
    """Basic user info for auth response"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool

    class Config:
        from_attributes = True


# Update forward reference
AuthResponse.model_rebuild()
