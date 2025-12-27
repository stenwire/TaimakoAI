from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from app.api.routes import router

from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.auth.router import router as auth_router
from app.db.base import Base
from app.db.session import engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Create tables (if not using alembic, but we are. Keeping for dev convenience or removing if strictly alembic)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic RAG API",
    description="API for Agentic RAG with Google OAuth2 and Multi-Agent Delegation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:5500",
#     "http://localhost:8000",
# ]

origins = ["http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
