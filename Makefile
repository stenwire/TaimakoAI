.PHONY: install start-backend start-frontend start-all clean

install:
	cd agentic_rag_api && uv sync
	cd frontend && npm install

start-backend:
	cd agentic_rag_api && uv run uvicorn app.main:app --reload --port 8000

start-frontend:
	cd frontend && npm run dev

start-all:
	make start-backend & make start-frontend
