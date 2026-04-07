"""
Tests for the plans API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock

from tests.factories import PlanFactory


pytestmark = pytest.mark.api


class TestGetPublicPlans:
    """Tests for GET /public/plans."""

    def test_list_active_plans(self, client, db_session):
        """Returns active plans ordered by tier."""
        PlanFactory(name="spark", tier=1, price=5000, is_active=True)
        PlanFactory(name="flux", tier=2, price=10000, is_active=True)
        PlanFactory(name="nexus", tier=3, price=20000, is_active=False)
        db_session.commit()

        resp = client.get("/public/plans")
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Plans retrieved successfully"

        plans = body["data"]
        assert len(plans) == 2
        assert plans[0]["name"] == "spark"
        assert plans[0]["tier"] == 1
        assert plans[1]["name"] == "flux"
        assert plans[1]["tier"] == 2

    def test_empty_list_when_no_plans(self, client, db_session):
        """Returns an empty list when no plans exist."""
        resp = client.get("/public/plans")
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        assert body["data"] == []

    def test_features_dict_formatted(self, client, db_session):
        """Features dict is formatted into human-readable list."""
        PlanFactory(
            name="spark",
            tier=1,
            is_active=True,
            features={"ai_responses": 500, "daily_sessions": 50},
        )
        db_session.commit()

        resp = client.get("/public/plans")
        assert resp.status_code == 200

        features = resp.json()["data"][0]["features"]
        assert isinstance(features, list)
        assert len(features) == 2
        # Features formatted as "{value} {Key Title}"
        assert "500 Ai Responses" in features
        assert "50 Daily Sessions" in features

    def test_features_empty_dict_returns_empty_list(self, client, db_session):
        """An empty features dict becomes an empty list."""
        PlanFactory(name="spark", tier=1, is_active=True, features={})
        db_session.commit()

        resp = client.get("/public/plans")
        features = resp.json()["data"][0]["features"]
        assert features == []


class TestSyncPlans:
    """Tests for POST /plans/sync."""

    def test_requires_auth(self, client):
        """Unauthenticated request is rejected."""
        resp = client.post("/plans/sync", json={"provider": "paystack"})
        assert resp.status_code in (401, 403)

    @patch("app.api.plans.SubscriptionServiceFactory")
    def test_sync_creates_and_updates(self, mock_factory, authenticated_client, db_session):
        """Sync upserts plans from the provider."""
        client, user = authenticated_client

        # Seed an existing plan to be updated
        PlanFactory(plan_code="PLN_existing", name="old_name", price=1000)
        db_session.commit()

        mock_service = MagicMock()
        mock_service.sync_plans.return_value = [
            {"plan_code": "PLN_existing", "name": "updated_name", "amount": 2000, "currency": "NGN", "interval": "monthly"},
            {"plan_code": "PLN_new", "name": "brand_new", "amount": 5000, "currency": "NGN", "interval": "monthly"},
        ]
        mock_factory.get_service.return_value = mock_service

        resp = client.post("/plans/sync", json={"provider": "paystack"})
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["updated"] == 1
        assert body["data"]["created"] == 1
