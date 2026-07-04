"""Unit tests for app.services.email_service module.

Tests EmailServiceFactory, DummyEmailService, and EmailSchema validation.
No SMTP connections are made.
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.services.email_service import (
    EmailSchema,
    DummyEmailService,
    SMTPEmailService,
    EmailServiceFactory,
    EmailService,
)


# ---------------------------------------------------------------------------
# EmailSchema validation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEmailSchema:
    """Tests for EmailSchema Pydantic model."""

    def test_valid_schema(self):
        """A fully valid EmailSchema should pass validation."""
        schema = EmailSchema(
            subject="Test",
            recipients=["user@example.com"],
            body="Hello world",
        )
        assert schema.subject == "Test"
        assert schema.recipients == ["user@example.com"]
        assert schema.body == "Hello world"

    def test_html_body_optional(self):
        """html_body should default to None when not provided."""
        schema = EmailSchema(
            subject="Test",
            recipients=["user@example.com"],
            body="text",
        )
        assert schema.html_body is None

    def test_html_body_accepted(self):
        """html_body should be stored when provided."""
        schema = EmailSchema(
            subject="Test",
            recipients=["user@example.com"],
            body="text",
            html_body="<p>text</p>",
        )
        assert schema.html_body == "<p>text</p>"

    def test_invalid_email_raises_validation_error(self):
        """Invalid email address in recipients should raise ValidationError."""
        with pytest.raises(ValidationError):
            EmailSchema(
                subject="Test",
                recipients=["not-an-email"],
                body="text",
            )

    def test_multiple_recipients(self):
        """Multiple valid recipients should be accepted."""
        schema = EmailSchema(
            subject="Test",
            recipients=["a@b.com", "c@d.com"],
            body="text",
        )
        assert len(schema.recipients) == 2

    def test_empty_recipients_allowed_by_type(self):
        """Empty recipients list should be structurally valid (List[EmailStr])."""
        schema = EmailSchema(
            subject="Test",
            recipients=[],
            body="text",
        )
        assert schema.recipients == []

    def test_missing_subject_raises_validation_error(self):
        """Missing subject should raise ValidationError."""
        with pytest.raises(ValidationError):
            EmailSchema(
                recipients=["a@b.com"],
                body="text",
            )

    def test_missing_body_raises_validation_error(self):
        """Missing body should raise ValidationError."""
        with pytest.raises(ValidationError):
            EmailSchema(
                subject="Test",
                recipients=["a@b.com"],
            )


# ---------------------------------------------------------------------------
# DummyEmailService
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDummyEmailService:
    """Tests for DummyEmailService."""

    @pytest.mark.asyncio
    async def test_send_email_returns_true(self):
        """DummyEmailService.send_email should return True without errors."""
        service = DummyEmailService()
        email = EmailSchema(
            subject="Test Subject",
            recipients=["test@example.com"],
            body="Test body",
        )
        result = await service.send_email(email)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_email_with_html_body_returns_true(self):
        """DummyEmailService should handle html_body gracefully."""
        service = DummyEmailService()
        email = EmailSchema(
            subject="HTML Test",
            recipients=["test@example.com"],
            body="plain",
            html_body="<b>bold</b>",
        )
        result = await service.send_email(email)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_email_does_not_raise(self):
        """DummyEmailService.send_email should never raise an exception."""
        service = DummyEmailService()
        email = EmailSchema(
            subject="Safe",
            recipients=["x@y.com"],
            body="body",
        )
        # Should complete without exception
        await service.send_email(email)

    def test_dummy_is_email_service_subclass(self):
        """DummyEmailService should be a subclass of EmailService."""
        assert issubclass(DummyEmailService, EmailService)


# ---------------------------------------------------------------------------
# EmailServiceFactory
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEmailServiceFactory:
    """Tests for EmailServiceFactory.get_service()."""

    def setup_method(self):
        """Reset the singleton before each test."""
        EmailServiceFactory._service_instance = None

    def test_returns_dummy_when_smtp_not_configured(self):
        """When SMTP_HOST and SMTP_USER are empty, DummyEmailService is returned."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = ""
            service = EmailServiceFactory.get_service()
            assert isinstance(service, DummyEmailService)

    def test_returns_smtp_when_configured(self):
        """When SMTP_HOST and SMTP_USER are set, SMTPEmailService is returned."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = "user@example.com"
            service = EmailServiceFactory.get_service()
            assert isinstance(service, SMTPEmailService)

    def test_returns_dummy_when_host_missing(self):
        """When only SMTP_HOST is empty, DummyEmailService is returned."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = "user@example.com"
            service = EmailServiceFactory.get_service()
            assert isinstance(service, DummyEmailService)

    def test_returns_dummy_when_user_missing(self):
        """When only SMTP_USER is empty, DummyEmailService is returned."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_USER = ""
            service = EmailServiceFactory.get_service()
            assert isinstance(service, DummyEmailService)

    def test_factory_caches_service_instance(self):
        """Subsequent calls should return the same instance (singleton)."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = ""
            s1 = EmailServiceFactory.get_service()
            s2 = EmailServiceFactory.get_service()
            assert s1 is s2

    def test_returned_service_is_email_service_subclass(self):
        """Factory should always return an EmailService subclass."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            mock_settings.SMTP_USER = ""
            service = EmailServiceFactory.get_service()
            assert isinstance(service, EmailService)
