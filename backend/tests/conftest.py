"""
Root test configuration.

Sets up in-memory SQLite, mocks external services, and provides
core fixtures used across all test categories.
"""
import sys
import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock heavy external dependencies before any app code is imported.
# This prevents import-time side effects (ChromaDB client init, etc.).
# ---------------------------------------------------------------------------
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.services.rag_service import rag_service  # noqa: E402

# ---------------------------------------------------------------------------
# Import ALL models so Base.metadata knows every table.
# ---------------------------------------------------------------------------
from app.models.user import User  # noqa: F401, E402
from app.models.business import Business  # noqa: F401, E402
from app.models.document import Document  # noqa: F401, E402
from app.models.widget import WidgetSettings, GuestUser, GuestMessage  # noqa: F401, E402
from app.models.chat_session import ChatSession  # noqa: F401, E402
from app.models.escalation import Escalation  # noqa: F401, E402
from app.models.plan import Plan  # noqa: F401, E402
from app.models.payment import PaymentTransaction  # noqa: F401, E402
from app.models.analytics import AnalyticsDailySummary  # noqa: F401, E402


# ===== Core Fixtures =====


@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient wired to the test database."""

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ===== Factory Session Binding =====


@pytest.fixture(autouse=True)
def _bind_factory_sessions(db_session):
    """Bind all factory-boy factories to the current test DB session."""
    from tests.factories import (
        UserFactory,
        BusinessFactory,
        WidgetSettingsFactory,
        GuestUserFactory,
        ChatSessionFactory,
        EscalationFactory,
        GuestMessageFactory,
        PlanFactory,
        PaymentTransactionFactory,
    )

    for cls in (
        UserFactory,
        BusinessFactory,
        WidgetSettingsFactory,
        GuestUserFactory,
        ChatSessionFactory,
        EscalationFactory,
        GuestMessageFactory,
        PlanFactory,
        PaymentTransactionFactory,
    ):
        cls._meta.sqlalchemy_session = db_session


# ===== Auth Helpers =====


@pytest.fixture
def authenticated_client(client, db_session):
    """Returns (client, user) with a pre-authenticated user."""
    from tests.factories import UserFactory

    user = UserFactory()
    db_session.commit()
    token = create_access_token(subject=user.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client, user


@pytest.fixture
def auth_client_with_business(client, db_session):
    """Returns (client, user, business) — user with a business profile."""
    from tests.factories import UserFactory, BusinessFactory

    user = UserFactory()
    business = BusinessFactory(user=user, user_id=user.id)
    db_session.commit()
    token = create_access_token(subject=user.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client, user, business


@pytest.fixture
def auth_client_with_widget(client, db_session):
    """Returns (client, user, business, widget) — full setup for widget tests."""
    from tests.factories import UserFactory, BusinessFactory, WidgetSettingsFactory

    user = UserFactory()
    business = BusinessFactory(user=user, user_id=user.id)
    widget = WidgetSettingsFactory(user=user, user_id=user.id)
    db_session.commit()
    token = create_access_token(subject=user.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client, user, business, widget


# ===== Mock Helpers =====


@pytest.fixture
def mock_vector_db(monkeypatch):
    """Mock the RAG vector database."""
    mock_db = MagicMock()
    monkeypatch.setattr(rag_service, "vector_db", mock_db)
    return mock_db
