"""
Tests for the POST /webhooks/{provider} endpoint.

This is the most critical test file -- it validates that webhook events
from payment providers correctly update business state, handle credit
carryover math, and enforce idempotency.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from tests.factories import (
    UserFactory,
    BusinessFactory,
    PaymentTransactionFactory,
)

VERIFY_SIG_PATH = (
    "app.services.subscription.paystack.PaystackSubscriptionService"
    ".verify_webhook_signature"
)
PARSE_EVENT_PATH = (
    "app.services.subscription.paystack.PaystackSubscriptionService"
    ".parse_webhook_event"
)
FACTORY_PATH = "app.api.subscription.SubscriptionServiceFactory.get_service"

# Email helpers are fired as background tasks; just let them be called
EMAIL_PATCH_BASE = "app.api.subscription"


def _post_webhook(client, payload: dict, provider: str = "paystack"):
    """Helper to POST a webhook with correct content-type."""
    return client.post(
        f"/webhooks/{provider}",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )


def _make_event(event_type: str, email: str, **overrides) -> dict:
    """Build a standardized parsed webhook event dict."""
    base = {
        "event_type": event_type,
        "customer_email": email,
        "customer_code": overrides.pop("customer_code", "CUS_test123"),
        "subscription_code": overrides.pop("subscription_code", "SUB_test123"),
        "reference": overrides.pop("reference", f"ref_{event_type.lower()}_1"),
        "email_token": overrides.pop("email_token", "tok_test"),
        "authorization_code": overrides.pop("authorization_code", "AUTH_test"),
        "amount": overrides.pop("amount", 500000),
        "raw_payload": overrides.pop("raw_payload", {"data": {"metadata": {}}}),
    }
    base.update(overrides)
    return base


def _mock_service_with_event(event: dict):
    """Return a mock service that verifies signature and parses to `event`."""
    svc = MagicMock()
    svc.verify_webhook_signature.return_value = True
    svc.parse_webhook_event.return_value = event
    return svc


# ===========================================================================
# SUBSCRIPTION_CREATED
# ===========================================================================


@pytest.mark.api
class TestSubscriptionCreated:
    def test_sets_business_fields(self, client, db_session):
        user = UserFactory(email="sub@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        db_session.commit()

        event = _make_event(
            "SUBSCRIPTION_CREATED",
            email="sub@test.com",
            customer_code="CUS_abc",
            subscription_code="SUB_abc",
            email_token="tok_abc",
        )
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "subscription.create"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

        db_session.refresh(business)
        assert business.payment_customer_id == "CUS_abc"
        assert business.payment_subscription_id == "SUB_abc"
        assert business.subscription_email_token == "tok_abc"
        assert business.subscription_status == "active"


# ===========================================================================
# RENEWAL_SUCCESS
# ===========================================================================


@pytest.mark.api
class TestRenewalSuccess:
    def test_fresh_renewal_credits(self, client, db_session):
        """Standard renewal: plan credits + remaining, capped at 2x."""
        user = UserFactory(email="renew@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_tier = "spark"
        business.allocated_ai_responses = 100
        business.used_ai_responses = 60  # 40 remaining
        business.allocated_escalations = 5
        business.used_escalations = 2  # 3 remaining
        db_session.commit()

        event = _make_event(
            "RENEWAL_SUCCESS",
            email="renew@test.com",
            raw_payload={"data": {"metadata": {}}},
        )
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "charge.success"})

        assert resp.status_code == 200
        db_session.refresh(business)

        # spark: 100 monthly_credits, 5 max_monthly_escalations
        # new_ai = 100 + 40 = 140, cap = 200 => 140
        assert business.allocated_ai_responses == 140
        # new_esc = 5 + 3 = 8, cap = 10 => 8
        assert business.allocated_escalations == 8
        assert business.used_ai_responses == 0
        assert business.used_escalations == 0
        assert business.subscription_status == "active"

    def test_renewal_cap_at_2x(self, client, db_session):
        """Carryover should not exceed 2x plan allocation."""
        user = UserFactory(email="cap@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_tier = "spark"
        business.allocated_ai_responses = 100
        business.used_ai_responses = 0  # 100 remaining (full rollover)
        business.allocated_escalations = 5
        business.used_escalations = 0
        db_session.commit()

        event = _make_event(
            "RENEWAL_SUCCESS",
            email="cap@test.com",
            reference="ref_cap_1",
            raw_payload={"data": {"metadata": {}}},
        )
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "charge.success"})

        assert resp.status_code == 200
        db_session.refresh(business)

        # new_ai = 100 + 100 = 200, cap = 200 => 200
        assert business.allocated_ai_responses == 200
        # new_esc = 5 + 5 = 10, cap = 10 => 10
        assert business.allocated_escalations == 10

    def test_tier_upgrade_proportional_carryover(self, client, db_session):
        """Upgrade from spark to nexus uses proportional carry-over."""
        user = UserFactory(email="upgrade@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_tier = "spark"
        business.allocated_ai_responses = 100
        business.used_ai_responses = 50  # 50 remaining => ratio = 0.5
        business.allocated_escalations = 5
        business.used_escalations = 3  # 2 remaining => ratio = 0.4
        db_session.commit()

        event = _make_event(
            "RENEWAL_SUCCESS",
            email="upgrade@test.com",
            reference="ref_upgrade_1",
            raw_payload={
                "data": {
                    "metadata": {
                        "is_upgrade": True,
                        "tier": "nexus",
                    }
                }
            },
        )
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "charge.success"})

        assert resp.status_code == 200
        db_session.refresh(business)

        # nexus: 1000 monthly_credits, 100 max_monthly_escalations
        # ai: ratio=50/100=0.5, carryover=0.5*1000=500, total=1000+500=1500, cap=2000 => 1500
        assert business.allocated_ai_responses == 1500
        # esc: ratio=2/5=0.4, carryover=0.4*100=40, total=100+40=140, cap=200 => 140
        assert business.allocated_escalations == 140
        assert business.subscription_tier == "nexus"
        assert business.used_ai_responses == 0


# ===========================================================================
# SUBSCRIPTION_CANCELLED
# ===========================================================================


@pytest.mark.api
class TestSubscriptionCancelled:
    def test_sets_cancelled_status(self, client, db_session):
        user = UserFactory(email="cancel@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_status = "active"
        db_session.commit()

        event = _make_event("SUBSCRIPTION_CANCELLED", email="cancel@test.com")
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "subscription.disable"})

        assert resp.status_code == 200
        db_session.refresh(business)
        assert business.subscription_status == "cancelled"


# ===========================================================================
# PAYMENT_FAILED
# ===========================================================================


@pytest.mark.api
class TestPaymentFailed:
    def test_sets_attention_status(self, client, db_session):
        user = UserFactory(email="fail@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_status = "active"
        business.subscription_tier = "spark"
        db_session.commit()

        event = _make_event("PAYMENT_FAILED", email="fail@test.com")
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "invoice.payment_failed"})

        assert resp.status_code == 200
        db_session.refresh(business)
        assert business.subscription_status == "attention"


# ===========================================================================
# SUBSCRIPTION_NON_RENEWING
# ===========================================================================


@pytest.mark.api
class TestSubscriptionNonRenewing:
    def test_sets_non_renewing_status(self, client, db_session):
        user = UserFactory(email="nonrenew@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        business.subscription_status = "active"
        db_session.commit()

        event = _make_event("SUBSCRIPTION_NON_RENEWING", email="nonrenew@test.com")
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "subscription.not_renew"})

        assert resp.status_code == 200
        db_session.refresh(business)
        assert business.subscription_status == "non-renewing"


# ===========================================================================
# IDEMPOTENCY
# ===========================================================================


@pytest.mark.api
class TestWebhookIdempotency:
    def test_duplicate_reference_not_processed_twice(self, client, db_session):
        user = UserFactory(email="idem@test.com")
        business = BusinessFactory(user=user, user_id=user.id)
        PaymentTransactionFactory(
            business=business,
            business_id=business.id,
            reference="ref_dup_webhook",
        )
        db_session.commit()

        event = _make_event(
            "RENEWAL_SUCCESS",
            email="idem@test.com",
            reference="ref_dup_webhook",
        )
        svc = _mock_service_with_event(event)

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "charge.success"})

        assert resp.status_code == 200
        body = resp.json()
        assert "duplicate" in body["message"].lower() or "processed" in body["message"].lower()


# ===========================================================================
# INVALID SIGNATURE
# ===========================================================================


@pytest.mark.api
class TestWebhookInvalidSignature:
    def test_invalid_signature_returns_401(self, client, db_session):
        svc = MagicMock()
        svc.verify_webhook_signature.return_value = False

        with patch(FACTORY_PATH, return_value=svc):
            resp = _post_webhook(client, {"event": "charge.success"})

        assert resp.status_code == 401
        assert "invalid signature" in resp.json()["message"].lower()
