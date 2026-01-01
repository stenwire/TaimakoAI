from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.base import Base
# Import all your models here so they are registered with Base.metadata
from app.models.user import User
from app.models.document import Document
from app.models.business import Business
from app.models.widget import WidgetSettings, GuestUser, GuestMessage
from app.models.chat_session import ChatSession
from app.models.analytics import AnalyticsDailySummary

# Alembic Config object
config = context.config

# === Dynamically build DATABASE_URL from individual env vars ===
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # fallback for local runs
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    database_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    config.set_main_option("sqlalchemy.url", database_url)
else:
    # Fallback: if individual vars are missing, try the full DATABASE_URL (e.g., from Heroku, Render, Railway)
    fallback_url = os.getenv("DATABASE_URL")
    if fallback_url:
        config.set_main_option("sqlalchemy.url", fallback_url)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True  # Important for SQLite → PostgreSQL migrations if ever needed
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()