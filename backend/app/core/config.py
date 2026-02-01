import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class BaseConfig(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_PREFIX", "Taimako AI")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")
    CHROMA_DB_DIR: str = "chroma_db"
    
    # Database
    PROJECT_PREFIX: str = os.getenv("PROJECT_PREFIX", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "")
    DATABASE_URL: Union[str, None] = None

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey") # Change in production!
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))
    REFRESH_TOKEN_EXPIRATION_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRATION_DAYS", 30))

    # Common Middleware Defaults
    CORS_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_ALLOW_ORIGIN_REGEX: Union[str, None] = None
    
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    USE_HTTPS_REDIRECT: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

class LocalConfig(BaseConfig):
    FRONTEND_URI: str = os.getenv("FRONTEND_LOCAL_URI", "http://localhost:3000")
    FRONTEND_REDIRECT_URI: str = f"{os.getenv('FRONTEND_LOCAL_URI', 'http://localhost:3000')}/auth/callback"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    CORS_ALLOW_ORIGIN_REGEX: str = ".*"

class ProductionConfig(BaseConfig):
    FRONTEND_URI: str = os.getenv("FRONTEND_LIVE_URI", "https://taimako.dubem.xyz")
    FRONTEND_REDIRECT_URI: str = f"{os.getenv('FRONTEND_LIVE_URI', 'https://taimako.dubem.xyz')}/auth/callback"
    
    CORS_ORIGINS: List[str] = [
        "https://taimako.dubem.xyz", 
        "https://www.taimako.dubem.xyz"
    ]
    CORS_ALLOW_ORIGIN_REGEX: str = r"https?://.*"
    
    ALLOWED_HOSTS: List[str] = [
        "taimako.dubem.xyz", 
        "api.taimako.dubem.xyz",
        "*.taimako.dubem.xyz"
    ]
    # USE_HTTPS_REDIRECT: bool = True # Uncomment if handling SSL termination directly

@lru_cache()
def get_settings():
    env = os.getenv("ENVIRONMENT", "local")
    if env == "production":
        return ProductionConfig()
    elif env == "staging":
        # Treating staging similar to prod for now, or can be its own class
        return ProductionConfig()
    return LocalConfig()

settings = get_settings()
