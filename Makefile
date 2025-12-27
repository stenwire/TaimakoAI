.PHONY: start stop build logs migrate migrate-generate db-shell db-backup db-restore clean

# Start all services
start:
	docker-compose up

# Start in detached mode
start-d:
	docker-compose up -d

# Stop all services
stop:
	docker-compose down

# Stop and remove volumes (CAUTION: deletes database data)
clean:
	docker-compose down -v

# Build/rebuild containers
build:
	docker-compose build

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Database migrations (runs inside container)
migrate:
	docker-compose exec backend uv run alembic upgrade head

# Generate new migration (runs inside container)
migrate-generate:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend uv run alembic revision --autogenerate -m "$$msg"

# Access PostgreSQL shell
db-shell:
	docker-compose exec postgres psql -U agentic_cx -d agentic_cx_db

# Backup database to local file
db-backup:
	docker-compose exec postgres pg_dump -U agentic_cx agentic_cx_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$$(date +%Y%m%d_%H%M%S).sql"

# Restore database from backup file (usage: make db-restore FILE=backup.sql)
db-restore:
	@if [ -z "$(FILE)" ]; then echo "Usage: make db-restore FILE=backup.sql"; exit 1; fi
	cat $(FILE) | docker-compose exec -T postgres psql -U agentic_cx -d agentic_cx_db
	@echo "Database restored from $(FILE)"

# Reset database to clean state (drops all tables, need to run 'make migrate' after)
db-reset:
	@echo "Resetting database to clean state (dropping all tables)..."
	docker-compose exec postgres psql -U agentic_cx -d agentic_cx_db -c "\
		DROP SCHEMA public CASCADE; \
		CREATE SCHEMA public; \
		GRANT ALL ON SCHEMA public TO agentic_cx; \
		GRANT ALL ON SCHEMA public TO public;"
	@echo "Database reset complete. Run 'make migrate' to recreate tables."

# Truncate all tables (keeps tables but removes all data)
db-truncate:
	@echo "Truncating all tables..."
	docker-compose exec postgres psql -U agentic_cx -d agentic_cx_db -c "\
		DO \$$\$$ \
		DECLARE r RECORD; \
		BEGIN \
			FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version') LOOP \
				EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE'; \
			END LOOP; \
		END \$$\$$;"
	@echo "All tables truncated (data cleared, tables preserved)."

# Show running containers
ps:
	docker-compose ps
