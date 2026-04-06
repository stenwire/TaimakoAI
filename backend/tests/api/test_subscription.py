"""
Tests for subscription API endpoints.

Covers: POST /subscription/initialize, /subscription/cancel,
        /subscription/upgrade, /subscription/enable, /subscription/verify
"""
import pytest
from unittest.mock import patch, MagicMock

from tests.factories import (
    PlanFactory,
    PaymentTransactionFactory,
)

MOCK_SERVICE_PATH = "app.api.subscription.SubscriptionServiceFactory.get_service"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_service(**overrides):
    svc = MagicMock()
    svc.initialize_subscription.return_value = {
        "authorization_url": "https://checkout.paystack.com/test",
        "reference": "ref_test_123",
    }
    svc.cancel_subscription.return_value = True
    svc.verify_transaction.return_value = {
        "event_type": "RENEWAL_SUCCESS",
        "customer_email": "user@test.com",
        "customer_code": "CUS_test",
        "amount": 500000,
        "reference": "ref_verify_1",
        "raw_payload": {},
    }
    for k, v in overrides.items():
        setattr(svc, k, v)
    return svc


# ===========================================================================
# POST /subscription/initialize
# ===========================================================================


@pytest.mark.api
class TestInitializeSubscription:
    def test_success(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        plan = PlanFactory(name="spark", tier=1)
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post(
                "/subscription/initialize",
                json={"plan_id": plan.id},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "authorization_url" in body["data"]

    def test_missing_business_returns_404(self, authenticated_client, db_session):
        client, user = authenticated_client
        plan = PlanFactory(name="spark", tier=1)
        db_session.commit()

        resp = client.post(
            "/subscription/initialize",
            json={"plan_id": plan.id},
        )
        assert resp.status_code == 404
        assert "Business not found" in resp.json()["message"]

    def test_missing_plan_returns_404(self, auth_client_with_business):
        client, user, business = auth_client_with_business

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post(
                "/subscription/initialize",
                json={"plan_id": 99999},
            )
        assert resp.status_code == 404
        assert "Plan not found" in resp.json()["message"]

    def test_unauthenticated_returns_error(self, client):
        resp = client.post(
            "/subscription/initialize",
            json={"plan_id": 1},
        )
        # Auth dependency may return 401 or 403 depending on middleware
        assert resp.status_code in (401, 403)


# ===========================================================================
# POST /subscription/cancel
# ===========================================================================


@pytest.mark.api
class TestCancelSubscription:
    def test_success(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = "SUB_test"
        business.subscription_status = "active"
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/cancel", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

        db_session.refresh(business)
        assert business.subscription_status == "non-renewing"

    def test_no_active_subscription(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = None
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/cancel", json={})
        assert resp.status_code == 400
        assert "No active subscription" in resp.json()["message"]

    def test_already_cancelled(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = "SUB_test"
        business.subscription_status = "cancelled"
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/cancel", json={})
        assert resp.status_code == 400
        assert "already cancelled" in resp.json()["message"]


# ===========================================================================
# POST /subscription/upgrade
# ===========================================================================


@pytest.mark.api
class TestUpgradeSubscription:
    def test_success(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_customer_id = "CUS_test"
        business.subscription_tier = "spark"
        PlanFactory(name="spark", tier=1)  # current plan (side-effect: DB record)
        new_plan = PlanFactory(name="nexus", tier=2)
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post(
                "/subscription/upgrade",
                json={"new_plan_id": new_plan.id},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "authorization_url" in body["data"]

    def test_missing_plan_raises_error(self, auth_client_with_business, db_session):
        """When the plan doesn't exist, the endpoint should return an error.

        NOTE: There is a known bug in the source — ``print(new_plan.to_dict())``
        on line 168 of subscription.py executes before the ``if not new_plan``
        guard, causing an AttributeError. The TestClient propagates this as
        an unhandled server exception.
        """
        client, user, business = auth_client_with_business
        business.payment_customer_id = "CUS_test"
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            with pytest.raises(AttributeError, match="to_dict"):
                client.post(
                    "/subscription/upgrade",
                    json={"new_plan_id": 99999},
                )

    def test_no_customer_profile(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_customer_id = None
        new_plan = PlanFactory(name="nexus", tier=2)
        # Need an old plan matching business tier so lookup succeeds
        PlanFactory(name="spark", tier=1)
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post(
                "/subscription/upgrade",
                json={"new_plan_id": new_plan.id},
            )
        assert resp.status_code == 400
        assert "Customer profile not found" in resp.json()["message"]

    def test_downgrade_rejected(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_customer_id = "CUS_test"
        business.subscription_tier = "nexus"
        PlanFactory(name="nexus", tier=2)  # current plan
        lower_plan = PlanFactory(name="spark", tier=1)
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post(
                "/subscription/upgrade",
                json={"new_plan_id": lower_plan.id},
            )
        assert resp.status_code == 400
        assert "Downgrades are not allowed" in resp.json()["message"]


# ===========================================================================
# POST /subscription/enable
# ===========================================================================


@pytest.mark.api
class TestEnableSubscription:
    def test_success(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = "SUB_test"
        business.subscription_status = "non-renewing"
        business.subscription_tier = "spark"
        PlanFactory(name="spark", tier=1)
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/enable", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "authorization_url" in body["data"]

    def test_not_non_renewing(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = "SUB_test"
        business.subscription_status = "active"
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/enable", json={})
        assert resp.status_code == 400
        assert "not in non-renewing state" in resp.json()["message"]

    def test_no_subscription(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        business.payment_subscription_id = None
        business.subscription_status = "non-renewing"
        db_session.commit()

        with patch(MOCK_SERVICE_PATH, return_value=_make_mock_service()):
            resp = client.post("/subscription/enable", json={})
        assert resp.status_code == 400
        assert "No active subscription" in resp.json()["message"]


# ===========================================================================
# POST /subscription/verify
# ===========================================================================


@pytest.mark.api
class TestVerifySubscription:
    def test_success(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business

        mock_svc = _make_mock_service()
        with patch(MOCK_SERVICE_PATH, return_value=mock_svc):
            resp = client.post(
                "/subscription/verify",
                json={"reference": "ref_verify_1"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "verified" in body["message"].lower() or "processed" in body["message"].lower()

    def test_duplicate_reference_skips(self, auth_client_with_business, db_session):
        client, user, business = auth_client_with_business
        PaymentTransactionFactory(
            business=business,
            business_id=business.id,
            reference="ref_dup",
        )
        db_session.commit()

        mock_svc = _make_mock_service()
        with patch(MOCK_SERVICE_PATH, return_value=mock_svc):
            resp = client.post(
                "/subscription/verify",
                json={"reference": "ref_dup"},
            )
        assert resp.status_code == 200
        assert "already processed" in resp.json()["message"].lower()
        mock_svc.verify_transaction.assert_not_called()
