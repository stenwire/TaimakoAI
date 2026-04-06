from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError

from app.api.routes import router as api_router
from app.auth.router import router as auth_router
from app.db.session import engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.middleware import register_middleware
from sqladmin import Admin


# Create tables (if not using alembic, but we are. Keeping for dev convenience or removing if strictly alembic)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Taimako API",
    description="API for Taimako.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

admin = Admin(app, engine)

from app.models.user import UserAdmin
from app.models.business import BusinessAdmin
from app.models.payment import PaymentTransactionAdmin
from app.models.analytics import AnalyticsDailySummaryAdmin
from app.models.chat_session import ChatSessionAdmin
from app.models.document import DocumentAdmin
from app.models.escalation import EscalationAdmin
from app.models.widget import WidgetSettingsAdmin, GuestUserAdmin, GuestMessageAdmin
from app.models.plan import PlanAdmin

admin.add_view(UserAdmin)
admin.add_view(BusinessAdmin)
admin.add_view(PaymentTransactionAdmin)
admin.add_view(AnalyticsDailySummaryAdmin)
admin.add_view(ChatSessionAdmin)
admin.add_view(DocumentAdmin)
admin.add_view(EscalationAdmin)
admin.add_view(WidgetSettingsAdmin)
admin.add_view(GuestUserAdmin)
admin.add_view(GuestMessageAdmin)
admin.add_view(PlanAdmin)



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

from app.api.subscription import router as subscription_router
app.include_router(subscription_router, tags=["subscription"])

from app.api.plans import router as plans_router
app.include_router(plans_router, tags=["plans"])

from app.api.whatsapp import router as whatsapp_router
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])

from app.core.response_wrapper import success_response

@app.get("/")
async def root():
    return success_response(message="Agentic RAG API is running")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
