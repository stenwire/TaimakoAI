"""Fixtures for agent tool tests."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_tool_context():
    """Mock ToolContext with configurable state."""
    context = MagicMock()
    context.state = {
        "user_id": "test-user-123",
        "api_key": "test-api-key-456",
        "response_style": "normal",
    }
    return context


@pytest.fixture
def mock_rag_service_fixture(monkeypatch):
    """Mock RAG service for get_context tool tests."""
    mock_service = MagicMock()
    mock_service.query.return_value = [
        "Context chunk 1: Sample information.",
        "Context chunk 2: Additional details.",
    ]
    monkeypatch.setattr("app.services.agent_system.tools.rag_service", mock_service)
    return mock_service


@pytest.fixture
def mock_email_service_fixture():
    """Mock email service for escalation tool tests."""
    with patch("app.services.agent_system.tools.EmailServiceFactory") as mock_factory:
        mock_service = MagicMock()
        mock_factory.get_service.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_session_local():
    """Mock SessionLocal for tools that create their own DB sessions."""
    with patch("app.services.agent_system.tools.SessionLocal") as mock_cls:
        mock_sess = MagicMock()
        mock_cls.return_value = mock_sess
        yield mock_sess
