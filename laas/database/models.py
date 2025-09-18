"""
Database models for LAAS Platform
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass



# Enums
class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Association tables
listing_categories = Table(
    "listing_categories",
    Base.metadata,
    Column(
        "listing_id", UUID(as_uuid=True), ForeignKey("listings.id"), primary_key=True
    ),
    Column(
        "category_id", UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

listing_tags = Table(
    "listing_tags",
    Base.metadata,
    Column(
        "listing_id", UUID(as_uuid=True), ForeignKey("listings.id"), primary_key=True
    ),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

user_favorites = Table(
    "user_favorites",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column(
        "listing_id", UUID(as_uuid=True), ForeignKey("listings.id"), primary_key=True
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class Tenant(Base):
    """Multi-tenant organization model"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=False)  # real_estate, healthcare, etc.

    # Status and plan information
    status = Column(String(50), default="active", nullable=False)
    plan = Column(String(50), default="starter", nullable=False)

    # Configuration
    settings = Column(JSON, default=dict)
    branding = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    listings = relationship(
        "Listing", back_populates="tenant", cascade="all, delete-orphan"
    )
    industry_schemas = relationship(
        "IndustrySchema", back_populates="tenant", cascade="all, delete-orphan"
    )
    categories = relationship(
        "Category", back_populates="tenant", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey", back_populates="tenant", cascade="all, delete-orphan"
    )
    analytics = relationship(
        "Analytics", back_populates="tenant", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_tenant_subdomain", "subdomain"),
        Index("idx_tenant_industry", "industry"),
        Index("idx_tenant_status", "status"),
    )


class User(Base):
    """User model with tenant isolation"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Authentication
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    permissions = Column(JSON, default=list)

    # Status
    status = Column(String(50), default="active", nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    listings = relationship(
        "Listing", back_populates="owner", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan",
        foreign_keys="Review.user_id"
    )
    favorites = relationship(
        "Listing", secondary=user_favorites, back_populates="favorited_by"
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    moderated_reviews = relationship(
        "Review", back_populates="moderator", 
        foreign_keys="Review.moderated_by"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("idx_user_tenant_id", "tenant_id"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
        Index("idx_user_status", "status"),
    )


class IndustrySchema(Base):
    """Industry-specific schema definitions"""

    __tablename__ = "industry_schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Schema information
    industry = Column(String(100), nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Schema definition
    fields = Column(JSON, nullable=False)  # List of field definitions
    searchable_fields = Column(JSON, default=list)
    required_fields = Column(JSON, default=list)
    business_rules = Column(JSON, default=dict)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="industry_schemas")
    listings = relationship("Listing", back_populates="schema")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "industry", "version", name="uq_schema_tenant_industry_version"
        ),
        Index("idx_schema_tenant_id", "tenant_id"),
        Index("idx_schema_industry", "industry"),
        Index("idx_schema_active", "is_active"),
    )


class Listing(Base):
    """Generic listing model with dynamic fields"""

    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    schema_id = Column(
        UUID(as_uuid=True), ForeignKey("industry_schemas.id"), nullable=False
    )

    # Core listing information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(255), nullable=False)

    # Dynamic fields (industry-specific)
    data = Column(JSON, default=dict)  # All custom fields stored here

    # Location information
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)

    # Status and visibility
    status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)

    # Pricing (if applicable)
    price = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    # Metadata
    listing_metadata = Column(JSON, default=dict)

    # Search optimization (PostgreSQL TSVECTOR, SQLite TEXT)
    search_vector = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="listings")
    owner = relationship("User", back_populates="listings")
    schema = relationship("IndustrySchema", back_populates="listings")
    categories = relationship(
        "Category", secondary=listing_categories, back_populates="listings"
    )
    tags = relationship("Tag", secondary=listing_tags, back_populates="listings")
    media = relationship(
        "Media", back_populates="listing", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="listing", cascade="all, delete-orphan"
    )
    favorited_by = relationship(
        "User", secondary=user_favorites, back_populates="favorites"
    )
    analytics = relationship(
        "ListingAnalytics", back_populates="listing", cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_listing_tenant_slug"),
        Index("idx_listing_tenant_id", "tenant_id"),
        Index("idx_listing_owner_id", "owner_id"),
        Index("idx_listing_schema_id", "schema_id"),
        Index("idx_listing_status", "status"),
        Index("idx_listing_public", "is_public"),
        Index("idx_listing_verified", "is_verified"),
        Index("idx_listing_location", "latitude", "longitude"),
        Index("idx_listing_city_state", "city", "state"),
        Index("idx_listing_created_at", "created_at"),
        Index("idx_listing_published_at", "published_at"),
    )


class AuditLog(Base):
    """Audit logging for compliance and debugging"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Action information
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(100), nullable=False)  # listing, user, tenant, etc.
    resource_id = Column(String(255), nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)

    # Change details
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_audit_tenant_id", "tenant_id"),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created_at", "created_at"),
    )


