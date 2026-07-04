from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin

from app.api.routes import router as api_router
from app.auth.router import router as auth_router
from app.api.business import router as business_router
from app.api.widget import router as widget_router
from app.api.analytics import router as analytics_router
from app.api.escalation import router as escalation_router
from app.api.subscription import router as subscription_router
from app.api.plans import router as plans_router
from app.api.whatsapp import router as whatsapp_router
from app.api.whatsapp_templates import router as whatsapp_templates_router
from app.api.whatsapp_contacts import router as whatsapp_contacts_router
from app.api.whatsapp_campaigns import router as whatsapp_campaigns_router
from app.api.orders import router as orders_router

from app.core.config import settings
from app.db.session import engine
from app.core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.middleware import register_middleware
from app.core.response_wrapper import success_response
from app.admin.auth import AdminAuth
from app.admin.views import (
    UserAdmin, BusinessAdmin, PlanAdmin, PaymentTransactionAdmin,
    ChatSessionAdmin, GuestMessageAdmin, EscalationAdmin,
    WidgetSettingsAdmin, GuestUserAdmin, DocumentAdmin,
    AnalyticsDailySummaryAdmin, ProductAdmin,
)

app = FastAPI(
    title="Taimako API",
    description="API for Taimako.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Session middleware (required for SQLAdmin cookie-based auth)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

# Admin panel at /hub with authentication
authentication_backend = AdminAuth(secret_key=settings.JWT_SECRET)
admin = Admin(
    app,
    engine,
    authentication_backend=authentication_backend,
    base_url="/hub",
    title="Taimako Admin",
)

admin.add_view(UserAdmin)
admin.add_view(BusinessAdmin)
admin.add_view(PlanAdmin)
admin.add_view(PaymentTransactionAdmin)
admin.add_view(ChatSessionAdmin)
admin.add_view(GuestMessageAdmin)
admin.add_view(EscalationAdmin)
admin.add_view(WidgetSettingsAdmin)
admin.add_view(GuestUserAdmin)
admin.add_view(DocumentAdmin)
admin.add_view(AnalyticsDailySummaryAdmin)
admin.add_view(ProductAdmin)

# Register Middleware (CORS, Security, Rate Limiting)
register_middleware(app)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(widget_router, prefix="/widgets", tags=["widgets"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(escalation_router, prefix="/escalations", tags=["escalations"])
app.include_router(subscription_router, tags=["subscription"])
app.include_router(plans_router, tags=["plans"])
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(whatsapp_templates_router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(whatsapp_contacts_router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(whatsapp_campaigns_router, prefix="/whatsapp", tags=["whatsapp"])
app.include_router(orders_router)


@app.get("/")
async def root():
    return success_response(message="Agentic RAG API is running")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
