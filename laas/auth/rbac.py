"""
Role-Based Access Control (RBAC) system
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Set

from fastapi import HTTPException, status

from laas.database.models import User, UserRole


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
    UserRole.ADMIN: {
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
    user_role = UserRole(user.role) if isinstance(user.role, str) else user.role
    if user_role in ROLE_PERMISSIONS:
        permissions.update(ROLE_PERMISSIONS[user_role])

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


def require_permission(permission: Permission) -> Callable[[Any], Any]:
    """Decorator to require a specific permission"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def require_any_permission(permissions: List[Permission]) -> Callable[[Any], Any]:
    """Decorator to require any of the specified permissions"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_any_permission(user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "One of the following permissions required: "
                        f"{[p.value for p in permissions]}"
                    ),
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(permissions: List[Permission]) -> Callable[[Any], Any]:
    """Decorator to require all of the specified permissions"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not has_all_permissions(user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "All of the following permissions required: "
                        f"{[p.value for p in permissions]}"
                    ),
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_superadmin(user: User) -> bool:
    """Check if user is a superadmin"""
    return str(user.role) == UserRole.SUPERADMIN.value


def is_tenant_admin(user: User) -> bool:
    """Check if user is a tenant admin"""
    return str(user.role) == UserRole.ADMIN.value


def is_admin(user: User) -> bool:
    """Check if user is any type of admin"""
    return str(user.role) in [UserRole.SUPERADMIN.value, UserRole.ADMIN.value]


def can_manage_tenant(user: User, tenant_id: str) -> bool:
    """Check if user can manage a specific tenant"""
    if is_superadmin(user):
        return True

    if is_tenant_admin(user) and str(user.tenant_id) == tenant_id:
        return True

    return False
