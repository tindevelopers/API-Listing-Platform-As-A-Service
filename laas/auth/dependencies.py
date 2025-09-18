"""
Authentication dependencies for FastAPI
"""

from typing import Any, Callable, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from laas.auth.jwt_handler import verify_token
from laas.auth.rbac import Permission, has_permission
from laas.database.connection import get_db
from laas.database.models import User

# Security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""

    # Verify token
    try:
        payload = verify_token(credentials.credentials)
        user_id: Optional[str] = payload.get("sub")
        tenant_id: Optional[str] = payload.get("tenant_id")

        if user_id is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = (
        db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set tenant context for database queries
    request.state.tenant_id = tenant_id
    request.state.user_id = user_id

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current verified user"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_permission_dependency(permission: Permission) -> Callable[[], Any]:
    """Create a dependency that requires a specific permission"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required",
            )
        return current_user

    return permission_checker


def require_any_permission_dependency(
    permissions: List[Permission],
) -> Callable[[], Any]:
    """Create a dependency that requires any of the specified permissions"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not any(has_permission(current_user, perm) for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "One of the following permissions required: "
                    f"{[p.value for p in permissions]}"
                ),
            )
        return current_user

    return permission_checker


def require_all_permissions_dependency(
    permissions: List[Permission],
) -> Callable[[], Any]:
    """Create a dependency that requires all of the specified permissions"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not all(has_permission(current_user, perm) for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "All of the following permissions required: "
                    f"{[p.value for p in permissions]}"
                ),
            )
        return current_user

    return permission_checker


# Common permission dependencies
RequireAdmin = require_permission_dependency(Permission.MANAGE_USERS)
RequireListingManagement = require_permission_dependency(Permission.MANAGE_LISTINGS)
RequireSchemaManagement = require_permission_dependency(Permission.MANAGE_SCHEMAS)
RequireAnalytics = require_permission_dependency(Permission.VIEW_ANALYTICS)
RequireSystemManagement = require_permission_dependency(Permission.MANAGE_SYSTEM)
