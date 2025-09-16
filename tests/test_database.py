"""
Database model tests for LAAS Platform
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from laas.database.models import (
    Base, Tenant, User, IndustrySchema, Listing, Category, Tag, 
    Media, Review, APIKey, Analytics, ListingAnalytics, AuditLog,
    ListingStatus, UserRole, MediaType, ReviewStatus
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_tenant(db_session):
    """Create a sample tenant for testing"""
    tenant = Tenant(
        name="Test Tenant",
        subdomain="test",
        industry="general",
        status="active",
        plan="starter"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def sample_user(db_session, sample_tenant):
    """Create a sample user for testing"""
    user = User(
        tenant_id=sample_tenant.id,
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestTenant:
    """Test Tenant model"""
    
    def test_create_tenant(self, db_session):
        """Test tenant creation"""
        tenant = Tenant(
            name="Test Company",
            subdomain="testco",
            industry="real_estate",
            status="active",
            plan="enterprise"
        )
        db_session.add(tenant)
        db_session.commit()
        
        assert tenant.id is not None
        assert tenant.name == "Test Company"
        assert tenant.subdomain == "testco"
        assert tenant.industry == "real_estate"
        assert tenant.status == "active"
        assert tenant.plan == "enterprise"
        assert tenant.created_at is not None

    def test_tenant_unique_subdomain(self, db_session):
        """Test tenant subdomain uniqueness"""
        tenant1 = Tenant(
            name="Company 1",
            subdomain="unique",
            industry="general"
        )
        tenant2 = Tenant(
            name="Company 2",
            subdomain="unique",  # Same subdomain
            industry="general"
        )
        
        db_session.add(tenant1)
        db_session.commit()
        
        db_session.add(tenant2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestUser:
    """Test User model"""
    
    def test_create_user(self, db_session, sample_tenant):
        """Test user creation"""
        user = User(
            tenant_id=sample_tenant.id,
            email="user@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            role=UserRole.ADMIN
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.tenant_id == sample_tenant.id
        assert user.email == "user@example.com"
        assert user.role == UserRole.ADMIN
        assert user.status == "active"  # Default value
        assert user.email_verified == False  # Default value

    def test_user_tenant_email_unique(self, db_session, sample_tenant):
        """Test user email uniqueness within tenant"""
        user1 = User(
            tenant_id=sample_tenant.id,
            email="same@example.com",
            password_hash="hash1"
        )
        user2 = User(
            tenant_id=sample_tenant.id,
            email="same@example.com",  # Same email, same tenant
            password_hash="hash2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestListing:
    """Test Listing model"""
    
    def test_create_listing(self, db_session, sample_tenant, sample_user):
        """Test listing creation"""
        # Create industry schema first
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[{"name": "title", "type": "text"}]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Test Listing",
            description="A test listing",
            slug="test-listing",
            status=ListingStatus.PUBLISHED,
            price=100.00,
            currency="USD"
        )
        db_session.add(listing)
        db_session.commit()
        
        assert listing.id is not None
        assert listing.title == "Test Listing"
        assert listing.status == ListingStatus.PUBLISHED
        assert listing.price == 100.00
        assert listing.currency == "USD"
        assert listing.is_public == True  # Default value

    def test_listing_tenant_slug_unique(self, db_session, sample_tenant, sample_user):
        """Test listing slug uniqueness within tenant"""
        # Create schema
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing1 = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Listing 1",
            slug="unique-slug"
        )
        listing2 = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Listing 2",
            slug="unique-slug"  # Same slug, same tenant
        )
        
        db_session.add(listing1)
        db_session.commit()
        
        db_session.add(listing2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestCategory:
    """Test Category model"""
    
    def test_create_category(self, db_session, sample_tenant):
        """Test category creation"""
        category = Category(
            tenant_id=sample_tenant.id,
            name="Electronics",
            slug="electronics",
            description="Electronic devices",
            icon="laptop",
            color="#FF0000",
            level=0,
            sort_order=1
        )
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.level == 0
        assert category.is_active == True  # Default value

    def test_category_hierarchy(self, db_session, sample_tenant):
        """Test category parent-child relationship"""
        parent = Category(
            tenant_id=sample_tenant.id,
            name="Electronics",
            slug="electronics",
            level=0
        )
        db_session.add(parent)
        db_session.commit()
        
        child = Category(
            tenant_id=sample_tenant.id,
            parent_id=parent.id,
            name="Laptops",
            slug="laptops",
            level=1
        )
        db_session.add(child)
        db_session.commit()
        
        assert child.parent_id == parent.id
        assert child.level == 1


class TestTag:
    """Test Tag model"""
    
    def test_create_tag(self, db_session, sample_tenant):
        """Test tag creation"""
        tag = Tag(
            tenant_id=sample_tenant.id,
            name="Featured",
            slug="featured",
            description="Featured listings",
            color="#FFD700",
            usage_count=0
        )
        db_session.add(tag)
        db_session.commit()
        
        assert tag.id is not None
        assert tag.name == "Featured"
        assert tag.slug == "featured"
        assert tag.usage_count == 0
        assert tag.is_active == True  # Default value


class TestMedia:
    """Test Media model"""
    
    def test_create_media(self, db_session, sample_tenant, sample_user):
        """Test media creation"""
        # Create listing first
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Test Listing",
            slug="test-listing"
        )
        db_session.add(listing)
        db_session.commit()
        
        media = Media(
            listing_id=listing.id,
            filename="test.jpg",
            original_filename="original.jpg",
            file_path="/uploads/test.jpg",
            file_url="https://example.com/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            media_type=MediaType.IMAGE,
            width=800,
            height=600,
            alt_text="Test image"
        )
        db_session.add(media)
        db_session.commit()
        
        assert media.id is not None
        assert media.listing_id == listing.id
        assert media.media_type == MediaType.IMAGE
        assert media.width == 800
        assert media.height == 600


class TestReview:
    """Test Review model"""
    
    def test_create_review(self, db_session, sample_tenant, sample_user):
        """Test review creation"""
        # Create listing first
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Test Listing",
            slug="test-listing"
        )
        db_session.add(listing)
        db_session.commit()
        
        review = Review(
            listing_id=listing.id,
            user_id=sample_user.id,
            rating=5,
            title="Great product!",
            content="Really happy with this purchase.",
            status=ReviewStatus.APPROVED
        )
        db_session.add(review)
        db_session.commit()
        
        assert review.id is not None
        assert review.rating == 5
        assert review.status == ReviewStatus.APPROVED
        assert review.is_verified == False  # Default value

    def test_review_listing_user_unique(self, db_session, sample_tenant, sample_user):
        """Test review uniqueness per listing-user pair"""
        # Create listing
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Test Listing",
            slug="test-listing"
        )
        db_session.add(listing)
        db_session.commit()
        
        review1 = Review(
            listing_id=listing.id,
            user_id=sample_user.id,
            rating=4
        )
        review2 = Review(
            listing_id=listing.id,
            user_id=sample_user.id,  # Same user, same listing
            rating=5
        )
        
        db_session.add(review1)
        db_session.commit()
        
        db_session.add(review2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


class TestAPIKey:
    """Test APIKey model"""
    
    def test_create_api_key(self, db_session, sample_tenant, sample_user):
        """Test API key creation"""
        api_key = APIKey(
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            name="Test API Key",
            key_hash="hashed_key",
            key_prefix="test_",
            permissions=["read", "write"],
            rate_limit=1000
        )
        db_session.add(api_key)
        db_session.commit()
        
        assert api_key.id is not None
        assert api_key.name == "Test API Key"
        assert api_key.key_prefix == "test_"
        assert api_key.rate_limit == 1000
        assert api_key.is_active == True  # Default value


class TestAnalytics:
    """Test Analytics models"""
    
    def test_create_analytics(self, db_session, sample_tenant):
        """Test analytics creation"""
        analytics = Analytics(
            tenant_id=sample_tenant.id,
            date=datetime.utcnow(),
            metric_name="total_listings",
            metric_value=100.0,
            metric_data={"breakdown": {"active": 80, "draft": 20}}
        )
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.id is not None
        assert analytics.metric_name == "total_listings"
        assert analytics.metric_value == 100.0
        assert analytics.metric_data["breakdown"]["active"] == 80

    def test_create_listing_analytics(self, db_session, sample_tenant, sample_user):
        """Test listing analytics creation"""
        # Create listing
        schema = IndustrySchema(
            tenant_id=sample_tenant.id,
            industry="general",
            name="Test Schema",
            fields=[]
        )
        db_session.add(schema)
        db_session.commit()
        
        listing = Listing(
            tenant_id=sample_tenant.id,
            owner_id=sample_user.id,
            schema_id=schema.id,
            title="Test Listing",
            slug="test-listing"
        )
        db_session.add(listing)
        db_session.commit()
        
        analytics = ListingAnalytics(
            listing_id=listing.id,
            date=datetime.utcnow(),
            metric_name="views",
            metric_value=50.0
        )
        db_session.add(analytics)
        db_session.commit()
        
        assert analytics.id is not None
        assert analytics.listing_id == listing.id
        assert analytics.metric_name == "views"
        assert analytics.metric_value == 50.0


class TestAuditLog:
    """Test AuditLog model"""
    
    def test_create_audit_log(self, db_session, sample_tenant, sample_user):
        """Test audit log creation"""
        audit_log = AuditLog(
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            action="CREATE",
            resource_type="listing",
            resource_id="123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-123",
            old_values=None,
            new_values={"title": "New Listing"}
        )
        db_session.add(audit_log)
        db_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.action == "CREATE"
        assert audit_log.resource_type == "listing"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.new_values["title"] == "New Listing"

