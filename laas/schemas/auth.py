"""
Authentication schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

from laas.auth.rbac import UserRole


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserRegister(UserBase):
    """User registration schema"""

    password: str
    tenant_id: str
    role: Optional[UserRole] = UserRole.USER

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """User login schema"""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""

    id: str
    tenant_id: str
    role: str
    status: str
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    """Password reset request schema"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
