"""
Password management utilities
"""

from typing import Any, Dict, List

from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordManager:
    """Password management utilities"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return validation result"""
        result: Dict[str, Any] = {"is_valid": True, "errors": [], "score": 0}
        errors: List[str] = []

        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
            result["is_valid"] = False

        # Character variety checks
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not has_upper:
            errors.append(
                "Password must contain at least one uppercase letter"
            )
            result["is_valid"] = False

        if not has_lower:
            errors.append(
                "Password must contain at least one lowercase letter"
            )
            result["is_valid"] = False

        if not has_digit:
            errors.append("Password must contain at least one digit")
            result["is_valid"] = False

        if not has_special:
            errors.append(
                "Password must contain at least one special character"
            )
            result["is_valid"] = False

        # Calculate strength score
        score = 0
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if has_upper:
            score += 1
        if has_lower:
            score += 1
        if has_digit:
            score += 1
        if has_special:
            score += 1

        result["score"] = score
        result["errors"] = errors

        return result
