"""
JWT token handling and management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, status

from laas.core.config import get_settings
from laas.database.models import User


class AuthManager:
    """JWT authentication manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = self.settings.jwt_algorithm
        self.access_token_expire_minutes = self.settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.jwt_refresh_token_expire_days
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.refresh_token_expire_days
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_token_pair(self, user: User) -> Dict[str, str]:
        """Create both access and refresh tokens for a user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "role": user.role,
            "permissions": user.permissions or []
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


# Global auth manager instance
auth_manager = AuthManager()


def create_access_token(data: Dict[str, Any]) -> str:
    """Create access token"""
    return auth_manager.create_access_token(data)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token"""
    return auth_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify token"""
    return auth_manager.verify_token(token, token_type)
