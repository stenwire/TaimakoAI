from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Individual PostgreSQL environment variables (from .env)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # fallback for local runs
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Build PostgreSQL URL if all required parts are present
if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
# Allow direct DATABASE_URL override (common on Heroku, Render, Railway, etc.)
elif os.getenv("DATABASE_URL"):
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# Final fallback: SQLite for quick local development, cause why not, eh?
else:
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./sql_app.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create the engine
# For SQLite: allow multiple threads (FastAPI is multi-threaded by default)
# For PostgreSQL: no special connect_args needed
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()