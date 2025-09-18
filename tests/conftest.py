"""
Pytest configuration and shared fixtures for LAAS Platform tests
"""

import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from laas.main import app
from laas.database.models import Base
from laas.database.connection import db_manager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Use environment variable for database URL, fallback to SQLite for local testing
    import os
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Override the global db_manager for testing
    original_engine = db_manager.engine
    original_session = db_manager.SessionLocal
    
    db_manager.engine = engine
    db_manager.SessionLocal = SessionLocal
    
    yield session
    
    # Restore original db_manager
    db_manager.engine = original_engine
    db_manager.SessionLocal = original_session
    session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def sample_tenant(test_db):
    """Create a sample tenant for testing."""
    from laas.database.models import Tenant
    
    tenant = Tenant(
        name="Test Tenant",
        subdomain="test",
        industry="general",
        status="active",
        plan="starter"
    )
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)
    return tenant


@pytest.fixture(scope="function")
def sample_user(test_db, sample_tenant):
    """Create a sample user for testing."""
    from laas.database.models import User, UserRole
    
    user = User(
        tenant_id=sample_tenant.id,
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.USER
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_schema(test_db, sample_tenant):
    """Create a sample industry schema for testing."""
    from laas.database.models import IndustrySchema
    
    schema = IndustrySchema(
        tenant_id=sample_tenant.id,
        industry="general",
        name="Test Schema",
        description="Test schema for testing",
        fields=[
            {
                "name": "title",
                "type": "text",
                "required": True,
                "display_name": "Title"
            },
            {
                "name": "description",
                "type": "text",
                "required": False,
                "display_name": "Description"
            }
        ],
        searchable_fields=["title", "description"],
        required_fields=["title"]
    )
    test_db.add(schema)
    test_db.commit()
    test_db.refresh(schema)
    return schema


@pytest.fixture(scope="function")
def sample_listing(test_db, sample_tenant, sample_user, sample_schema):
    """Create a sample listing for testing."""
    from laas.database.models import Listing, ListingStatus
    
    listing = Listing(
        tenant_id=sample_tenant.id,
        owner_id=sample_user.id,
        schema_id=sample_schema.id,
        title="Test Listing",
        description="A test listing for testing purposes",
        slug="test-listing",
        status=ListingStatus.PUBLISHED,
        price=100.00,
        currency="USD",
        city="Test City",
        state="Test State",
        country="Test Country"
    )
    test_db.add(listing)
    test_db.commit()
    test_db.refresh(listing)
    return listing


@pytest.fixture(scope="function")
def sample_categories(test_db, sample_tenant):
    """Create sample categories for testing."""
    from laas.database.models import Category
    
    electronics = Category(
        tenant_id=sample_tenant.id,
        name="Electronics",
        slug="electronics",
        description="Electronic devices",
        level=0,
        sort_order=1
    )
    test_db.add(electronics)
    test_db.commit()
    test_db.refresh(electronics)
    
    laptops = Category(
        tenant_id=sample_tenant.id,
        parent_id=electronics.id,
        name="Laptops",
        slug="laptops",
        description="Laptop computers",
        level=1,
        sort_order=1
    )
    test_db.add(laptops)
    test_db.commit()
    test_db.refresh(laptops)
    
    return {
        "electronics": electronics,
        "laptops": laptops
    }


@pytest.fixture(scope="function")
def sample_tags(test_db, sample_tenant):
    """Create sample tags for testing."""
    from laas.database.models import Tag
    
    featured = Tag(
        tenant_id=sample_tenant.id,
        name="Featured",
        slug="featured",
        description="Featured listings",
        color="#FFD700"
    )
    test_db.add(featured)
    test_db.commit()
    test_db.refresh(featured)
    
    new = Tag(
        tenant_id=sample_tenant.id,
        name="New",
        slug="new",
        description="New listings",
        color="#00FF00"
    )
    test_db.add(new)
    test_db.commit()
    test_db.refresh(new)
    
    return {
        "featured": featured,
        "new": new
    }


@pytest.fixture(scope="function")
def auth_headers(client, sample_user):
    """Create authentication headers for testing."""
    # This would normally involve getting a JWT token
    # For now, we'll return a placeholder
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": str(sample_user.tenant_id)
    }


@pytest.fixture(scope="function")
def search_engine(test_db):
    """Create a search engine instance for testing."""
    from laas.search.engine import SearchEngine
    return SearchEngine(test_db)


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]

