"""
Tests for WhatsApp API endpoints.

Covers: GET /whatsapp/webhook (Meta verification challenge),
        POST /whatsapp/webhook (incoming messages).
"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


SEND_MSG_PATH = "app.api.whatsapp.send_whatsapp_message"
PROCESS_MSG_PATH = "app.api.whatsapp._process_whatsapp_message"
SETTINGS_PATH = "app.api.whatsapp.settings"


def _whatsapp_text_payload(from_phone: str, phone_number_id: str, text: str) -> dict:
    """Build a minimal Meta Cloud API webhook payload for a text message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "BIZ_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": phone_number_id,
                            },
                            "messages": [
                                {
                                    "from": from_phone,
                                    "id": "wamid.test123",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def _whatsapp_image_payload(from_phone: str, phone_number_id: str) -> dict:
    """Build a Meta webhook payload for an image (non-text) message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "BIZ_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": phone_number_id,
                            },
                            "messages": [
                                {
                                    "from": from_phone,
                                    "id": "wamid.img123",
                                    "timestamp": "1700000000",
                                    "type": "image",
                                    "image": {
                                        "id": "img_id",
                                        "mime_type": "image/jpeg",
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


# ===========================================================================
# GET /whatsapp/webhook — Meta verification challenge
# ===========================================================================


@pytest.mark.api
class TestWhatsAppVerification:
    def test_valid_verify_token(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_VERIFY_TOKEN", "my_secret_token"
        )
        resp = client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "my_secret_token",
                "hub.challenge": "challenge_abc123",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "challenge_abc123"

    def test_wrong_verify_token_returns_403(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_VERIFY_TOKEN", "my_secret_token"
        )
        resp = client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_abc123",
            },
        )
        assert resp.status_code == 403

    def test_missing_mode_returns_403(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_VERIFY_TOKEN", "my_secret_token"
        )
        resp = client.get(
            "/whatsapp/webhook",
            params={
                "hub.verify_token": "my_secret_token",
                "hub.challenge": "challenge_abc123",
            },
        )
        assert resp.status_code == 403


# ===========================================================================
# POST /whatsapp/webhook — incoming text message
# ===========================================================================


@pytest.mark.api
class TestWhatsAppIncomingText:
    def test_text_message_processed(self, client, db_session, monkeypatch):
        """A text message should invoke _process_whatsapp_message."""
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_APP_SECRET", ""
        )

        payload = _whatsapp_text_payload("2348001234567", "PH_NUM_ID", "Hello!")

        with patch(PROCESS_MSG_PATH, new_callable=AsyncMock) as mock_process:
            resp = client.post(
                "/whatsapp/webhook",
                content=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        mock_process.assert_called_once()
        args = mock_process.call_args
        # positional: db, phone_number_id, from_phone, message_text
        assert args[0][1] == "PH_NUM_ID"
        assert args[0][2] == "2348001234567"
        assert args[0][3] == "Hello!"

    def test_empty_entry_returns_200(self, client, monkeypatch):
        """Payload with empty entry should return 200 silently."""
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_APP_SECRET", ""
        )
        resp = client.post(
            "/whatsapp/webhook",
            json={"object": "whatsapp_business_account", "entry": []},
        )
        assert resp.status_code == 200


# ===========================================================================
# POST /whatsapp/webhook — non-text message
# ===========================================================================


@pytest.mark.api
class TestWhatsAppNonTextMessage:
    def test_non_text_sends_unsupported_notice(self, client, db_session, monkeypatch):
        """An image message should trigger the unsupported notice path.

        The WhatsApp handler calls next(get_db()) directly rather than using
        FastAPI DI, so we mock the DB query and send_whatsapp_message to
        verify the unsupported-notice logic without relying on the test DB.
        """
        monkeypatch.setattr(
            "app.core.config.settings.WHATSAPP_APP_SECRET", ""
        )

        payload = _whatsapp_image_payload("2348009999999", "PH_IMG_ID")

        mock_widget = MagicMock()
        mock_widget.whatsapp_access_token = "tok_test"

        mock_db = MagicMock()
        # The handler queries WidgetSettings filtered by phone_number_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_widget

        with (
            patch("app.api.whatsapp.get_db", return_value=iter([mock_db])),
            patch(SEND_MSG_PATH, new_callable=AsyncMock) as mock_send,
        ):
            resp = client.post(
                "/whatsapp/webhook",
                content=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )

        assert resp.status_code == 200
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "PH_IMG_ID"  # phone_number_id
        assert call_args[0][2] == "2348009999999"  # to_phone
        assert "text messages" in call_args[0][3].lower()  # unsupported notice
