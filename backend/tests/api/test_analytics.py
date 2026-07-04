"""
Tests for the analytics API endpoints.
"""
import pytest

from tests.factories import (
    UserFactory,
    BusinessFactory,
    WidgetSettingsFactory,
    GuestUserFactory,
    ChatSessionFactory,
    GuestMessageFactory,
)


pytestmark = pytest.mark.api


@pytest.fixture
def analytics_setup(db_session):
    """Create user + business + widget + guest + sessions for analytics."""
    user = UserFactory()
    business = BusinessFactory(user=user, user_id=user.id)
    widget = WidgetSettingsFactory(user=user, user_id=user.id)
    guest = GuestUserFactory(widget=widget, widget_id=widget.id, is_lead=True)

    s1 = ChatSessionFactory(
        guest=guest, guest_id=guest.id,
        top_intent="pricing",
        country="Nigeria", city="Lagos",
        referrer="https://google.com",
        session_duration=120,
    )
    s2 = ChatSessionFactory(
        guest=guest, guest_id=guest.id,
        top_intent="support",
        country="Nigeria", city="Abuja",
        referrer="https://twitter.com",
        session_duration=60,
    )
    db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(subject=user.id)
    return {
        "token": token,
        "user": user,
        "business": business,
        "widget": widget,
        "guest": guest,
        "sessions": [s1, s2],
    }


class TestOverview:
    """Tests for GET /analytics/overview."""

    def test_returns_metrics(self, client, db_session, analytics_setup):
        token = analytics_setup["token"]
        resp = client.get(
            "/analytics/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_sessions"] == 2
        assert data["total_guests"] >= 1
        assert data["leads_captured"] >= 1
        assert "avg_session_duration" in data

    def test_no_widget_returns_zeros(self, authenticated_client):
        """User with no widget gets zero metrics."""
        client, user = authenticated_client
        resp = client.get("/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_sessions"] == 0
        assert data["total_guests"] == 0


class TestIntents:
    """Tests for GET /analytics/intents."""

    def test_returns_top_intents(self, client, analytics_setup):
        resp = client.get(
            "/analytics/intents",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 2
        intents = {d["intent"] for d in data}
        assert "pricing" in intents
        assert "support" in intents

    def test_no_widget_returns_empty(self, authenticated_client):
        client, _ = authenticated_client
        resp = client.get("/analytics/intents")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestLocations:
    """Tests for GET /analytics/locations."""

    def test_returns_locations(self, client, analytics_setup):
        resp = client.get(
            "/analytics/locations",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 2
        cities = {d["city"] for d in data}
        assert "Lagos" in cities
        assert "Abuja" in cities

    def test_no_widget_returns_empty(self, authenticated_client):
        client, _ = authenticated_client
        resp = client.get("/analytics/locations")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestSources:
    """Tests for GET /analytics/sources."""

    def test_returns_sources(self, client, analytics_setup):
        resp = client.get(
            "/analytics/sources",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 2
        sources = {d["source"] for d in data}
        assert "https://google.com" in sources
        assert "https://twitter.com" in sources

    def test_no_widget_returns_empty(self, authenticated_client):
        client, _ = authenticated_client
        resp = client.get("/analytics/sources")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestTrend:
    """Tests for GET /analytics/trend."""

    def test_returns_daily_counts(self, client, analytics_setup):
        resp = client.get(
            "/analytics/trend",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "date" in data[0]
        assert "count" in data[0]

    def test_no_widget_returns_empty(self, authenticated_client):
        client, _ = authenticated_client
        resp = client.get("/analytics/trend")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestSessions:
    """Tests for GET /analytics/sessions."""

    def test_returns_recent_sessions(self, client, analytics_setup):
        resp = client.get(
            "/analytics/sessions",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 2
        assert "guest_name" in data[0]
        assert "top_intent" in data[0]

    def test_no_widget_returns_empty(self, authenticated_client):
        client, _ = authenticated_client
        resp = client.get("/analytics/sessions")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestSessionDetail:
    """Tests for GET /analytics/sessions/{id}."""

    def test_returns_session_detail(self, client, db_session, analytics_setup):
        session = analytics_setup["sessions"][0]
        guest = analytics_setup["guest"]

        GuestMessageFactory(
            guest=guest, guest_id=guest.id,
            session=session, session_id=session.id,
            sender="guest", message_text="Hello",
        )
        db_session.commit()

        resp = client.get(
            f"/analytics/sessions/{session.id}",
            headers={"Authorization": f"Bearer {analytics_setup['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == session.id
        assert data["guest"]["id"] == guest.id
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"

    def test_session_not_found(self, authenticated_client):
        client, _ = authenticated_client
        # User has no widget, so 404 on "Widget not found"
        resp = client.get("/analytics/sessions/nonexistent-id")
        assert resp.status_code == 404
