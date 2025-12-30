from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.env = os.getenv("ENVIRONMENT", "local")

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Standard Security Headers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (Production/Staging only)
        if self.env in ["production", "staging"]:
            # 63072000 seconds = 2 years
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
            
        return response
