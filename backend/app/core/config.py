import os
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

if ENVIRONMENT in ["production", "staging"]:
    ENV_FRONTEND_URI = os.getenv("FRONTEND_LIVE_URI", "https://taimako.dubem.xyz")
else:
    ENV_FRONTEND_URI = os.getenv("FRONTEND_LOCAL_URI", "http://localhost:3000")

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_PREFIX", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")
    CHROMA_DB_DIR: str = "chroma_db"
    FRONTEND_URI: str = ENV_FRONTEND_URI
    FRONTEND_REDIRECT_URI: str = f"{ENV_FRONTEND_URI}/auth/callback"

    # Database
    PROJECT_PREFIX: str = os.getenv("PROJECT_PREFIX", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "")
    DATABASE_URL: str | None = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    FRONTEND_REDIRECT_URI: str = os.getenv("FRONTEND_REDIRECT_URI", "http://localhost:3000/auth/callback")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey") # Change in production!
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))
    REFRESH_TOKEN_EXPIRATION_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", 30))

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
