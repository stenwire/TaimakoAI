import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic RAG API"
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "hello-world")
    CHROMA_DB_DIR: str = "chroma_db"

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

    class Config:
        env_file = ".env"

settings = Settings()
