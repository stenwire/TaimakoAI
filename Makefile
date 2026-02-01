# Load variables from .env file (if present)
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default values (fallback if .env missing or vars not set)
PROJECT_PREFIX      ?= taimako
POSTGRES_USER       ?= taimako
POSTGRES_DB         ?= taimako_db
POSTGRES_CONTAINER  ?= $(PROJECT_PREFIX)_postgres
BACKEND_CONTAINER   ?= $(PROJECT_PREFIX)_backend
FRONTEND_CONTAINER  ?= $(PROJECT_PREFIX)_frontend

.PHONY: start start-d stop build logs migrate migrate-generate db-shell db-backup db-restore clean ps db-reset db-truncate logs-backend logs-frontend

# Start all services (foreground)
start:
	docker-compose up

# Start in detached mode
start-d:
	docker-compose up -d

# Run tests for backend
backend-test:
	docker-compose exec backend uv run pytest . -v

# Stop all services
stop:
	docker-compose down

# Stop and remove volumes (CAUTION: deletes database data)
clean:
	docker-compose down -v

# Build/rebuild containers
build:
	docker-compose build

# View logs (all services)
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Database migrations (runs inside backend container)
migrate:
	docker-compose exec backend uv run alembic upgrade head

# Generate new migration
migrate-generate:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend uv run alembic revision --autogenerate -m "$$msg"

# Access PostgreSQL shell
db-shell:
	docker-compose exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# Backup database to local file
db-backup:
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker-compose exec $(POSTGRES_CONTAINER) pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > backup_$${timestamp}.sql; \
	echo "Database backed up to backup_$${timestamp}.sql"

# Restore database from backup file
# Usage: make db-restore FILE=backup_20251231_120000.sql
db-restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file. Usage: make db-restore FILE=backup.sql"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: File $(FILE) not found!"; \
		exit 1; \
	fi
	cat $(FILE) | docker-compose exec -T $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)
	@echo "Database successfully restored from $(FILE)"

# Reset database (drop everything and recreate public schema)
db-reset:
	@echo "Resetting database to clean state (dropping all tables)..."
	docker-compose exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "\
		DROP SCHEMA public CASCADE; \
		CREATE SCHEMA public; \
		GRANT ALL ON SCHEMA public TO $(POSTGRES_USER); \
		GRANT ALL ON SCHEMA public TO public;"
	@echo "Database reset complete. Run 'make migrate' to recreate tables."

# Truncate all tables (clear data, preserve structure)
db-truncate:
	@echo "Truncating all tables (excluding alembic_version)..."
	docker-compose exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "\
		DO \$\$ \
		DECLARE r RECORD; \
		BEGIN \
			FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version') LOOP \
				EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE'; \
			END LOOP; \
		END \$\$;"
	@echo "All tables truncated (data cleared, structure preserved)."

# Show running containers
ps:
	docker-compose ps
