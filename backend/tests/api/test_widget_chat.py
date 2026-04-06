"""
Tests for widget chat-flow API endpoints.
All AI calls are mocked to avoid hitting real services.
"""
import pytest
from unittest.mock import patch, AsyncMock

from tests.factories import (
    UserFactory,
    BusinessFactory,
    WidgetSettingsFactory,
    GuestUserFactory,
    ChatSessionFactory,
)


pytestmark = pytest.mark.api

# Shared mock target
RUN_CONVERSATION = "app.api.widget.run_conversation"


@pytest.fixture
def widget_env(db_session):
    """Reusable widget environment: user + business + widget, all committed."""
    user = UserFactory()
    business = BusinessFactory(
        user=user,
        user_id=user.id,
        allocated_ai_responses=100,
        used_ai_responses=0,
        allocated_daily_sessions=50,
        allocated_messages_per_session=10,
    )
    widget = WidgetSettingsFactory(
        user=user,
        user_id=user.id,
        max_messages_per_session=5,
        max_sessions_per_day=3,
    )
    db_session.commit()
    return {
        "user": user,
        "business": business,
        "widget": widget,
        "db": db_session,
    }


class TestStartGuestSession:
    """Tests for POST /widgets/guest/start/{public_widget_id}."""

    def test_start_creates_guest(self, client, widget_env):
        widget = widget_env["widget"]

        resp = client.post(
            f"/widgets/guest/start/{widget.public_widget_id}",
            json={"name": "Test Guest", "email": "guest@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["guest_id"] is not None
        assert data["status"] == "ready"
        assert data["widget_owner_id"] == widget.user_id

    def test_start_reuses_existing_guest_by_email(self, client, db_session, widget_env):
        widget = widget_env["widget"]
        guest = GuestUserFactory(
            widget=widget, widget_id=widget.id,
            name="Existing", email="reuse@example.com",
        )
        db_session.commit()

        resp = client.post(
            f"/widgets/guest/start/{widget.public_widget_id}",
            json={"name": "New Name", "email": "reuse@example.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["guest_id"] == guest.id

    def test_404_for_unknown_widget(self, client):
        resp = client.post(
            "/widgets/guest/start/nonexistent-widget",
            json={"name": "Test"},
        )
        assert resp.status_code == 404


class TestInitGuestSession:
    """Tests for POST /widgets/guest/session/init/{public_widget_id}."""

    @patch(RUN_CONVERSATION, new_callable=AsyncMock, return_value="Hello from AI")
    def test_init_session_with_first_message(self, mock_ai, client, db_session, widget_env):
        widget = widget_env["widget"]
        guest = GuestUserFactory(widget=widget, widget_id=widget.id)
        db_session.commit()

        resp = client.post(
            f"/widgets/guest/session/init/{widget.public_widget_id}",
            json={
                "guest_id": guest.id,
                "message": "Hi there",
                "origin": "manual",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["message"]["sender"] == "guest"
        assert data["message"]["message_text"] == "Hi there"
        assert data["response"]["sender"] == "ai"
        assert data["response"]["message_text"] == "Hello from AI"
        mock_ai.assert_called_once()

    @patch(RUN_CONVERSATION, new_callable=AsyncMock, return_value="OK")
    def test_daily_session_limit(self, mock_ai, client, db_session, widget_env):
        """Returns 429 when the business daily session limit is reached."""
        widget = widget_env["widget"]
        business = widget_env["business"]
        # Set a very low limit
        business.allocated_daily_sessions = 1
        db_session.commit()

        guest = GuestUserFactory(widget=widget, widget_id=widget.id)
        db_session.commit()

        # Create one session already today
        ChatSessionFactory(guest=guest, guest_id=guest.id)
        db_session.commit()

        resp = client.post(
            f"/widgets/guest/session/init/{widget.public_widget_id}",
            json={"guest_id": guest.id, "message": "Hello", "origin": "manual"},
        )
        assert resp.status_code == 429
        body = resp.json()
        # HTTPException detail may be in "detail" or wrapped in "message"
        detail_text = body.get("detail") or body.get("message", "")
        assert "daily session limit" in detail_text.lower()

    def test_init_404_unknown_guest(self, client, widget_env):
        widget = widget_env["widget"]
        resp = client.post(
            f"/widgets/guest/session/init/{widget.public_widget_id}",
            json={"guest_id": "nonexistent-id", "message": "Hi", "origin": "manual"},
        )
        assert resp.status_code == 404


class TestChatInSession:
    """Tests for POST /widgets/chat/{public_widget_id}/session/{session_id}."""

    @patch(RUN_CONVERSATION, new_callable=AsyncMock, return_value="AI reply")
    def test_send_message(self, mock_ai, client, db_session, widget_env):
        widget = widget_env["widget"]
        guest = GuestUserFactory(widget=widget, widget_id=widget.id)
        session = ChatSessionFactory(guest=guest, guest_id=guest.id)
        db_session.commit()

        resp = client.post(
            f"/widgets/chat/{widget.public_widget_id}/session/{session.id}",
            json={"message": "What are your prices?"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["message"]["message_text"] == "What are your prices?"
        assert data["response"]["message_text"] == "AI reply"
        mock_ai.assert_called_once()

    @patch(RUN_CONVERSATION, new_callable=AsyncMock, return_value="OK")
    def test_message_limit_enforcement(self, mock_ai, client, db_session, widget_env):
        """Returns a limit-reached message when user_messages >= max."""
        widget = widget_env["widget"]
        guest = GuestUserFactory(widget=widget, widget_id=widget.id)
        session = ChatSessionFactory(
            guest=guest, guest_id=guest.id,
            user_messages=5,  # equals widget.max_messages_per_session
            total_messages=10,
        )
        db_session.commit()

        resp = client.post(
            f"/widgets/chat/{widget.public_widget_id}/session/{session.id}",
            json={"message": "One more question"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "limit reached" in data["response"]["message_text"].lower()
        # AI should NOT have been called
        mock_ai.assert_not_called()

    def test_ai_credit_exhaustion(self, client, db_session, widget_env):
        """Returns credit-exhaustion message when business has no remaining credits."""
        widget = widget_env["widget"]
        business = widget_env["business"]
        business.allocated_ai_responses = 10
        business.used_ai_responses = 10  # zero remaining
        db_session.commit()

        guest = GuestUserFactory(widget=widget, widget_id=widget.id)
        session = ChatSessionFactory(guest=guest, guest_id=guest.id)
        db_session.commit()

        resp = client.post(
            f"/widgets/chat/{widget.public_widget_id}/session/{session.id}",
            json={"message": "Hello"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "insufficient ai credits" in data["response"]["message_text"].lower()

    def test_404_unknown_session(self, client, widget_env):
        widget = widget_env["widget"]
        resp = client.post(
            f"/widgets/chat/{widget.public_widget_id}/session/bad-session-id",
            json={"message": "Hi"},
        )
        assert resp.status_code == 404

    def test_404_unknown_widget(self, client):
        resp = client.post(
            "/widgets/chat/bad-widget/session/bad-session",
            json={"message": "Hi"},
        )
        assert resp.status_code == 404
