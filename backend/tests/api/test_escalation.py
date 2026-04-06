"""
Tests for the escalation API endpoints.
"""
import pytest
import uuid

from tests.factories import (
    UserFactory,
    BusinessFactory,
    WidgetSettingsFactory,
    GuestUserFactory,
    ChatSessionFactory,
    EscalationFactory,
    GuestMessageFactory,
)
from app.models.escalation import EscalationStatus


pytestmark = pytest.mark.api


def _make_escalation_chain(db_session):
    """Helper: creates user -> business -> widget -> guest -> session -> escalation."""
    user = UserFactory()
    business = BusinessFactory(user=user, user_id=user.id)
    widget = WidgetSettingsFactory(user=user, user_id=user.id)
    guest = GuestUserFactory(widget=widget, widget_id=widget.id)
    session = ChatSessionFactory(guest=guest, guest_id=guest.id)
    escalation = EscalationFactory(
        business=business,
        business_id=business.id,
        session=session,
        session_id=session.id,
    )
    db_session.commit()
    return user, business, widget, guest, session, escalation


class TestListEscalations:
    """Tests for GET /escalations/?business_id=X."""

    def test_list_escalations(self, client, db_session):
        """Returns escalations for the given business."""
        user, business, widget, guest, session, esc = _make_escalation_chain(db_session)

        resp = client.get(f"/escalations/?business_id={business.id}")
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert len(data) == 1
        assert data[0]["id"] == esc.id
        assert data[0]["business_id"] == business.id
        assert data[0]["status"] == EscalationStatus.PENDING.value

    def test_list_empty_for_other_business(self, client, db_session):
        """Returns empty list when no escalations match the business."""
        _make_escalation_chain(db_session)

        resp = client.get(f"/escalations/?business_id={str(uuid.uuid4())}")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestGetEscalationDetails:
    """Tests for GET /escalations/{id}."""

    def test_get_detail_with_messages(self, client, db_session):
        """Returns escalation detail including guest info and messages."""
        user, business, widget, guest, session, esc = _make_escalation_chain(db_session)

        GuestMessageFactory(
            guest=guest, guest_id=guest.id,
            session=session, session_id=session.id,
            sender="guest", message_text="I need help",
        )
        GuestMessageFactory(
            guest=guest, guest_id=guest.id,
            session=session, session_id=session.id,
            sender="ai", message_text="Sure, how can I help?",
        )
        db_session.commit()

        resp = client.get(f"/escalations/{esc.id}")
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["id"] == esc.id
        assert data["session_id"] == session.id
        assert data["guest"]["name"] == guest.name
        assert len(data["messages"]) == 2
        assert data["messages"][0]["message"] == "I need help"

    def test_404_for_nonexistent(self, client, db_session):
        """Returns 404 for a non-existent escalation ID."""
        resp = client.get(f"/escalations/{str(uuid.uuid4())}")
        assert resp.status_code == 404


class TestResolveEscalation:
    """Tests for POST /escalations/{id}/resolve."""

    def test_resolve(self, client, db_session):
        """Marks an escalation as resolved."""
        user, business, widget, guest, session, esc = _make_escalation_chain(db_session)

        resp = client.post(f"/escalations/{esc.id}/resolve")
        assert resp.status_code == 200

        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["status"] == EscalationStatus.RESOLVED.value

    def test_resolve_404(self, client, db_session):
        """Returns 404 when resolving a non-existent escalation."""
        resp = client.post(f"/escalations/{str(uuid.uuid4())}/resolve")
        assert resp.status_code == 404
