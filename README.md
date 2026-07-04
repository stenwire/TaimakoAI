# TaimakoAI

> Because your customers deserve better than "Have you tried turning it off and on again?"

**TaimakoAI** is an AI-powered customer support platform that actually knows what it's talking about. Upload your docs, embed a chat widget, and let the AI handle the "where's my order?" at 3am so you don't have to.

Built with a Retrieval-Augmented Generation (RAG) engine, it reads your knowledge base and responds like an employee who actually read the handbook. Revolutionary, we know.

## What It Does

- **Smart Chat Widget** — A sleek, embeddable widget that lives on your site and answers customer questions using *your* documents. Not hallucinated nonsense. Well, mostly.
- **Agentic RAG Engine** — Google ADK + Gemini 2.0 Flash + ChromaDB. It retrieves relevant context, reasons about it, and responds. It's like Stack Overflow but it doesn't judge you.
- **Business Dashboard** — Upload docs, view analytics, manage sessions, configure your widget, and pretend you're a data-driven company. Charts included.
- **Human Escalation** — When the AI detects a customer is about to throw their laptop, it escalates to a human. Sentiment analysis meets self-preservation.
- **WhatsApp Integration** — Same AI brain, now on WhatsApp. Because some customers think email is a generational trauma.
- **Subscription Management** — Paystack-powered billing with tiered plans. From "just getting started" to "we have a budget now."
- **Analytics** — Session tracking, intent classification, traffic sources, location data. Everything you need for the board meeting you're definitely preparing for.

## Tech Stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | Next.js 16, React 19, Tailwind 4, TypeScript | Because we like living on the edge (literally, edge runtime) |
| Backend | FastAPI, SQLAlchemy, Alembic, Python 3.10+ | Fast enough to make Django developers nervous |
| AI/RAG | Google ADK, Gemini 2.0 Flash, ChromaDB | The brains of the operation |
| Database | PostgreSQL | The only database that won't ghost you at scale |
| Payments | Paystack | For our African market kings and queens |
| Infra | Docker, GitHub Actions CI/CD | It works on my machine AND yours |

## Getting Started

### Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.10+ with [uv](https://docs.astral.sh/uv/), Node.js 22+, PostgreSQL

### Setup

```bash
git clone https://github.com/your-org/TaimakoAI.git
cd TaimakoAI
make setup    # installs deps + pre-commit hooks. One command. You're welcome.
```

### Run

**With Docker** (the civilized way):

```bash
make build      # first time only
make start-d    # start everything
make migrate    # run database migrations
```

**Without Docker** (you like pain, we respect that):

```bash
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend && npm run dev
```

Then open:
- Frontend: [http://localhost:3000](http://localhost:3000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger, the developer's coloring book)

## Project Structure

```
TaimakoAI/
  backend/                 # FastAPI — where the magic happens
    app/
      api/                 # Route handlers (the front door)
      auth/                # Google OAuth + JWT (the bouncer)
      core/                # Config, security, middleware (the boring but important stuff)
      models/              # SQLAlchemy models (the source of truth)
      schemas/             # Pydantic schemas (the trust issues)
      services/            # Business logic, agents, RAG (the actual work)
    tests/                 # 280 tests. Yes, we test our code. Shocking.
  frontend/                # Next.js — where things look pretty
    src/
      app/                 # Pages and routes
      components/          # UI components (buttons that actually work)
      contexts/            # React contexts (global state, but make it elegant)
      lib/                 # API client, types, utils
    tests/                 # 71 tests. The frontend pulls its weight too.
  scripts/                 # Dev tooling
  .github/                 # CI, PR templates, issue templates
  Makefile                 # 25+ commands. `make help` yourself.
```

## Development

### Lint & Test

```bash
make lint-be          # backend lint (ruff)
make lint-fe          # frontend lint (eslint)
make test-be          # backend tests (pytest)
make test-be-unit     # just unit tests (fast, for the impatient)
make test-fe          # frontend tests (vitest)
```

A pre-commit hook runs lint on staged files automatically. It's like a spell checker, but for your code's dignity.

### Database Migrations

```bash
make migrate-generate   # creates migration from model changes
make migrate            # applies migrations
```

## Contributing

We welcome contributions! Check out [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

**TL;DR:**
1. Fork & clone
2. `make setup`
3. Branch, code, test
4. Open a PR (the template will guide you)

Detailed testing guides: [Backend](backend/TESTING.md) | [Frontend](frontend/TESTING.md)

## Architecture (For the Curious)

```
Customer visits website
       |
       v
  [Chat Widget]  ------>  [FastAPI Backend]
       ^                        |
       |                   [Auth + Rate Limits]
       |                        |
  [AI Response]  <------  [Agent System (Google ADK)]
                                |
                          [RAG: ChromaDB + Gemini Embeddings]
                                |
                          [Your uploaded documents]
                          (the ones you actually wrote)
```

The agent system uses sub-agents for different tasks: greeting, context retrieval, sentiment analysis, and escalation. It's basically a team meeting, but productive.

## License

*Coming soon. For now, be cool.*
