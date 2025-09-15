"""
Search engine abstraction (placeholder for Phase 1 basic filtering)
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from laas.database.models import Listing


class SearchEngine:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        tenant_id: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        q = self.db.query(Listing).filter(
            Listing.tenant_id == tenant_id,
            Listing.is_public == True,
            Listing.status.in_(["published", "active"])  # noqa: E712
        )

        if query:
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

        if hasattr(Listing, sort_by):
            col = getattr(Listing, sort_by)
            q = q.order_by(col.desc() if sort_order == "desc" else col.asc())

        total = q.count()
        items = q.offset(offset).limit(limit).all()

        return {
            "results": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


