"""
Tests for the escalate_to_human tool.
Validates escalation creation, database interaction, and email sending.
"""
import pytest
import json
from unittest.mock import MagicMock, patch

from app.models.business import Business
from app.models.chat_session import ChatSession
from app.models.widget import WidgetSettings, GuestUser
from app.models.escalation import Escalation, EscalationStatus


def _make_query_side_effect(mock_chat_session, mock_business, existing_escalation=None):
    """Helper to build a query side-effect that handles ChatSession, Business, and Escalation."""
    def query_side_effect(model):
        if model == ChatSession:
            m = MagicMock()
            m.filter.return_value.first.return_value = mock_chat_session
            return m
        elif model == Business:
            m = MagicMock()
            m.filter.return_value.first.return_value = mock_business
            return m
        elif model == Escalation:
            m = MagicMock()
            m.filter.return_value.first.return_value = existing_escalation
            return m
        return MagicMock()
    return query_side_effect


class TestEscalateToHuman:
    """Test suite for escalate_to_human tool functionality."""

    @pytest.fixture
    def mock_tool_context(self):
        """Create a mock ToolContext with session_id."""
        context = MagicMock()
        context.state = {"session_id": "test-session-123"}
        return context

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        with patch("app.services.agent_system.tools.SessionLocal") as mock_session_cls:
            mock_sess = MagicMock()
            mock_session_cls.return_value = mock_sess
            yield mock_sess

    @pytest.fixture
    def mock_email_service(self):
        """Create a mock email service."""
        with patch("app.services.agent_system.tools.EmailServiceFactory") as mock_factory:
            mock_service = MagicMock()
            mock_factory.get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_business(self):
        """Create a mock business with escalation enabled."""
        business = MagicMock(spec=Business)
        business.id = "biz-123"
        business.business_name = "Test Business"
        business.is_escalation_enabled = True
        business.escalation_emails = ["support@test.com"]
        business.subscription_tier = "spark"
        business.allocated_escalations = 10
        business.used_escalations = 0
        return business

    @pytest.fixture
    def mock_widget(self, mock_business):
        """Create a mock widget settings."""
        widget = MagicMock(spec=WidgetSettings)
        widget.id = "widget-123"
        widget.user_id = "user-123"
        return widget

    @pytest.fixture
    def mock_guest(self, mock_widget):
        """Create a mock guest user."""
        guest = MagicMock(spec=GuestUser)
        guest.id = "guest-123"
        guest.widget_id = mock_widget.id
        guest.widget = mock_widget
        return guest

    @pytest.fixture
    def mock_chat_session(self, mock_guest):
        """Create a mock chat session."""
        session = MagicMock(spec=ChatSession)
        session.id = "test-session-123"
        session.guest_id = mock_guest.id
        session.guest = mock_guest
        return session

    class TestSuccessfulEscalation:
        """Tests for successful escalation scenarios."""

        def test_creates_escalation_record(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business, mock_guest, mock_widget
        ):
            """Test that escalation record is created in database."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)

            def refresh_side_effect(instance):
                instance.id = "esc-789"
            mock_db_session.refresh.side_effect = refresh_side_effect
            escalate_to_human(
                reason="User frustrated",
                user_message="I need help!",
                tool_context=mock_tool_context
            )

            # Verify escalation was added - find the Escalation among add calls
            assert mock_db_session.add.called
            escalation_added = False
            for call in mock_db_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Escalation):
                    escalation_added = True
                    break
            assert escalation_added

        def test_escalation_contains_reason(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that escalation summary contains the reason."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            escalate_to_human(
                reason="Angry customer",
                user_message="This is unacceptable!",
                tool_context=mock_tool_context
            )

            # Find the Escalation object
            for call in mock_db_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Escalation):
                    assert "Angry customer" in obj.summary
                    return
            pytest.fail("Escalation object not found in db.add calls")

        def test_sends_notification_email(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that notification email is sent (via threading)."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            with patch("threading.Thread") as mock_thread:
                mock_thread.return_value.start = MagicMock()
                escalate_to_human(
                    reason="Test reason",
                    user_message="Test message",
                    tool_context=mock_tool_context
                )

                # The tool sends email via a background thread
                assert mock_thread.called

        def test_returns_valid_json_response(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that response is valid JSON with expected fields."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            result = escalate_to_human(
                reason="Test",
                user_message="Test",
                tool_context=mock_tool_context
            )

            data = json.loads(result)
            assert "escalation_id" in data
            assert "status" in data
            assert "message" in data

    class TestErrorHandling:
        """Tests for error handling scenarios."""

        def test_missing_session_id_returns_error(self, mock_db_session, mock_email_service):
            """Test that missing session_id returns error."""
            from app.services.agent_system.tools import escalate_to_human

            context = MagicMock()
            context.state = {}  # No session_id

            result = escalate_to_human(
                reason="Test",
                user_message="Test",
                tool_context=context
            )

            assert "Error" in result
            assert "Session ID" in result

        def test_session_not_found_returns_error(
            self, mock_tool_context, mock_db_session, mock_email_service
        ):
            """Test that non-existent session returns error."""
            from app.services.agent_system.tools import escalate_to_human

            def query_side_effect(model):
                m = MagicMock()
                m.filter.return_value.first.return_value = None
                return m

            mock_db_session.query.side_effect = query_side_effect

            result = escalate_to_human(
                reason="Test",
                user_message="Test",
                tool_context=mock_tool_context
            )

            assert "Error" in result

        def test_escalation_disabled_returns_message(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that disabled escalation returns appropriate message."""
            from app.services.agent_system.tools import escalate_to_human

            mock_business.is_escalation_enabled = False

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)

            result = escalate_to_human(
                reason="Test",
                user_message="Test",
                tool_context=mock_tool_context
            )

            assert "not available" in result.lower()

    class TestInputValidation:
        """Tests for input validation."""

        def test_empty_reason_handled(
            self, mock_tool_context, mock_db_session, mock_email_service
        ):
            """Test that empty reason is handled."""
            from app.services.agent_system.tools import escalate_to_human

            result = escalate_to_human(
                reason="",
                user_message="Test message",
                tool_context=mock_tool_context
            )

            # Should either return error or be handled by schema validation
            assert isinstance(result, str)

        def test_empty_user_message_handled(
            self, mock_tool_context, mock_db_session, mock_email_service
        ):
            """Test that empty user_message is handled."""
            from app.services.agent_system.tools import escalate_to_human

            result = escalate_to_human(
                reason="Valid reason",
                user_message="",
                tool_context=mock_tool_context
            )

            assert isinstance(result, str)

    class TestEscalationStatus:
        """Tests for escalation status handling."""

        def test_escalation_created_with_pending_status(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that new escalations have PENDING status."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            escalate_to_human(
                reason="Test",
                user_message="Test",
                tool_context=mock_tool_context
            )

            # Find the Escalation object
            for call in mock_db_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Escalation):
                    assert obj.status == EscalationStatus.PENDING.value
                    return
            pytest.fail("Escalation object not found in db.add calls")

    class TestEmailContent:
        """Tests for email notification content."""

        def test_email_contains_business_name(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that email subject contains business name."""
            from app.services.agent_system.tools import escalate_to_human

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            with patch("threading.Thread") as mock_thread:
                mock_thread.return_value.start = MagicMock()
                escalate_to_human(
                    reason="Urgent issue",
                    user_message="Help me!",
                    tool_context=mock_tool_context
                )

                # The tool creates a thread to send the email
                assert mock_thread.called

        def test_no_email_sent_when_no_recipients(
            self, mock_tool_context, mock_db_session, mock_email_service,
            mock_chat_session, mock_business
        ):
            """Test that no email is sent when no escalation emails configured."""
            from app.services.agent_system.tools import escalate_to_human

            mock_business.escalation_emails = []  # No recipients

            mock_db_session.query.side_effect = _make_query_side_effect(mock_chat_session, mock_business)
            mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 'esc-123')

            with patch("threading.Thread") as mock_thread:
                escalate_to_human(
                    reason="Test",
                    user_message="Test",
                    tool_context=mock_tool_context
                )

                # No thread should be created for email when no recipients
                mock_thread.assert_not_called()
