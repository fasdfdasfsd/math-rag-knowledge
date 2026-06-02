"""API route registration tests via OpenAPI schema."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from src.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client. DB not initialized but /health and /docs work."""
    app = create_app()
    return TestClient(app)


class TestRouteExistence:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_docs(self, client: TestClient) -> None:
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_all_routes_registered_in_openapi(self, client: TestClient) -> None:
        """Verify all 6 route groups are registered in OpenAPI schema."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = list(resp.json()["paths"].keys())
        prefixes = {p.split("/")[3] for p in paths if p.startswith("/api/v1/")}
        assert "adventure" in prefixes, f"Missing adventure routes. Found: {prefixes}"
        assert "npc" in prefixes, f"Missing npc routes. Found: {prefixes}"
        assert "collection" in prefixes, f"Missing collection routes. Found: {prefixes}"
        assert "parent" in prefixes, f"Missing parent routes. Found: {prefixes}"
        assert "world" in prefixes, f"Missing world routes. Found: {prefixes}"
        assert "content" in prefixes, f"Missing content routes. Found: {prefixes}"

    def test_npc_route_exists(self, client: TestClient) -> None:
        resp = client.get("/api/v1/npc/npc1")
        assert resp.status_code != 404  # Route exists (DB init fails but route is registered)

    def test_collection_route_exists(self, client: TestClient) -> None:
        resp = client.get("/api/v1/collection")
        assert resp.status_code != 404

    def test_parent_route_exists(self, client: TestClient) -> None:
        resp = client.get("/api/v1/parent/dashboard")
        assert resp.status_code != 404

    def test_world_route_exists(self, client: TestClient) -> None:
        resp = client.get("/api/v1/world")
        assert resp.status_code != 404

    def test_content_report_route_exists(self, client: TestClient) -> None:
        resp = client.post("/api/v1/content/reports?level_id=l1&report_type=inappropriate")
        assert resp.status_code != 404
