"""
Tests for root endpoints defined in app/main.py.

Covers: GET / (welcome message), GET /health
"""
import pytest


@pytest.mark.api
class TestRootEndpoint:
    def test_root_returns_success_response(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        assert "running" in body["message"].lower()
        assert body["data"] is None

    def test_root_response_has_standard_keys(self, client):
        body = client.get("/").json()
        assert "status" in body
        assert "message" in body
        assert "data" in body


@pytest.mark.api
class TestHealthEndpoint:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
