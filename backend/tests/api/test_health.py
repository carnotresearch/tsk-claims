"""
API tests for the /api/health endpoint.
"""
import pytest

pytestmark = pytest.mark.api


class TestHealthEndpoint:
    async def test_health_returns_200(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_health_status_ok(self, client):
        data = response = await client.get("/api/health")
        assert response.json()["status"] == "ok"

    async def test_health_has_version(self, client):
        response = await client.get("/api/health")
        assert "version" in response.json()

    async def test_health_environment_is_test(self, client):
        response = await client.get("/api/health")
        assert response.json()["environment"] == "test"

    async def test_health_content_type_json(self, client):
        response = await client.get("/api/health")
        assert "application/json" in response.headers["content-type"]
