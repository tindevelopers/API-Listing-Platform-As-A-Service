"""
Advanced search engine with full-text search, geospatial, and faceted search
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Session, joinedload

from laas.database.models import (
    Category,
    Listing,
    ListingStatus,
    Media,
    Review,
    ReviewStatus,
    Tag,
)


class SearchEngine:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        tenant_id: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        location: Optional[Dict[str, Any]] = None,
        price_range: Optional[Dict[str, float]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
        include_media: bool = True,
        include_reviews: bool = False,
    ) -> Dict[str, Any]:
        """
        Advanced search with multiple filter options
        """
        # Base query with relationships
        q = self.db.query(Listing).filter(
            Listing.tenant_id == tenant_id,
            Listing.is_public == True,
            Listing.status == ListingStatus.PUBLISHED,
        )

        # Add relationships for eager loading
        if include_media:
            q = q.options(joinedload(Listing.media))
        if include_reviews:
            q = q.options(joinedload(Listing.reviews))

        # Full-text search
        if query:
            # Use PostgreSQL full-text search if available
            if hasattr(Listing, "search_vector"):
                q = q.filter(Listing.search_vector.match(query))
            else:
                # Fallback to ILIKE search
                q = q.filter(
                    or_(
                        Listing.title.ilike(f"%{query}%"),
                        Listing.description.ilike(f"%{query}%"),
                        Listing.address.ilike(f"%{query}%"),
                        Listing.city.ilike(f"%{query}%"),
                        Listing.state.ilike(f"%{query}%"),
                    )
                )

        # Category filtering
        if categories:
            q = q.join(Listing.categories).filter(Category.slug.in_(categories))

        # Tag filtering
        if tags:
            q = q.join(Listing.tags).filter(Tag.slug.in_(tags))

        # Location-based search
        if location:
            lat = location.get("latitude")
            lon = location.get("longitude")
            radius = location.get("radius", 25)  # Default 25 miles

            if lat and lon:
                # Use PostGIS for accurate distance calculation
                q = q.filter(
                    and_(
                        Listing.latitude.isnot(None),
                        Listing.longitude.isnot(None),
                        text(
                            f"ST_DWithin(ST_Point(listings.longitude, listings.latitude)::geography, ST_Point({lon}, {lat})::geography, {radius * 1609.344})"
                        ),
                    )
                )

        # Price range filtering
        if price_range:
            min_price = price_range.get("min")
            max_price = price_range.get("max")

            if min_price is not None:
                q = q.filter(Listing.price >= min_price)
            if max_price is not None:
                q = q.filter(Listing.price <= max_price)

        # Additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(Listing, field) and value is not None:
                    if isinstance(value, list):
                        q = q.filter(getattr(Listing, field).in_(value))
                    else:
                        q = q.filter(getattr(Listing, field) == value)

        # Sorting
        if sort_by == "relevance" and query:
            # Sort by search relevance (PostgreSQL full-text search ranking)
            if hasattr(Listing, "search_vector"):
                q = q.order_by(
                    desc(
                        func.ts_rank(
                            Listing.search_vector,
                            func.plainto_tsquery("laas_search", query),
                        )
                    )
                )
            else:
                q = q.order_by(desc(Listing.created_at))
        elif sort_by == "distance" and location:
            # Sort by distance from location
            lat = location.get("latitude")
            lon = location.get("longitude")
            if lat and lon:
                q = q.order_by(
                    text(
                        f"ST_Distance(ST_Point(listings.longitude, listings.latitude)::geography, ST_Point({lon}, {lat})::geography)"
                    )
                )
        elif sort_by == "rating":
            # Sort by average rating
            q = (
                q.outerjoin(Review)
                .filter(Review.status == ReviewStatus.APPROVED)
                .group_by(Listing.id)
                .order_by(desc(func.avg(Review.rating)))
            )
        elif hasattr(Listing, sort_by):
            col = getattr(Listing, sort_by)
            q = q.order_by(col.desc() if sort_order == "desc" else col.asc())
        else:
            q = q.order_by(desc(Listing.created_at))

        # Get total count before pagination
        total = q.count()

        # Apply pagination
        items = q.offset(offset).limit(limit).all()

        return {
            "results": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        }

    def get_facets(
        self,
        tenant_id: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get search facets for filtering UI
        """
        # Base query
        q = self.db.query(Listing).filter(
            Listing.tenant_id == tenant_id,
            Listing.is_public == True,
            Listing.status == ListingStatus.PUBLISHED,
        )

        # Apply same filters as search
        if query:
            if hasattr(Listing, "search_vector"):
                q = q.filter(Listing.search_vector.match(query))
            else:
                q = q.filter(
                    or_(
                        Listing.title.ilike(f"%{query}%"),
                        Listing.description.ilike(f"%{query}%"),
                    )
                )

        if filters:
            for field, value in filters.items():
                if hasattr(Listing, field) and value is not None:
                    q = q.filter(getattr(Listing, field) == value)

        # Get category facets
        category_facets = (
            self.db.query(
                Category.name, Category.slug, func.count(Listing.id).label("count")
            )
            .join(Listing.categories)
            .filter(Category.tenant_id == tenant_id, Category.is_active == True)
            .group_by(Category.id, Category.name, Category.slug)
            .all()
        )

        # Get tag facets
        tag_facets = (
            self.db.query(Tag.name, Tag.slug, func.count(Listing.id).label("count"))
            .join(Listing.tags)
            .filter(Tag.tenant_id == tenant_id, Tag.is_active == True)
            .group_by(Tag.id, Tag.name, Tag.slug)
            .all()
        )

        # Get price range facets
        price_stats = (
            self.db.query(
                func.min(Listing.price).label("min_price"),
                func.max(Listing.price).label("max_price"),
                func.avg(Listing.price).label("avg_price"),
            )
            .filter(
                Listing.tenant_id == tenant_id,
                Listing.is_public == True,
                Listing.status == ListingStatus.PUBLISHED,
                Listing.price.isnot(None),
            )
            .first()
        )

        return {
            "categories": [
                {"name": name, "slug": slug, "count": count}
                for name, slug, count in category_facets
            ],
            "tags": [
                {"name": name, "slug": slug, "count": count}
                for name, slug, count in tag_facets
            ],
            "price_range": (
                {
                    "min": float(price_stats.min_price) if price_stats.min_price else 0,
                    "max": float(price_stats.max_price) if price_stats.max_price else 0,
                    "avg": float(price_stats.avg_price) if price_stats.avg_price else 0,
                }
                if price_stats
                else None
            ),
        }

    def get_suggestions(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Get search suggestions based on query
        """
        # Get suggestions from listing titles
        title_suggestions = (
            self.db.query(Listing.title)
            .filter(
                Listing.tenant_id == tenant_id,
                Listing.is_public == True,
                Listing.status == ListingStatus.PUBLISHED,
                Listing.title.ilike(f"%{query}%"),
            )
            .limit(limit)
            .all()
        )

        # Get suggestions from categories
        category_suggestions = (
            self.db.query(Category.name)
            .filter(
                Category.tenant_id == tenant_id,
                Category.is_active == True,
                Category.name.ilike(f"%{query}%"),
            )
            .limit(limit)
            .all()
        )

        # Combine and deduplicate
        suggestions = set()
        for (title,) in title_suggestions:
            suggestions.add(title)
        for (name,) in category_suggestions:
            suggestions.add(name)

        return list(suggestions)[:limit]
