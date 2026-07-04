# Contributing to TaimakoAI

Thanks for your interest in contributing! This guide covers everything you need to get started.

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended) — or run services directly:
  - Python 3.10+ with [uv](https://docs.astral.sh/uv/)
  - Node.js 22+ with npm
  - PostgreSQL

### One-Command Setup

```bash
git clone https://github.com/your-org/TaimakoAI.git
cd TaimakoAI
make setup
```

This installs the pre-commit hook and all backend/frontend dependencies.

### Running the App

**With Docker (recommended):**

```bash
make build       # first time only
make start-d     # start all services
make migrate     # run database migrations
make logs        # tail logs
make stop        # stop everything
```

**Without Docker:**

```bash
# Terminal 1 — backend
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feat/my-feature    # or fix/my-bugfix
```

### 2. Make Your Changes

Write your code, then verify it passes checks:

```bash
make lint-be       # backend lint
make lint-fe       # frontend lint
make test-be       # backend tests (280 tests)
make test-fe       # frontend tests (71 tests)
```

The pre-commit hook runs lint automatically on staged files when you commit. If it fails, fix the issues or run `make lint-be-fix` / `make lint-fe-fix` for auto-fixes.

### 3. Commit

```bash
git add <files>
git commit -m "feat: add widget analytics export"
```

Commit messages should be concise and describe *what* and *why*. Use conventional prefixes when they fit: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.

### 4. Open a Pull Request

Push your branch and open a PR against `main`. The PR template will auto-populate with a checklist — fill it out.

CI will run lint and tests for both backend and frontend. All checks must pass before merge.

## Project Structure

```
TaimakoAI/
  backend/               # FastAPI + SQLAlchemy + Alembic
    app/
      api/               # Route handlers
      auth/              # Google OAuth + JWT
      core/              # Config, security, middleware
      models/            # SQLAlchemy models
      schemas/           # Pydantic schemas
      services/          # Business logic, agent system, RAG
    tests/               # pytest (unit/, api/, integration/)
    TESTING.md           # Backend testing guide

  frontend/              # Next.js 16 + React 19 + Tailwind 4
    src/
      app/               # App Router pages
      components/        # UI and dashboard components
      contexts/          # Auth, Business, Toast providers
      lib/               # API client, types, utilities
    tests/               # Vitest (unit/, components/)
    TESTING.md           # Frontend testing guide

  scripts/               # Dev tooling (pre-commit hook)
  .github/               # CI workflows, PR/issue templates
  Makefile               # All dev commands
  CLAUDE.md              # Architecture reference
```

## Code Style

### Backend (Python)

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — runs on commit and in CI
- **Framework**: FastAPI with dependency injection
- **ORM**: SQLAlchemy 2.0 declarative models
- **Response format**: All endpoints return `{status, message, data}` via `success_response()`
- **Migrations**: Alembic — run `make migrate-generate` to create, `make migrate` to apply

### Frontend (TypeScript)

- **Linter**: ESLint with `eslint-config-next`
- **Styles**: Tailwind CSS 4 with CSS variables (`--brand-primary`, `--text-primary`, etc.)
- **Components**: Functional components, `forwardRef` for inputs
- **API calls**: Axios instance in `src/lib/api.ts` with JWT interceptors

## Testing

Every code change should include tests. See the detailed guides:

- **Backend**: [`backend/TESTING.md`](backend/TESTING.md)
- **Frontend**: [`frontend/TESTING.md`](frontend/TESTING.md)

### Quick Reference

| Command                  | What it runs                          |
| ------------------------ | ------------------------------------- |
| `make test-be`           | All backend tests                     |
| `make test-be-unit`      | Backend unit tests only (fastest)     |
| `make test-be-api`       | Backend API endpoint tests            |
| `make test-be-integration` | Backend integration tests           |
| `make test-fe`           | All frontend tests                    |

### When to Write Tests

- New API endpoint → `backend/tests/api/`
- New utility or service → `backend/tests/unit/` or `frontend/tests/unit/`
- New UI component → `frontend/tests/components/`
- Bug fix → regression test that reproduces the bug

## Database Migrations

When you change a model in `backend/app/models/`:

```bash
make migrate-generate    # creates a new migration file
make migrate             # applies it
```

Review the generated migration before committing. All models must be imported in `backend/alembic/env.py`.

## Reporting Issues

Use the issue templates on GitHub:

- **Bug Report** — include steps to reproduce, expected vs actual behavior
- **Feature Request** — describe the problem, propose a solution

## All Makefile Commands

```bash
make setup               # Install hooks + dependencies
make install-hooks       # Install pre-commit hook only
make build               # Build Docker containers
make start-d             # Start services (detached)
make stop                # Stop services
make logs                # Tail all logs
make lint-be             # Lint backend
make lint-be-fix         # Lint + auto-fix backend
make lint-fe             # Lint frontend
make lint-fe-fix         # Lint + auto-fix frontend
make test-be             # Run all backend tests
make test-be-unit        # Backend unit tests
make test-be-api         # Backend API tests
make test-be-integration # Backend integration tests
make test-fe             # Run all frontend tests
make migrate             # Run database migrations
make migrate-generate    # Generate new migration
make db-shell            # PostgreSQL shell
make db-reset            # Drop all tables
make db-backup           # Backup database
make db-restore FILE=x   # Restore from backup
```
