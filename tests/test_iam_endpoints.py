"""
IAM-based endpoint tests for LAAS Platform
"""

from fastapi.testclient import TestClient

from laas.main import app


def test_api_status_endpoint():
    """Test the IAM-based API status endpoint"""
    client = TestClient(app)
    response = client.get("/api/v1/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["authentication"] == "iam"
    assert "message" in data


def test_root_endpoint():
    """Test the root endpoint"""
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "LAAS Platform"
    assert data["version"] == "1.0.0"
    assert "docs_url" in data
    assert "health_url" in data


def test_health_endpoint():
    """Test the health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
