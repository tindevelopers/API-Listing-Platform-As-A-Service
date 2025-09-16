"""
Role-Based Access Control (RBAC) system
"""

from enum import Enum
from functools import wraps
from typing import Dict, List, Optional, Set

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from laas.database.connection import get_db
from laas.database.models import User


class UserRole(str, Enum):
    """User roles in the system"""

    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    GUEST = "guest"


class Permission(str, Enum):
    """System permissions"""

    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"

    # Listing management
    MANAGE_LISTINGS = "manage_listings"
    VIEW_LISTINGS = "view_listings"
    CREATE_LISTINGS = "create_listings"
    UPDATE_LISTINGS = "update_listings"
    DELETE_LISTINGS = "delete_listings"
    PUBLISH_LISTINGS = "publish_listings"

    # Schema management
    MANAGE_SCHEMAS = "manage_schemas"
    VIEW_SCHEMAS = "view_schemas"
    CREATE_SCHEMAS = "create_schemas"
    UPDATE_SCHEMAS = "update_schemas"
    DELETE_SCHEMAS = "delete_schemas"

    # Tenant management
    MANAGE_TENANT = "manage_tenant"
    VIEW_TENANT = "view_tenant"
    UPDATE_TENANT = "update_tenant"

    # Analytics and reporting
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    # System administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPERADMIN: {
        # Superadmin has all permissions
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_LISTINGS,
        Permission.VIEW_LISTINGS,
        Permission.CREATE_LISTINGS,
        Permission.UPDATE_LISTINGS,
        Permission.DELETE_LISTINGS,
        Permission.PUBLISH_LISTINGS,
        Permission.MANAGE_SCHEMAS,
        Permission.VIEW_SCHEMAS,
        Permission.CREATE_SCHEMAS,
        Permission.UPDATE_SCHEMAS,
        Permission.DELETE_SCHEMAS,
        Permission.MANAGE_TENANT,
        Permission.VIEW_TENANT,
        Permission.UPDATE_TENANT,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_LOGS,
        Permission.MANAGE_INTEGRATIONS,
    },
    UserRole.TENANT_ADMIN: {
        # Tenant admin has most permissions within their tenant
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_LISTINGS,
        Permission.VIEW_LISTINGS,
        Permission.CREATE_LISTINGS,
        Permission.UPDATE_LISTINGS,
        Permission.DELETE_LISTINGS,
        Permission.PUBLISH_LISTINGS,
        Permission.MANAGE_SCHEMAS,
        Permission.VIEW_SCHEMAS,
        Permission.CREATE_SCHEMAS,
        Permission.UPDATE_SCHEMAS,
        Permission.DELETE_SCHEMAS,
        Permission.VIEW_TENANT,
        Permission.UPDATE_TENANT,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.VIEW_LOGS,
        Permission.MANAGE_INTEGRATIONS,
    },
    UserRole.USER: {
        # Regular users have basic permissions
        Permission.VIEW_LISTINGS,
        Permission.CREATE_LISTINGS,
        Permission.UPDATE_LISTINGS,
        Permission.DELETE_LISTINGS,
        Permission.VIEW_SCHEMAS,
    },
    UserRole.GUEST: {
        # Guests have read-only permissions
        Permission.VIEW_LISTINGS,
        Permission.VIEW_SCHEMAS,
    },
}


def get_user_permissions(user: User) -> Set[Permission]:
    """Get all permissions for a user based on their role and custom permissions"""
    permissions = set()

    # Add role-based permissions
    if user.role in ROLE_PERMISSIONS:
        permissions.update(ROLE_PERMISSIONS[user.role])

    # Add custom permissions if any
    if user.permissions:
        for perm in user.permissions:
            try:
                permissions.add(Permission(perm))
            except ValueError:
                # Skip invalid permissions
                continue

    return permissions


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all of the specified permissions"""
    user_permissions = get_user_permissions(user)
    return all(perm in user_permissions for perm in permissions)


def require_permission(permission: Permission):
    """Decorator to require a specific permission"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or dependencies
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission.value}' required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_any_permission(user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of the following permissions required: {[p.value for p in permissions]}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(permissions: List[Permission]):
    """Decorator to require all of the specified permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_all_permissions(user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"All of the following permissions required: {[p.value for p in permissions]}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_superadmin(user: User) -> bool:
    """Check if user is a superadmin"""
    return user.role == UserRole.SUPERADMIN


def is_tenant_admin(user: User) -> bool:
    """Check if user is a tenant admin"""
    return user.role == UserRole.TENANT_ADMIN


def is_admin(user: User) -> bool:
    """Check if user is any type of admin"""
    return user.role in [UserRole.SUPERADMIN, UserRole.TENANT_ADMIN]


def can_manage_tenant(user: User, tenant_id: str) -> bool:
    """Check if user can manage a specific tenant"""
    if is_superadmin(user):
        return True

    if is_tenant_admin(user) and str(user.tenant_id) == tenant_id:
        return True

    return False
