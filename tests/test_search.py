"""
Search engine tests for LAAS Platform
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from laas.database.models import (
    Base, Tenant, User, IndustrySchema, Listing, Category, Tag,
    ListingStatus, UserRole
)
from laas.search.engine import SearchEngine


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
def search_engine(db_session):
    """Create search engine instance"""
    return SearchEngine(db_session)


@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing"""
    # Create tenant
    tenant = Tenant(
        name="Test Tenant",
        subdomain="test",
        industry="general",
        status="active"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # Create user
    user = User(
        tenant_id=tenant.id,
        email="test@example.com",
        password_hash="hash",
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create schema
    schema = IndustrySchema(
        tenant_id=tenant.id,
        industry="general",
        name="Test Schema",
        fields=[]
    )
    db_session.add(schema)
    db_session.commit()
    db_session.refresh(schema)
    
    # Create categories
    electronics = Category(
        tenant_id=tenant.id,
        name="Electronics",
        slug="electronics",
        level=0
    )
    db_session.add(electronics)
    db_session.commit()
    db_session.refresh(electronics)
    
    laptops = Category(
        tenant_id=tenant.id,
        parent_id=electronics.id,
        name="Laptops",
        slug="laptops",
        level=1
    )
    db_session.add(laptops)
    db_session.commit()
    db_session.refresh(laptops)
    
    # Create tags
    featured = Tag(
        tenant_id=tenant.id,
        name="Featured",
        slug="featured"
    )
    db_session.add(featured)
    db_session.commit()
    db_session.refresh(featured)
    
    new = Tag(
        tenant_id=tenant.id,
        name="New",
        slug="new"
    )
    db_session.add(new)
    db_session.commit()
    db_session.refresh(new)
    
    # Create listings
    listing1 = Listing(
        tenant_id=tenant.id,
        owner_id=user.id,
        schema_id=schema.id,
        title="MacBook Pro 16-inch",
        description="High-performance laptop for professionals",
        slug="macbook-pro-16",
        status=ListingStatus.PUBLISHED,
        price=2499.00,
        currency="USD",
        city="San Francisco",
        state="CA",
        country="USA"
    )
    db_session.add(listing1)
    db_session.commit()
    db_session.refresh(listing1)
    
    listing2 = Listing(
        tenant_id=tenant.id,
        owner_id=user.id,
        schema_id=schema.id,
        title="Dell XPS 13",
        description="Ultrabook with great battery life",
        slug="dell-xps-13",
        status=ListingStatus.PUBLISHED,
        price=1299.00,
        currency="USD",
        city="New York",
        state="NY",
        country="USA"
    )
    db_session.add(listing2)
    db_session.commit()
    db_session.refresh(listing2)
    
    listing3 = Listing(
        tenant_id=tenant.id,
        owner_id=user.id,
        schema_id=schema.id,
        title="iPhone 15 Pro",
        description="Latest iPhone with titanium design",
        slug="iphone-15-pro",
        status=ListingStatus.PUBLISHED,
        price=999.00,
        currency="USD",
        city="Los Angeles",
        state="CA",
        country="USA"
    )
    db_session.add(listing3)
    db_session.commit()
    db_session.refresh(listing3)
    
    # Associate listings with categories and tags
    listing1.categories.append(laptops)
    listing2.categories.append(laptops)
    listing1.tags.append(featured)
    listing2.tags.append(new)
    listing3.tags.append(featured)
    
    db_session.commit()
    
    return {
        "tenant": tenant,
        "user": user,
        "schema": schema,
        "categories": {"electronics": electronics, "laptops": laptops},
        "tags": {"featured": featured, "new": new},
        "listings": {"macbook": listing1, "dell": listing2, "iphone": listing3}
    }


class TestSearchEngine:
    """Test SearchEngine functionality"""
    
    def test_basic_search(self, search_engine, sample_data):
        """Test basic text search"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            query="MacBook"
        )
        
        assert results["total"] == 1
        assert len(results["results"]) == 1
        assert results["results"][0].title == "MacBook Pro 16-inch"
    
    def test_search_no_results(self, search_engine, sample_data):
        """Test search with no results"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            query="nonexistent"
        )
        
        assert results["total"] == 0
        assert len(results["results"]) == 0
    
    def test_search_all_listings(self, search_engine, sample_data):
        """Test search without query returns all listings"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id)
        )
        
        assert results["total"] == 3
        assert len(results["results"]) == 3
    
    def test_category_filter(self, search_engine, sample_data):
        """Test category filtering"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            categories=["laptops"]
        )
        
        assert results["total"] == 2
        titles = [listing.title for listing in results["results"]]
        assert "MacBook Pro 16-inch" in titles
        assert "Dell XPS 13" in titles
        assert "iPhone 15 Pro" not in titles
    
    def test_tag_filter(self, search_engine, sample_data):
        """Test tag filtering"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            tags=["featured"]
        )
        
        assert results["total"] == 2
        titles = [listing.title for listing in results["results"]]
        assert "MacBook Pro 16-inch" in titles
        assert "iPhone 15 Pro" in titles
        assert "Dell XPS 13" not in titles
    
    def test_price_range_filter(self, search_engine, sample_data):
        """Test price range filtering"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            price_range={"min": 1000, "max": 2000}
        )
        
        assert results["total"] == 1
        assert results["results"][0].title == "Dell XPS 13"
    
    def test_multiple_filters(self, search_engine, sample_data):
        """Test multiple filters combined"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            categories=["laptops"],
            tags=["featured"],
            price_range={"min": 2000}
        )
        
        assert results["total"] == 1
        assert results["results"][0].title == "MacBook Pro 16-inch"
    
    def test_sort_by_price_asc(self, search_engine, sample_data):
        """Test sorting by price ascending"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            sort_by="price",
            sort_order="asc"
        )
        
        assert results["total"] == 3
        prices = [listing.price for listing in results["results"]]
        assert prices == sorted(prices)
    
    def test_sort_by_price_desc(self, search_engine, sample_data):
        """Test sorting by price descending"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            sort_by="price",
            sort_order="desc"
        )
        
        assert results["total"] == 3
        prices = [listing.price for listing in results["results"]]
        assert prices == sorted(prices, reverse=True)
    
    def test_pagination(self, search_engine, sample_data):
        """Test pagination"""
        # First page
        results1 = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            limit=2,
            offset=0
        )
        
        assert results1["total"] == 3
        assert len(results1["results"]) == 2
        assert results1["has_more"] == True
        
        # Second page
        results2 = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            limit=2,
            offset=2
        )
        
        assert results2["total"] == 3
        assert len(results2["results"]) == 1
        assert results2["has_more"] == False
    
    def test_get_facets(self, search_engine, sample_data):
        """Test getting search facets"""
        facets = search_engine.get_facets(
            tenant_id=str(sample_data["tenant"].id)
        )
        
        assert "categories" in facets
        assert "tags" in facets
        assert "price_range" in facets
        
        # Check category facets
        category_names = [cat["name"] for cat in facets["categories"]]
        assert "Laptops" in category_names
        
        # Check tag facets
        tag_names = [tag["name"] for tag in facets["tags"]]
        assert "Featured" in tag_names
        assert "New" in tag_names
        
        # Check price range
        assert facets["price_range"]["min"] == 999.0
        assert facets["price_range"]["max"] == 2499.0
    
    def test_get_suggestions(self, search_engine, sample_data):
        """Test getting search suggestions"""
        suggestions = search_engine.get_suggestions(
            tenant_id=str(sample_data["tenant"].id),
            query="Mac"
        )
        
        assert "MacBook Pro 16-inch" in suggestions
    
    def test_search_with_filters(self, search_engine, sample_data):
        """Test search with additional filters"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            query="laptop",
            filters={"currency": "USD"}
        )
        
        assert results["total"] >= 0  # Should not raise error
        for listing in results["results"]:
            assert listing.currency == "USD"
    
    def test_search_include_relationships(self, search_engine, sample_data):
        """Test search with relationship loading"""
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id),
            include_media=True,
            include_reviews=True
        )
        
        assert results["total"] == 3
        # Note: In a real test with PostgreSQL, we could verify
        # that relationships are properly loaded
    
    def test_search_draft_listings_excluded(self, search_engine, sample_data, db_session):
        """Test that draft listings are excluded from search"""
        # Create a draft listing
        draft_listing = Listing(
            tenant_id=sample_data["tenant"].id,
            owner_id=sample_data["user"].id,
            schema_id=sample_data["schema"].id,
            title="Draft Listing",
            slug="draft-listing",
            status=ListingStatus.DRAFT
        )
        db_session.add(draft_listing)
        db_session.commit()
        
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id)
        )
        
        # Should still only return 3 published listings
        assert results["total"] == 3
        titles = [listing.title for listing in results["results"]]
        assert "Draft Listing" not in titles
    
    def test_search_private_listings_excluded(self, search_engine, sample_data, db_session):
        """Test that private listings are excluded from search"""
        # Create a private listing
        private_listing = Listing(
            tenant_id=sample_data["tenant"].id,
            owner_id=sample_data["user"].id,
            schema_id=sample_data["schema"].id,
            title="Private Listing",
            slug="private-listing",
            status=ListingStatus.PUBLISHED,
            is_public=False
        )
        db_session.add(private_listing)
        db_session.commit()
        
        results = search_engine.search(
            tenant_id=str(sample_data["tenant"].id)
        )
        
        # Should still only return 3 public listings
        assert results["total"] == 3
        titles = [listing.title for listing in results["results"]]
        assert "Private Listing" not in titles

