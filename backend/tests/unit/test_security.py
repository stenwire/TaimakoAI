"""Unit tests for app.core.security module.

Tests JWT token creation/verification and password hashing/verification.
Settings are mocked to avoid dependency on environment variables.
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock


# Build a fake settings object used across all tests in this module.
_fake_settings = MagicMock(
    JWT_SECRET="test-secret-key-for-unit-tests",
    JWT_ALGORITHM="HS256",
    JWT_EXPIRATION_MINUTES=30,
    REFRESH_TOKEN_EXPIRATION_DAYS=7,
)

# Patch settings at module level so imports inside security.py pick it up.
_settings_patcher = patch("app.core.security.settings", _fake_settings)
_settings_patcher.start()

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
)


@pytest.fixture(autouse=True)
def _ensure_settings_patch():
    """Ensure the settings patch is active for every test."""
    yield


@pytest.mark.unit
class TestCreateAccessToken:
    """Tests for create_access_token()."""

    def test_create_access_token_returns_string(self):
        """Should return a non-empty JWT string."""
        token = create_access_token(subject="user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_subject(self):
        """Decoded token should contain the correct 'sub' claim."""
        token = create_access_token(subject="user-456")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"

    def test_create_access_token_with_custom_expiry(self):
        """Token created with custom expiry should still be valid."""
        token = create_access_token(subject="u1", expires_delta=timedelta(hours=2))
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "u1"

    def test_create_access_token_no_type_claim(self):
        """Access tokens should NOT contain a 'type' claim."""
        token = create_access_token(subject="u1")
        payload = verify_token(token)
        assert "type" not in payload


@pytest.mark.unit
class TestCreateRefreshToken:
    """Tests for create_refresh_token()."""

    def test_create_refresh_token_returns_string(self):
        """Should return a non-empty JWT string."""
        token = create_refresh_token(subject="user-789")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_type_refresh(self):
        """Decoded refresh token should have type='refresh'."""
        token = create_refresh_token(subject="u2")
        payload = verify_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_create_refresh_token_contains_subject(self):
        """Decoded refresh token should contain the correct 'sub' claim."""
        token = create_refresh_token(subject="user-abc")
        payload = verify_token(token)
        assert payload["sub"] == "user-abc"

    def test_create_refresh_token_with_custom_expiry(self):
        """Refresh token with custom expiry should be valid."""
        token = create_refresh_token(subject="u3", expires_delta=timedelta(days=1))
        payload = verify_token(token)
        assert payload is not None


@pytest.mark.unit
class TestVerifyToken:
    """Tests for verify_token()."""

    def test_verify_token_valid(self):
        """A freshly created token should verify successfully."""
        token = create_access_token(subject="valid-user")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "valid-user"

    def test_verify_token_expired(self):
        """An expired token should return None."""
        token = create_access_token(
            subject="expired-user",
            expires_delta=timedelta(seconds=-1),
        )
        result = verify_token(token)
        assert result is None

    def test_verify_token_tampered(self):
        """A tampered token should return None."""
        token = create_access_token(subject="user")
        # Tamper with the payload (second segment) to change the subject,
        # which invalidates the signature.
        parts = token.split(".")
        import base64
        # Decode payload, alter it, re-encode
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload_bytes = base64.urlsafe_b64decode(padded)
        tampered_payload = payload_bytes.replace(b'"user"', b'"evil"')
        new_segment = base64.urlsafe_b64encode(tampered_payload).rstrip(b"=").decode()
        tampered = f"{parts[0]}.{new_segment}.{parts[2]}"
        result = verify_token(tampered)
        assert result is None

    def test_verify_token_garbage_input(self):
        """Completely invalid input should return None."""
        result = verify_token("not-a-jwt-at-all")
        assert result is None

    def test_verify_token_wrong_secret(self):
        """Token signed with a different secret should fail verification."""
        from jose import jwt as jose_jwt

        token = jose_jwt.encode(
            {"sub": "user", "exp": 9999999999},
            "wrong-secret",
            algorithm="HS256",
        )
        result = verify_token(token)
        assert result is None


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for get_password_hash() and verify_password()."""

    def test_get_password_hash_returns_string(self):
        """Should return a bcrypt hash string."""
        hashed = get_password_hash("mypassword")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2")

    def test_get_password_hash_different_from_plain(self):
        """Hash should never equal the plaintext password."""
        plain = "secret123"
        hashed = get_password_hash(plain)
        assert hashed != plain

    def test_get_password_hash_unique_salts(self):
        """Two hashes of the same password should differ (unique salts)."""
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2

    def test_verify_password_correct(self):
        """verify_password should return True for the correct password."""
        hashed = get_password_hash("correct-horse")
        assert verify_password("correct-horse", hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for the wrong password."""
        hashed = get_password_hash("correct-horse")
        assert verify_password("wrong-horse", hashed) is False
