"""
API v1 Router
"""

from fastapi import APIRouter

# Import sub-routers
# from . import auth, tenants, users, listings, schemas, search

api_router = APIRouter()

# Register sub-routers
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
# api_router.include_router(schemas.router, prefix="/schemas", tags=["Schemas"])
# api_router.include_router(search.router, prefix="/search", tags=["Search"])

"""
Main API router for v1
"""

from fastapi import APIRouter

from laas.api.v1.endpoints import auth, users, tenants, listings, schemas, search

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
api_router.include_router(schemas.router, prefix="/schemas", tags=["Schemas"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
