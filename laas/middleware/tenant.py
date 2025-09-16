"""
Multi-tenant middleware for request routing and tenant isolation
"""

import re
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from laas.database.connection import get_db
from laas.database.models import Tenant


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for multi-tenant request routing"""

    def __init__(self, app, tenant_header: str = "X-Tenant-ID"):
        super().__init__(app)
        self.tenant_header = tenant_header
        self.subdomain_pattern = re.compile(r"^([^.]+)\.(.+)$")

    async def dispatch(self, request: Request, call_next):
        """Process request and extract tenant information"""

        # Skip tenant resolution for certain paths
        if self._should_skip_tenant_resolution(request):
            return await call_next(request)

        # Extract tenant ID from request
        tenant_id = await self._extract_tenant_id(request)

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required",
            )

        # Validate tenant exists and is active
        tenant = await self._validate_tenant(tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found or inactive",
            )

        # Set tenant context
        request.state.tenant_id = str(tenant.id)
        request.state.tenant = tenant

        # Set database context for tenant isolation
        request.state.tenant_context = {
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_industry": tenant.industry,
            "tenant_plan": tenant.plan,
        }

        # Process request
        response = await call_next(request)

        # Add tenant information to response headers
        response.headers["X-Tenant-ID"] = str(tenant.id)
        response.headers["X-Tenant-Name"] = tenant.name

        return response

    def _should_skip_tenant_resolution(self, request: Request) -> bool:
        """Check if tenant resolution should be skipped for this request"""
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]

        return any(request.url.path.startswith(path) for path in skip_paths)

    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""

        # Method 1: Check custom header
        tenant_id = request.headers.get(self.tenant_header)
        if tenant_id:
            return tenant_id

        # Method 2: Extract from subdomain
        host = request.headers.get("host", "")
        if host:
            match = self.subdomain_pattern.match(host)
            if match:
                subdomain = match.group(1)
                # Skip common subdomains
                if subdomain not in ["www", "api", "admin", "app"]:
                    return subdomain

        # Method 3: Extract from query parameter (for development)
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        return None

    async def _validate_tenant(self, tenant_identifier: str) -> Optional[Tenant]:
        """Validate tenant exists and is active"""
        try:
            # Get database session
            db = next(get_db())

            # Try to find tenant by ID first
            tenant = db.query(Tenant).filter(Tenant.id == tenant_identifier).first()

            # If not found by ID, try by subdomain
            if not tenant:
                tenant = (
                    db.query(Tenant)
                    .filter(
                        Tenant.subdomain == tenant_identifier, Tenant.status == "active"
                    )
                    .first()
                )

            # Check if tenant is active
            if tenant and tenant.status != "active":
                return None

            return tenant

        except Exception as e:
            # Log error but don't expose details
            print(f"Error validating tenant {tenant_identifier}: {e}")
            return None
        finally:
            if "db" in locals():
                db.close()
