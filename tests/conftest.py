"""
Pytest configuration and shared fixtures for LAAS Platform tests
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from laas.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def auth_headers():
    """Create authentication headers for testing."""
    # For IAM-based authentication, we'll use mock headers
    return {
        "Authorization": "Bearer mock-iam-token",
        "X-User-ID": "test-user-123"
    }


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]

