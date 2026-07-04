"""Unit tests for app.services.whatsapp_service module.

Tests webhook signature verification (HMAC-SHA256) and the
send_whatsapp_message() async function with mocked httpx.
"""

import hmac
import hashlib
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.whatsapp_service import verify_webhook_signature, send_whatsapp_message


def _make_signature(secret: str, payload: bytes) -> str:
    """Helper to compute a valid sha256= prefixed HMAC signature."""
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


# ---------------------------------------------------------------------------
# verify_webhook_signature
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature()."""

    def test_valid_signature_returns_true(self):
        """A correctly computed sha256 signature should return True."""
        payload = b'{"object":"whatsapp_business_account"}'
        secret = "my-app-secret"
        sig = _make_signature(secret, payload)
        assert verify_webhook_signature(payload, sig, secret) is True

    def test_invalid_signature_returns_false(self):
        """An incorrect signature should return False."""
        payload = b'{"object":"whatsapp_business_account"}'
        bad_sig = "sha256=" + "a" * 64
        assert verify_webhook_signature(payload, bad_sig, "my-app-secret") is False

    def test_missing_sha256_prefix_returns_false(self):
        """Signature without 'sha256=' prefix should return False."""
        payload = b"hello"
        secret = "secret"
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # No prefix
        assert verify_webhook_signature(payload, digest, secret) is False

    def test_empty_signature_returns_false(self):
        """Empty signature string should return False."""
        assert verify_webhook_signature(b"data", "", "secret") is False

    def test_none_signature_returns_false(self):
        """None signature should return False."""
        assert verify_webhook_signature(b"data", None, "secret") is False

    def test_tampered_payload_returns_false(self):
        """Signature valid for original payload should fail on tampered payload."""
        original = b"original"
        secret = "sec"
        sig = _make_signature(secret, original)
        assert verify_webhook_signature(b"tampered", sig, secret) is False


# ---------------------------------------------------------------------------
# send_whatsapp_message
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSendWhatsAppMessage:
    """Tests for the async send_whatsapp_message() function."""

    @pytest.mark.asyncio
    async def test_send_message_success_returns_true(self):
        """When the API returns 200, send_whatsapp_message should return True."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.whatsapp_service.httpx.AsyncClient", return_value=mock_client):
            result = await send_whatsapp_message(
                phone_number_id="12345",
                access_token="token-abc",
                to_phone="+1234567890",
                text="Hello!",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_message_failure_returns_false(self):
        """When the API returns non-200, send_whatsapp_message should return False."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.whatsapp_service.httpx.AsyncClient", return_value=mock_client):
            result = await send_whatsapp_message(
                phone_number_id="12345",
                access_token="token-abc",
                to_phone="+1234567890",
                text="Hello!",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_posts_correct_url(self):
        """The request should be sent to the correct WhatsApp Cloud API URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.whatsapp_service.httpx.AsyncClient", return_value=mock_client):
            await send_whatsapp_message(
                phone_number_id="99999",
                access_token="tok",
                to_phone="+0",
                text="hi",
            )

        call_args = mock_client.post.call_args
        assert "99999" in call_args[0][0]
        assert "graph.facebook.com" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_message_includes_bearer_token(self):
        """The Authorization header should include the provided access_token."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.whatsapp_service.httpx.AsyncClient", return_value=mock_client):
            await send_whatsapp_message(
                phone_number_id="1",
                access_token="my-secret-token",
                to_phone="+0",
                text="hi",
            )

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["Authorization"] == "Bearer my-secret-token"
