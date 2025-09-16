"""
Authentication and authorization package for LAAS Platform
"""

from .dependencies import get_current_active_user, get_current_user
from .jwt_handler import AuthManager, create_access_token, verify_token
from .password import PasswordManager
from .rbac import (
    Permission,
    UserRole,
    get_user_permissions,
    has_permission,
    require_permission,
)

__all__ = [
    "AuthManager",
    "create_access_token",
    "verify_token",
    "Permission",
    "UserRole",
    "has_permission",
    "get_user_permissions",
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    "PasswordManager",
]
