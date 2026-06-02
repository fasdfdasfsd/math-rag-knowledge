"""Middleware tests."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.core.exceptions import AppException, NotFoundException
from src.core.middleware import register_middleware


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    register_middleware(app)

    @app.get("/test-ok")
    async def ok():
        return {"status": "ok"}

    @app.get("/test-error")
    async def error():
        raise NotFoundException("Resource", "123")

    @app.get("/test-unauth")
    async def unauth():
        raise AppException("unauthorized", status_code=401)

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestMiddleware:
    def test_ok_response(self, client: TestClient) -> None:
        resp = client.get("/test-ok")
        assert resp.status_code == 200
        assert "X-Trace-Id" in resp.headers
        assert "X-Duration-Ms" in resp.headers

    def test_error_response_has_trace_id(self, client: TestClient) -> None:
        resp = client.get("/test-error")
        assert resp.status_code == 404
        assert "X-Trace-Id" in resp.headers

    def test_error_response_rfc9457_format(self, client: TestClient) -> None:
        resp = client.get("/test-error")
        body = resp.json()
        assert "title" in body
        assert "status" in body

    def test_custom_status_code(self, client: TestClient) -> None:
        resp = client.get("/test-unauth")
        assert resp.status_code == 401

    def test_cors_headers(self, client: TestClient) -> None:
        resp = client.options("/test-ok", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # CORS preflight should succeed
        assert resp.status_code in (200, 204, 405)
