"""
Audit logging middleware
"""

import json
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from laas.database.connection import get_db
from laas.database.models import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging"""

    def __init__(self, app):
        super().__init__(app)
        self.audit_enabled = True

    async def dispatch(self, request: Request, call_next):
        """Process request with audit logging"""

        # Skip audit logging for certain paths
        if self._should_skip_audit(request):
            return await call_next(request)

        # Extract audit information
        audit_data = await self._extract_audit_data(request)

        # Process request
        response = await call_next(request)

        # Log audit entry
        if self.audit_enabled and audit_data:
            await self._log_audit_entry(audit_data, response)

        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if audit logging should be skipped for this request"""
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]

        return any(request.url.path.startswith(path) for path in skip_paths)

    async def _extract_audit_data(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract audit data from request"""
        try:
            # Get tenant and user information
            tenant_id = getattr(request.state, "tenant_id", None)
            user_id = getattr(request.state, "user_id", None)

            # Get request information
            method = request.method
            path = request.url.path
            query_params = dict(request.query_params)

            # Get client information
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # Get request body (for POST/PUT requests)
            request_body = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        request_body = json.loads(body.decode())
                except:
                    pass

            return {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": f"{method} {path}",
                "resource_type": self._get_resource_type(path),
                "resource_id": self._extract_resource_id(path),
                "ip_address": client_ip,
                "user_agent": user_agent,
                "request_id": getattr(request.state, "request_id", None),
                "query_params": query_params,
                "request_body": request_body,
            }

        except Exception as e:
            print(f"Error extracting audit data: {e}")
            return None

    def _get_resource_type(self, path: str) -> str:
        """Extract resource type from path"""
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[1]  # e.g., "listings", "users", etc.
        return "unknown"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path"""
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[2].replace("-", "").isalnum():
            return path_parts[2]
        return None

    async def _log_audit_entry(self, audit_data: Dict[str, Any], response: Response):
        """Log audit entry to database"""
        try:
            db = next(get_db())

            audit_log = AuditLog(
                tenant_id=audit_data.get("tenant_id"),
                user_id=audit_data.get("user_id"),
                action=audit_data.get("action"),
                resource_type=audit_data.get("resource_type"),
                resource_id=audit_data.get("resource_id"),
                ip_address=audit_data.get("ip_address"),
                user_agent=audit_data.get("user_agent"),
                request_id=audit_data.get("request_id"),
                old_values=None,  # Would be populated for update operations
                new_values=audit_data.get("request_body"),
            )

            db.add(audit_log)
            db.commit()

        except Exception as e:
            print(f"Error logging audit entry: {e}")
        finally:
            if "db" in locals():
                db.close()
