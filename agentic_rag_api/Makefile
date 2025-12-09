.PHONY: run test docker-build docker-run

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

docker-build:
	docker build -t agentic-rag-api .

docker-run:
	docker run -p 8100:8100 agentic-rag-api
