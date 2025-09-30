"""
LAAS Platform - Main FastAPI Application
Deployment trigger: Updated timestamp for testing
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from laas.api.v1.router import api_router
from laas.core.config import get_settings
from laas.database.connection import db_manager
from laas.middleware.audit import AuditMiddleware
from laas.middleware.rate_limit import RateLimitMiddleware
from laas.middleware.tenant import TenantMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting LAAS Platform...")

    # Initialize database
    try:
        db_manager.create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

    yield

    # Shutdown
    print("🛑 Shutting down LAAS Platform...")


# Create FastAPI application
app = FastAPI(
    title="LAAS Platform API",
    description="""
    ## Listing Platform as a Service (LAAS)
    
    A comprehensive, industry-agnostic API platform for building listing applications.
    
    ### Features
    - **Multi-tenant architecture** - Secure, isolated environments for each client
    - **Dynamic schema system** - Industry-specific field definitions
    - **Advanced search capabilities** - Geospatial, faceted, and AI-powered search
    - **Role-based access control** - Granular permissions and security
    - **Industry templates** - Pre-built configurations for various verticals
    
    ### Authentication
    All endpoints require authentication via JWT tokens. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ### Multi-Tenancy
    The platform supports multi-tenancy through subdomain routing or custom headers:
    - Subdomain: `tenant1.laas-platform.com`
    - Header: `X-Tenant-ID: tenant-id`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()

# Add middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TenantMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_error",
                "message": "An internal server error occurred",
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


# Request processing middleware
@app.middleware("http")
async def process_request(request: Request, call_next):
    """Process requests with timing and request ID"""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Start timing
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = "1.0.0"

    return response


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.environment,
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to LAAS Platform API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health",
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema with additional information"""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="LAAS Platform API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication",
        }
    }

    # Add global security
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add server information
    openapi_schema["servers"] = [
        {"url": "https://api.laas-platform.com", "description": "Production server"},
        {
            "url": "https://staging-api.laas-platform.com",
            "description": "Staging server",
        },
        {"url": "http://localhost:8000", "description": "Development server"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "laas.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
