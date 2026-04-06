# Testing Guide

Standards and conventions for writing tests in the TaimakoAI backend.

## Quick Start

```bash
# Run full suite
make backend-test          # via Docker
uv run pytest tests/ -v    # locally

# Run by category
uv run pytest tests/unit/ -v        # fast, no DB
uv run pytest tests/api/ -v         # API endpoints
uv run pytest tests/integration/ -v # multi-component

# Run a single file or test
uv run pytest tests/api/test_plans.py -v
uv run pytest tests/unit/test_security.py::TestVerifyToken::test_verify_token_expired -v
```

## Directory Structure

```
tests/
  conftest.py                   # Root fixtures: db_session, client, auth helpers
  factories.py                  # factory-boy model factories

  unit/                         # Pure logic tests. No DB, no HTTP.
    test_response_wrapper.py
    test_security.py
    test_subscription_tier.py
    test_subscription_factory.py
    test_paystack_service.py
    test_whatsapp_service.py
    test_email_service.py
    tools/                      # Agent tool tests
      conftest.py               # Tool-specific fixtures (mock_tool_context, etc.)
      test_say_hello.py
      test_say_goodbye.py
      test_analyze_sentiment.py
      test_get_context.py
      test_escalate_to_human.py

  api/                          # Endpoint tests. Uses TestClient + in-memory SQLite.
    test_root.py
    test_auth_google.py
    test_auth_local.py
    test_business.py
    test_documents.py
    test_plans.py
    test_subscription.py
    test_webhook.py
    test_escalation.py
    test_analytics.py
    test_widget_settings.py
    test_widget_chat.py
    test_whatsapp_api.py

  integration/                  # Multi-component tests.
    test_rag_scoped.py
    test_automated_analysis.py
    test_escalation_flow.py
```

### Where does my test go?

| You are testing...                         | Put it in...       |
| ------------------------------------------ | ------------------ |
| A pure function (no DB, no HTTP)           | `tests/unit/`      |
| A utility, helper, or service method       | `tests/unit/`      |
| An agent tool (say_hello, get_context...)  | `tests/unit/tools/`|
| An API endpoint (request -> response)      | `tests/api/`       |
| A workflow that spans multiple services    | `tests/integration/`|

## Writing a Test

### Naming

Follow `test_<what>_<scenario>_<expected>`:

```python
def test_verify_token_expired_returns_none():
    ...

def test_list_plans_no_active_plans_returns_empty():
    ...

def test_webhook_duplicate_reference_skips_processing():
    ...
```

Group related tests in classes. Use nested classes for sub-categories:

```python
class TestVerifyToken:
    def test_valid_token(self):
        ...

    def test_expired_token(self):
        ...
```

### Fixtures

The root `conftest.py` provides these fixtures:

| Fixture                      | Returns                              | Use when...                    |
| ---------------------------- | ------------------------------------ | ------------------------------ |
| `db_session`                 | SQLAlchemy Session (in-memory SQLite)| You need a database            |
| `client`                     | FastAPI TestClient                   | Testing endpoints              |
| `authenticated_client`       | `(client, user)`                     | Endpoint requires auth         |
| `auth_client_with_business`  | `(client, user, business)`           | Endpoint requires a business   |
| `auth_client_with_widget`    | `(client, user, business, widget)`   | Widget endpoint testing        |
| `mock_vector_db`             | MagicMock                            | Mocking ChromaDB               |

Factory sessions are auto-bound -- just call `UserFactory()` etc. without any setup.

### Factories

Use factory-boy factories from `tests/factories.py` for test data:

```python
from tests.factories import UserFactory, BusinessFactory, PlanFactory

def test_something(db_session):
    user = UserFactory(email="custom@test.com")
    business = BusinessFactory(user=user, user_id=user.id, subscription_tier="nexus")
    plan = PlanFactory(name="nexus", tier=2, price=10000)
    db_session.commit()  # flush to DB
    ...
```

Available factories: `UserFactory`, `BusinessFactory`, `WidgetSettingsFactory`, `GuestUserFactory`, `ChatSessionFactory`, `EscalationFactory`, `GuestMessageFactory`, `PlanFactory`, `PaymentTransactionFactory`.

When you add a new model, add a factory for it.

### Mocking External Services

External services (Gemini, ChromaDB, Paystack, WhatsApp API) are mocked at import time in `conftest.py`. For endpoint-level mocking:

```python
from unittest.mock import patch, AsyncMock

MOCK_SERVICE = "app.services.subscription.factory.SubscriptionServiceFactory.get_service"

def test_initialize(self, auth_client_with_business, db_session):
    client, user, business = auth_client_with_business
    plan = PlanFactory(name="spark", tier=1)
    db_session.commit()

    mock_svc = MagicMock()
    mock_svc.initialize_subscription.return_value = {"authorization_url": "https://pay.test"}

    with patch(MOCK_SERVICE, return_value=mock_svc):
        resp = client.post("/subscription/initialize", json={"plan_id": plan.id, "provider": "paystack"})
    assert resp.status_code == 200
```

For async services (like `run_conversation`):

```python
@patch("app.api.widget.run_conversation", new_callable=AsyncMock, return_value="Hello!")
def test_chat(self, mock_ai, client, ...):
    ...
```

### Response Format

All endpoints return `{status, message, data}`. Assert against this:

```python
resp = client.get("/public/plans")
assert resp.status_code == 200
body = resp.json()
assert body["status"] == "success"
assert isinstance(body["data"], list)
```

## When to Write Tests

### Always write tests when you:

- **Add a new API endpoint** -- Add to the corresponding `tests/api/test_*.py` file.
- **Add a new agent tool** -- Add a new file in `tests/unit/tools/`.
- **Add a new service or utility** -- Add a unit test in `tests/unit/`.
- **Fix a bug** -- Write a regression test that would have caught the bug.
- **Change business logic** (credit calculation, subscription flow, limits) -- Update or add tests verifying the new behavior.

### You can skip tests for:

- Pure HTML/template changes.
- Config-only changes (env vars, settings).
- Database migrations (these are tested by running `alembic upgrade head`).

### PR checklist

- [ ] All existing tests pass: `uv run pytest tests/ -v`
- [ ] Lint passes: `uv run ruff check .`
- [ ] New code has corresponding tests
- [ ] No hardcoded secrets or real API keys in test files
- [ ] Factory used for test data (not raw SQL or manual model construction)

## Tips

1. **One assertion per concept.** A test can have multiple `assert` lines, but they should all verify the same logical thing.

2. **Don't test framework behavior.** Don't test that FastAPI returns 422 for missing required fields -- that's Pydantic's job.

3. **Use factories, not raw models.** `UserFactory()` handles UUID generation, timestamps, and defaults. Manual `User(id=..., email=..., ...)` is fragile.

4. **Mock at the boundary.** Mock `run_conversation`, not individual LLM calls. Mock `SubscriptionServiceFactory.get_service()`, not `httpx.Client.post`.

5. **Commit after factories.** Factories call `session.flush()` but not `session.commit()`. Always call `db_session.commit()` before making API requests.

6. **Keep tests independent.** Each test gets a fresh database. Never depend on state from another test.

7. **Async tests just work.** The pytest config has `asyncio_mode = "auto"`. Just write `async def test_...` and it runs.
