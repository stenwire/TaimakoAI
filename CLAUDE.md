# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaimakoAI is a SaaS platform providing AI-powered customer support chat widgets. Businesses embed a widget on their site; the backend uses an agentic RAG system (Google ADK + Gemini 2.0 Flash + ChromaDB) to answer customer questions from uploaded documents. Includes subscription management via Paystack, human escalation workflows, and analytics.

## Development Commands

All commands run via Docker Compose through the Makefile:

```bash
make build                # Build containers
make start-d              # Start all services (detached)
make stop                 # Stop services
make logs-backend         # Tail backend logs
make logs-frontend        # Tail frontend logs
make backend-test         # Run pytest inside backend container: uv run pytest . -v
make migrate              # Run alembic upgrade head
make migrate-generate     # Generate new alembic migration (interactive prompt for message)
make db-shell             # PostgreSQL shell
make db-reset             # Drop all tables (then run make migrate)
```

Without Docker, run backend/frontend directly:
- **Backend**: `cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Frontend**: `cd frontend && npm run dev`
- **Lint frontend**: `cd frontend && npm run lint`
- **Backend tests**: `cd backend && uv run pytest . -v`

## Architecture

### Backend (FastAPI + SQLAlchemy + Alembic)

- **Entry point**: `backend/app/main.py` — registers all routers, middleware, admin panel
- **Config**: `backend/app/core/config.py` — `LocalConfig` / `ProductionConfig` selected by `ENVIRONMENT` env var
- **DB session**: `backend/app/db/session.py` — SQLAlchemy engine + session factory
- **Models**: `backend/app/models/` — User, Business, Plan, ChatSession, GuestUser, GuestMessage, Document, Escalation, PaymentTransaction, AnalyticsDailySummary
- **Schemas**: `backend/app/schemas/` — Pydantic request/response models
- **API routes**: `backend/app/api/` — routes.py (chat/documents), widget.py (public widget endpoints), subscription.py, escalation.py, analytics.py, business.py, plans.py
- **Auth**: `backend/app/auth/` — Google OAuth2 + JWT. Protected routes use `get_current_user` dependency.

### Agent System (`backend/app/services/agent_system/`)

The core AI engine:
- **agent_factory.py**: Creates agents dynamically per business config using Google ADK. Sub-agents: greeting, context retrieval, escalation, sentiment analysis.
- **tools.py**: Agent tools — `get_context()` (RAG retrieval), `analyze_sentiment()`, `escalate_to_human()`, `say_hello()`/`say_goodbye()`
- **callbacks.py**: Content safety validation, response sanitization, tool argument validation
- **RAG**: `backend/app/services/rag_service.py` — ChromaDB vector search, document indexing/parsing

### Subscription System (`backend/app/services/subscription/`)

- **base.py**: Abstract `SubscriptionService` interface
- **paystack.py**: Paystack implementation — transaction init, subscription creation, cancellation, webhook verification
- **Tiers**: spark (tier 1), flux (tier 2), nexus (tier 3) — defined in `backend/app/core/subscription.py` with credit/session/domain limits

### Frontend (Next.js 16 App Router + React 19 + Tailwind 4)

- **API client**: `frontend/src/lib/api.ts` — Axios instance with JWT interceptors and token refresh on 401
- **Config**: `frontend/src/config.ts` — environment-aware backend URL selection via `NEXT_PUBLIC_ENVIRONMENT`
- **Contexts**: AuthContext (JWT/localStorage), BusinessContext, ToastContext in `frontend/src/contexts/`
- **Dashboard**: `frontend/src/app/dashboard/` — documents, analytics, sessions, widget-settings, escalation handoff, subscription settings
- **Widget**: `frontend/src/app/widget/[public_widget_id]/` — public embeddable chat widget

### API Response Pattern

All backend responses use a consistent wrapper: `{status, message, data}` via `success_response()` helper.

### Alembic Migrations

- Google ADK tables (sessions, app_states, events) are excluded from autogeneration in `alembic/env.py`
- All models must be imported in `env.py` for autogenerate to detect them

## Deployment

GitHub Actions CI/CD deploys on push to `prod` branch. Builds Docker images, pushes to GHCR, deploys to VPS with PostgreSQL. Config in `.github/workflows/deploy.yml`.
