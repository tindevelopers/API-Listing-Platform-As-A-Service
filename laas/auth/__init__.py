"""
Authentication and authorization package for LAAS Platform
"""

from .jwt_handler import AuthManager, create_access_token, verify_token
from .rbac import Permission, UserRole, has_permission, get_user_permissions
from .dependencies import get_current_user, get_current_active_user, require_permission
from .password import PasswordManager

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
    "PasswordManager"
]
