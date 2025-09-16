"""
Configuration management for LAAS Platform
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "LAAS Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Security
    secret_key: str
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]

    # File Upload
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
    ]

    # Business Configuration
    default_page_size: int = 20
    max_page_size: int = 100
    default_search_radius: int = 25  # miles

    # Google Cloud
    google_cloud_project_id: Optional[str] = None
    google_cloud_region: str = "us-central1"

    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    log_format: str = "json"

    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("allowed_hosts", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("allowed_file_types", pre=True)
    def assemble_file_types(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
