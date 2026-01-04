from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from app.api.routes import router as api_router
from app.auth.router import router as auth_router
from app.db.base import Base
from app.db.session import engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.security_headers import SecurityHeadersMiddleware

# Create tables (if not using alembic, but we are. Keeping for dev convenience or removing if strictly alembic)
# Base.metadata.create_all(bind=engine)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="Agentic RAG API",
    description="API for Agentic RAG with Google OAuth2 and Multi-Agent Delegation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Associate limiter with app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Environment
environment = os.getenv("ENVIRONMENT", "local")

# Rate Limit Middleware
app.add_middleware(SlowAPIMiddleware)

# Security Middlewares
# I am commenting out the HTTPS redirect middleware for now
# because this project is hosted behind a reverse proxy
# if environment in ["production", "staging"]:
    # app.add_middleware(HTTPSRedirectMiddleware)
    
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.taimako.dubem.xyz", "taimako.dubem.xyz", "*.staging.taimako.ai", "api.taimako.dubem.xyz"]
)

app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:5500",
#     "http://localhost:8000",
# ]

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://taimako.dubem.xyz",
    "https://taimako.dubem.xyz/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(auth_router)

# Import and include business router
from app.api.business import router as business_router
app.include_router(business_router)

from app.api.widget import router as widget_router
app.include_router(widget_router, prefix="/widgets", tags=["widgets"])

from app.api.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

from app.core.response_wrapper import success_response

@app.get("/")
async def root():
    return success_response(message="Agentic RAG API is running")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
