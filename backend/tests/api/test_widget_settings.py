"""
Tests for widget settings API endpoints (non-chat).
"""
import pytest

from tests.factories import (
    UserFactory,
    WidgetSettingsFactory,
    GuestUserFactory,
)


pytestmark = pytest.mark.api


class TestGetMySettings:
    """Tests for GET /widgets/my-settings."""

    def test_creates_widget_if_not_exists(self, authenticated_client, db_session):
        """Auto-creates a default widget when none exists."""
        client, user = authenticated_client

        resp = client.get("/widgets/my-settings")
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["theme"] == "light"
        assert data["primary_color"] == "#000000"
        assert data["public_widget_id"] is not None

    def test_returns_existing_widget(self, auth_client_with_widget):
        """Returns the pre-existing widget settings."""
        client, user, business, widget = auth_client_with_widget

        resp = client.get("/widgets/my-settings")
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["public_widget_id"] == widget.public_widget_id


class TestUpdateMySettings:
    """Tests for PUT /widgets/my-settings."""

    def test_update_theme_and_colors(self, auth_client_with_widget):
        client, user, business, widget = auth_client_with_widget

        resp = client.put(
            "/widgets/my-settings",
            json={"theme": "dark", "primary_color": "#FF5500"},
        )
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["theme"] == "dark"
        assert data["primary_color"] == "#FF5500"

    def test_update_limits(self, auth_client_with_widget):
        client, user, business, widget = auth_client_with_widget

        resp = client.put(
            "/widgets/my-settings",
            json={"max_messages_per_session": 100, "max_sessions_per_day": 10},
        )
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert data["max_messages_per_session"] == 100
        assert data["max_sessions_per_day"] == 10

    def test_update_welcome_message(self, auth_client_with_widget):
        client, user, business, widget = auth_client_with_widget

        resp = client.put(
            "/widgets/my-settings",
            json={"welcome_message": "Welcome!"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["welcome_message"] == "Welcome!"

    def test_welcome_message_too_long(self, auth_client_with_widget):
        client, user, business, widget = auth_client_with_widget

        resp = client.put(
            "/widgets/my-settings",
            json={"welcome_message": "x" * 1001},
        )
        assert resp.status_code == 400

    def test_creates_widget_on_update_if_missing(self, authenticated_client):
        """PUT auto-creates widget if it doesn't exist yet."""
        client, user = authenticated_client

        resp = client.put(
            "/widgets/my-settings",
            json={"theme": "dark"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["theme"] == "dark"


class TestGetWidgetConfig:
    """Tests for GET /widgets/config/{public_widget_id} (public)."""

    def test_returns_config(self, client, db_session):
        user = UserFactory()
        widget = WidgetSettingsFactory(user=user, user_id=user.id)
        db_session.commit()

        resp = client.get(f"/widgets/config/{widget.public_widget_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["public_widget_id"] == widget.public_widget_id
        assert data["theme"] == widget.theme

    def test_404_for_unknown_widget(self, client):
        resp = client.get("/widgets/config/nonexistent-widget-id")
        assert resp.status_code == 404


class TestGetGuests:
    """Tests for GET /widgets/guests."""

    def test_list_guests(self, auth_client_with_widget, db_session):
        client, user, business, widget = auth_client_with_widget

        GuestUserFactory(widget=widget, widget_id=widget.id, name="Alice")
        GuestUserFactory(widget=widget, widget_id=widget.id, name="Bob")
        db_session.commit()

        resp = client.get("/widgets/guests")
        assert resp.status_code == 200

        data = resp.json()["data"]
        assert len(data) == 2
        names = {g["name"] for g in data}
        assert "Alice" in names
        assert "Bob" in names

    def test_empty_when_no_widget(self, authenticated_client):
        """Returns empty list when user has no widget."""
        client, user = authenticated_client
        resp = client.get("/widgets/guests")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestToggleLeadStatus:
    """Tests for PUT /widgets/guests/{id}/lead."""

    def test_toggle_lead_on(self, auth_client_with_widget, db_session):
        client, user, business, widget = auth_client_with_widget

        guest = GuestUserFactory(widget=widget, widget_id=widget.id, is_lead=False)
        db_session.commit()

        resp = client.put(
            f"/widgets/guests/{guest.id}/lead",
            json={"is_lead": True},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_lead"] is True

    def test_toggle_lead_off(self, auth_client_with_widget, db_session):
        client, user, business, widget = auth_client_with_widget

        guest = GuestUserFactory(widget=widget, widget_id=widget.id, is_lead=True)
        db_session.commit()

        resp = client.put(
            f"/widgets/guests/{guest.id}/lead",
            json={"is_lead": False},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_lead"] is False

    def test_guest_not_found(self, auth_client_with_widget):
        client, user, business, widget = auth_client_with_widget

        resp = client.put(
            "/widgets/guests/nonexistent-guest-id/lead",
            json={"is_lead": True},
        )
        assert resp.status_code == 404
