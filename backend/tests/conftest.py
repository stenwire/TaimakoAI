import sys
import os
import pytest
from unittest.mock import MagicMock, patch
# Ensure the project root is on the Python path for test imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external services before importing app
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from app.db.session import get_db
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.user import User # Import to register models
from app.models.business import Business # Import to register models
from app.main import app
from app.services.rag_service import rag_service

@pytest.fixture(scope="function")
def db_session():
    # In-memory SQLite for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def mock_vector_db(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(rag_service, "vector_db", mock_db)
    return mock_db


# ===== Tool Testing Fixtures =====

@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with configurable state for tool tests."""
    context = MagicMock()
    context.state = {
        "user_id": "test-user-123",
        "api_key": "test-api-key-456",
        "response_style": "normal"
    }
    return context


@pytest.fixture
def mock_rag_service_fixture(monkeypatch):
    """Mock RAG service for testing get_context tool."""
    mock_service = MagicMock()
    mock_service.query.return_value = [
        "Context chunk 1: Sample information.",
        "Context chunk 2: Additional details."
    ]
    monkeypatch.setattr("app.services.agent_system.tools.rag_service", mock_service)
    return mock_service


@pytest.fixture
def mock_email_service_fixture():
    """Mock email service for testing escalation tool."""
    with patch("app.services.agent_system.tools.EmailServiceFactory") as mock_factory:
        mock_service = MagicMock()
        mock_factory.get_service.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_session_local():
    """Mock SessionLocal for tools that create their own DB sessions."""
    with patch("app.services.agent_system.tools.SessionLocal") as mock_session_cls:
        mock_sess = MagicMock()
        mock_session_cls.return_value = mock_sess
        yield mock_sess
