"""
Main API router for v1
"""

from fastapi import APIRouter

from laas.api.v1.endpoints import auth

# Create main API router
api_router = APIRouter()

# Include available endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# TODO: Add other endpoint routers when they are implemented
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
# api_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
# api_router.include_router(schemas.router, prefix="/schemas", tags=["Schemas"])
# api_router.include_router(search.router, prefix="/search", tags=["Search"])
