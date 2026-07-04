# TaimakoAI - Project Context

## Project Overview
**TaimakoAI** is an AI-powered customer support platform that leverages a Retrieval-Augmented Generation (RAG) engine. It processes uploaded knowledge base documents to provide accurate, context-aware responses to customer queries via a smart embeddable chat widget or WhatsApp. It includes a business dashboard for managing documents and analytics, along with capabilities for human escalation and subscription billing.

## Architecture & Tech Stack
- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, TypeScript.
- **Backend:** FastAPI (Python 3.10+), SQLAlchemy ORM, Alembic for migrations.
- **AI / RAG Engine:** Google ADK, Gemini 2.0 Flash, ChromaDB, LiteLLM.
- **Database:** PostgreSQL.
- **Payments:** Paystack integration for tiered billing.
- **Infrastructure:** Docker, Docker Compose, GitHub Actions (CI/CD).

## Building and Running
The repository relies heavily on a `Makefile` to orchestrate setup, running, testing, and db management. Docker is the recommended approach for local development.

### Setup
`make setup`    # Installs dependencies (uv for backend, npm for frontend) and git pre-commit hooks

### Running Locally (Docker)
`make build`    # Build/rebuild containers
`make start-d`  # Start all services (frontend, backend, db) in detached mode
`make migrate`  # Apply database migrations inside the backend container

### Running Locally (Without Docker)
- **Backend:** `cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Frontend:** `cd frontend && npm run dev`

### Stopping & Cleaning
`make stop`     # Stop all services gracefully
`make clean`    # Stop services and remove volumes (CAUTION: deletes DB data)

## Development Conventions

### Testing
- **Backend (Pytest):**
  - All tests: `make test-be`
  - Unit tests only: `make test-be-unit`
  - API tests only: `make test-be-api`
  - Integration tests only: `make test-be-integration`
- **Frontend (Vitest):**
  - Run all tests: `make test-fe`

### Linting & Formatting
- **Backend:** Code is linted using `ruff`. Run `make lint-be` or `make lint-be-fix` to auto-fix issues.
- **Frontend:** Code is linted using `eslint`. Run `make lint-fe` or `make lint-fe-fix` to auto-fix issues.
- **Pre-commit:** A pre-commit hook automatically runs linters on staged files.

### Database Management
- Generate a new migration: `make migrate-generate`
- Apply migrations: `make migrate`
- Useful DB Commands: `make db-shell` (psql access), `make db-backup`, `make db-restore`, `make db-reset`

### Admin Management
- Create or promote a user to admin: `make create-admin EMAIL=user@example.com`

## Contribution Guidelines
1. Fork and clone the repository.
2. Run `make setup` to prepare your local environment.
3. Ensure all tests (`make test-be` and `make test-fe`) pass and code is linted before submitting a pull request.
4. For detailed guidelines, refer to `CONTRIBUTING.md`, `backend/TESTING.md`, and `frontend/TESTING.md`.
