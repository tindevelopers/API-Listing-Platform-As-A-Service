"""
Configuration management for LAAS Platform
"""

from functools import lru_cache
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "LAAS Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = Field(default="sqlite:///./test.db", alias="DATABASE_URL")
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_pool_size: int = 10

    # JWT
    jwt_secret_key: str = Field(default="test-secret-key", alias="JWT_SECRET_KEY")
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
    secret_key: str = Field(default="test-secret-key", alias="SECRET_KEY")
    allowed_hosts: List[str] = [
        "localhost",
        "127.0.0.1",
        "testserver",
        "*.run.app",
        "*.a.run.app",
    ]

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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_file_types(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
