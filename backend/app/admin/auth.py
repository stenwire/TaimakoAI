from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not user.hashed_password:
                return False
            if not verify_password(password, user.hashed_password):
                return False
            if not user.is_admin:
                return False

            request.session.update({"admin_user_id": user.id})
            return True
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_user_id = request.session.get("admin_user_id")
        if not admin_user_id:
            return False

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == admin_user_id).first()
            if not user or not user.is_admin:
                request.session.clear()
                return False
            return True
        finally:
            db.close()
