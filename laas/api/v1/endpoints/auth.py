"""
Authentication endpoints
"""

from datetime import timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from laas.database.connection import get_db
from laas.database.models import User
from laas.auth.jwt_handler import auth_manager
from laas.auth.password import PasswordManager
from laas.auth.dependencies import get_current_user
from laas.schemas.auth import (
    UserLogin, UserRegister, TokenResponse, UserResponse, 
    PasswordReset, PasswordResetConfirm
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.tenant_id == user_data.tenant_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    password_validation = PasswordManager.validate_password_strength(user_data.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet requirements",
                "errors": password_validation["errors"]
            }
        )
    
    # Create new user
    hashed_password = PasswordManager.get_password_hash(user_data.password)
    
    new_user = User(
        tenant_id=user_data.tenant_id,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role or "user",
        status="active",
        email_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    
    # Get user by email
    user = db.query(User).filter(
        User.email == form_data.username,
        User.status == "active"
    ).first()
    
    if not user or not PasswordManager.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = auth_manager.create_token_pair(user)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    payload = auth_manager.verify_token(refresh_token, "refresh")
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id,
        User.status == "active"
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    tokens = auth_manager.create_token_pair(user)
    
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify old password
    if not PasswordManager.verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Validate new password
    password_validation = PasswordManager.validate_password_strength(new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "New password does not meet requirements",
                "errors": password_validation["errors"]
            }
        )
    
    # Update password
    current_user.password_hash = PasswordManager.get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    
    # Check if user exists
    user = db.query(User).filter(
        User.email == email,
        User.status == "active"
    ).first()
    
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # TODO: Send password reset email
    # For now, just return success message
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    
    # TODO: Verify reset token
    # For now, just validate password and update
    
    # Validate new password
    password_validation = PasswordManager.validate_password_strength(reset_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet requirements",
                "errors": password_validation["errors"]
            }
        )
    
    # TODO: Get user from reset token
    # For now, return success message
    
    return {"message": "Password reset successfully"}
