import os
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

from app.api.routes import router as api_router
from app.auth.router import router as auth_router
from app.db.base import Base
from app.db.session import engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.middleware import register_middleware

# Create tables (if not using alembic, but we are. Keeping for dev convenience or removing if strictly alembic)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Taimako API",
    description="API for Taimako.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register Middleware (CORS, Security, Rate Limiting)
register_middleware(app)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router)
app.include_router(auth_router)

# Import and include business router
from app.api.business import router as business_router
app.include_router(business_router)

from app.api.widget import router as widget_router
app.include_router(widget_router, prefix="/widgets", tags=["widgets"])

from app.api.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

from app.api.escalation import router as escalation_router
app.include_router(escalation_router, prefix="/escalations", tags=["escalations"])

from app.core.response_wrapper import success_response

@app.get("/")
async def root():
    return success_response(message="Agentic RAG API is running")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
