"""Unit tests for app.services.subscription.paystack module.

Tests webhook signature verification and webhook event parsing.
No HTTP calls are made -- all Paystack API interactions are out of scope.
"""

import hmac
import hashlib
import pytest
from unittest.mock import patch

from app.services.subscription.paystack import PaystackSubscriptionService


@pytest.fixture
def service():
    """Create a PaystackSubscriptionService with a known secret key."""
    with patch("app.services.subscription.paystack.settings") as mock_settings:
        mock_settings.PAYSTACK_SECRET_KEY = "test-paystack-secret"
        svc = PaystackSubscriptionService()
    return svc


def _compute_signature(secret: str, body: bytes) -> str:
    """Helper to compute a valid HMAC-SHA512 signature."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha512,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestVerifyWebhookSignature:
    """Tests for PaystackSubscriptionService.verify_webhook_signature()."""

    def test_verify_webhook_signature_valid(self, service):
        """Valid HMAC-SHA512 signature should return True."""
        body = b'{"event":"charge.success"}'
        sig = _compute_signature("test-paystack-secret", body)
        headers = {"x-paystack-signature": sig}
        assert service.verify_webhook_signature(headers, body) is True

    def test_verify_webhook_signature_invalid(self, service):
        """Incorrect signature should return False."""
        body = b'{"event":"charge.success"}'
        headers = {"x-paystack-signature": "deadbeef" * 16}
        assert service.verify_webhook_signature(headers, body) is False

    def test_verify_webhook_signature_missing_header(self, service):
        """Missing x-paystack-signature header should return False."""
        body = b'{"event":"charge.success"}'
        headers = {}
        assert service.verify_webhook_signature(headers, body) is False

    def test_verify_webhook_signature_tampered_body(self, service):
        """Signature computed for different body should not match."""
        original_body = b'{"event":"charge.success"}'
        tampered_body = b'{"event":"charge.fail"}'
        sig = _compute_signature("test-paystack-secret", original_body)
        headers = {"x-paystack-signature": sig}
        assert service.verify_webhook_signature(headers, tampered_body) is False


# ---------------------------------------------------------------------------
# Webhook event parsing
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestParseWebhookEvent:
    """Tests for PaystackSubscriptionService.parse_webhook_event()."""

    def test_parse_charge_success_event_type(self, service):
        """charge.success should map to RENEWAL_SUCCESS."""
        payload = {
            "event": "charge.success",
            "data": {
                "customer": {"email": "a@b.com", "customer_code": "CUS_1"},
                "subscription_code": "SUB_1",
                "plan": {"plan_code": "PLN_1"},
                "amount": 5000,
                "reference": "ref-123",
                "authorization": {"authorization_code": "AUTH_xyz"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "RENEWAL_SUCCESS"

    def test_parse_charge_success_extracts_authorization_code(self, service):
        """charge.success should extract authorization_code."""
        payload = {
            "event": "charge.success",
            "data": {
                "customer": {"email": "a@b.com", "customer_code": "CUS_1"},
                "authorization": {"authorization_code": "AUTH_abc"},
                "plan": {},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["authorization_code"] == "AUTH_abc"

    def test_parse_subscription_create_event_type(self, service):
        """subscription.create should map to SUBSCRIPTION_CREATED."""
        payload = {
            "event": "subscription.create",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_2"},
                "subscription_code": "SUB_new",
                "email_token": "tok_email",
                "plan": {"plan_code": "PLN_2"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "SUBSCRIPTION_CREATED"

    def test_parse_subscription_create_extracts_email_token(self, service):
        """subscription.create should extract email_token."""
        payload = {
            "event": "subscription.create",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_2"},
                "subscription_code": "SUB_new",
                "email_token": "tok_email",
                "plan": {"plan_code": "PLN_2"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["email_token"] == "tok_email"

    def test_parse_subscription_disable_event_type(self, service):
        """subscription.disable should map to SUBSCRIPTION_CANCELLED."""
        payload = {
            "event": "subscription.disable",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_3"},
                "subscription_code": "SUB_old",
                "plan": {"plan_code": "PLN_3"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "SUBSCRIPTION_CANCELLED"

    def test_parse_invoice_payment_failed_event_type(self, service):
        """invoice.payment_failed should map to PAYMENT_FAILED."""
        payload = {
            "event": "invoice.payment_failed",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_4"},
                "subscription": {"subscription_code": "SUB_fail"},
                "plan": {"plan_code": "PLN_4"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "PAYMENT_FAILED"

    def test_parse_invoice_payment_failed_extracts_subscription_code(self, service):
        """invoice.payment_failed should extract subscription_code from nested data."""
        payload = {
            "event": "invoice.payment_failed",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_4"},
                "subscription": {"subscription_code": "SUB_nested"},
                "plan": {},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["subscription_code"] == "SUB_nested"

    def test_parse_subscription_not_renew_event_type(self, service):
        """subscription.not_renew should map to SUBSCRIPTION_NON_RENEWING."""
        payload = {
            "event": "subscription.not_renew",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_5"},
                "subscription_code": "SUB_nr",
                "plan": {"plan_code": "PLN_5"},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "SUBSCRIPTION_NON_RENEWING"

    def test_parse_unknown_event_type(self, service):
        """An unrecognised event type should map to UNKNOWN."""
        payload = {
            "event": "refund.processed",
            "data": {
                "customer": {"email": "u@x.com", "customer_code": "CUS_6"},
                "plan": {},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["event_type"] == "UNKNOWN"

    def test_parse_event_preserves_raw_payload(self, service):
        """raw_payload should contain the original webhook payload."""
        payload = {
            "event": "charge.success",
            "data": {"customer": {}, "plan": {}},
        }
        result = service.parse_webhook_event(payload)
        assert result["raw_payload"] is payload

    def test_parse_event_extracts_customer_email(self, service):
        """customer_email should be extracted from data.customer.email."""
        payload = {
            "event": "charge.success",
            "data": {
                "customer": {"email": "hello@world.com", "customer_code": "C1"},
                "plan": {},
                "authorization": {},
            },
        }
        result = service.parse_webhook_event(payload)
        assert result["customer_email"] == "hello@world.com"