class Category(Base):
    """Category model for organizing listings"""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Category information
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    # Hierarchy
    level = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    listings = relationship(
        "Listing", secondary=listing_categories, back_populates="categories"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_category_tenant_slug"),
        Index("idx_category_tenant_id", "tenant_id"),
        Index("idx_category_parent_id", "parent_id"),
        Index("idx_category_active", "is_active"),
        Index("idx_category_level", "level"),
    )


class Tag(Base):
    """Tag model for flexible listing categorization"""

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Tag information
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    # Usage statistics
    usage_count = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="tags")
    listings = relationship("Listing", secondary=listing_tags, back_populates="tags")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_tag_tenant_slug"),
        Index("idx_tag_tenant_id", "tenant_id"),
        Index("idx_tag_active", "is_active"),
        Index("idx_tag_usage", "usage_count"),
    )


class Media(Base):
    """Media files associated with listings"""

    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)

    # Media information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)

    # Image specific fields
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    alt_text = Column(String(255), nullable=True)

    # Organization
    sort_order = Column(Integer, default=0, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    listing = relationship("Listing", back_populates="media")

    # Constraints and indexes
    __table_args__ = (
        Index("idx_media_listing_id", "listing_id"),
        Index("idx_media_type", "media_type"),
        Index("idx_media_active", "is_active"),
        Index("idx_media_primary", "is_primary"),
    )


class Review(Base):
    """User reviews for listings"""

    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)

    # Status
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Moderation
    moderated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    listing = relationship("Listing", back_populates="reviews")
    user = relationship("User", back_populates="reviews", foreign_keys=[user_id])
    moderator = relationship("User", back_populates="moderated_reviews", foreign_keys=[moderated_by])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("listing_id", "user_id", name="uq_review_listing_user"),
        Index("idx_review_listing_id", "listing_id"),
        Index("idx_review_user_id", "user_id"),
        Index("idx_review_status", "status"),
        Index("idx_review_rating", "rating"),
        Index("idx_review_created_at", "created_at"),
    )


class APIKey(Base):
    """API keys for programmatic access"""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Key information
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed version of the key
    key_prefix = Column(
        String(20), nullable=False
    )  # First few chars for identification

    # Permissions
    permissions = Column(JSON, default=list)
    rate_limit = Column(Integer, default=1000, nullable=False)  # Requests per hour

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")

    # Constraints and indexes
    __table_args__ = (
        Index("idx_api_key_tenant_id", "tenant_id"),
        Index("idx_api_key_user_id", "user_id"),
        Index("idx_api_key_active", "is_active"),
        Index("idx_api_key_prefix", "key_prefix"),
    )


class Analytics(Base):
    """Tenant-level analytics and metrics"""

    __tablename__ = "analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Date and metrics
    date = Column(DateTime(timezone=True), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_data = Column(JSON, nullable=True)  # Additional metric details

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="analytics")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "date", "metric_name", name="uq_analytics_tenant_date_metric"
        ),
        Index("idx_analytics_tenant_id", "tenant_id"),
        Index("idx_analytics_date", "date"),
        Index("idx_analytics_metric", "metric_name"),
    )


class ListingAnalytics(Base):
    """Listing-specific analytics and metrics"""

    __tablename__ = "listing_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)

    # Date and metrics
    date = Column(DateTime(timezone=True), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_data = Column(JSON, nullable=True)  # Additional metric details

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    listing = relationship("Listing", back_populates="analytics")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "date",
            "metric_name",
            name="uq_listing_analytics_listing_date_metric",
        ),
        Index("idx_listing_analytics_listing_id", "listing_id"),
        Index("idx_listing_analytics_date", "date"),
        Index("idx_listing_analytics_metric", "metric_name"),
    )
