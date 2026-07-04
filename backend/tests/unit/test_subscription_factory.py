"""Unit tests for app.services.subscription.factory module.

Tests SubscriptionServiceFactory.get_service() returns the correct provider
or raises ValueError for unknown providers.
"""

import pytest
from unittest.mock import patch

from app.services.subscription.factory import SubscriptionServiceFactory
from app.services.subscription.paystack import PaystackSubscriptionService


@pytest.mark.unit
class TestSubscriptionServiceFactory:
    """Tests for SubscriptionServiceFactory.get_service()."""

    @patch.object(PaystackSubscriptionService, "__init__", return_value=None)
    def test_get_service_paystack_returns_correct_type(self, mock_init):
        """get_service('paystack') should return a PaystackSubscriptionService."""
        service = SubscriptionServiceFactory.get_service("paystack")
        assert isinstance(service, PaystackSubscriptionService)

    @patch.object(PaystackSubscriptionService, "__init__", return_value=None)
    def test_get_service_default_is_paystack(self, mock_init):
        """get_service() with no args should default to paystack."""
        service = SubscriptionServiceFactory.get_service()
        assert isinstance(service, PaystackSubscriptionService)

    @patch.object(PaystackSubscriptionService, "__init__", return_value=None)
    def test_get_service_case_insensitive(self, mock_init):
        """Provider name should be case-insensitive."""
        service = SubscriptionServiceFactory.get_service("PAYSTACK")
        assert isinstance(service, PaystackSubscriptionService)

    def test_get_service_unknown_provider_raises_value_error(self):
        """Unknown provider should raise ValueError."""
        with pytest.raises(ValueError, match="not supported"):
            SubscriptionServiceFactory.get_service("stripe")

    def test_get_service_empty_string_raises_value_error(self):
        """Empty string provider should raise ValueError."""
        with pytest.raises(ValueError, match="not supported"):
            SubscriptionServiceFactory.get_service("")
