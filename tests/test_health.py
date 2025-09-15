from fastapi.testclient import TestClient

from laas.main import app


def test_health_check():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"

