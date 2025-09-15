"""
Database models for LAAS Platform
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, JSON, ARRAY, DECIMAL, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


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
    listings = relationship("Listing", back_populates="tenant", cascade="all, delete-orphan")
    industry_schemas = relationship("IndustrySchema", back_populates="tenant", cascade="all, delete-orphan")
    
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
    role = Column(String(50), default="user", nullable=False)
    permissions = Column(ARRAY(String), default=list)
    
    # Status
    status = Column(String(50), default="active", nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    listings = relationship("Listing", back_populates="owner", cascade="all, delete-orphan")
    
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
    searchable_fields = Column(ARRAY(String), default=list)
    required_fields = Column(ARRAY(String), default=list)
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
        UniqueConstraint("tenant_id", "industry", "version", name="uq_schema_tenant_industry_version"),
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
    schema_id = Column(UUID(as_uuid=True), ForeignKey("industry_schemas.id"), nullable=False)
    
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
    status = Column(String(50), default="draft", nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    
    # Pricing (if applicable)
    price = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    images = Column(ARRAY(String), default=list)  # URLs to images
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="listings")
    owner = relationship("User", back_populates="listings")
    schema = relationship("IndustrySchema", back_populates="listings")
    
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
