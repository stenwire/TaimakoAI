"""
Create or promote a user to admin.

Usage:
    # Promote an existing user to admin:
    uv run python -m scripts.create_admin --email user@example.com

    # Create a new admin user with a password:
    uv run python -m scripts.create_admin --email admin@example.com --password securepass --name "Admin"
"""

import argparse
import sys

from app.db.session import SessionLocal
from app.models.user import User
# Import all models to resolve SQLAlchemy relationship references
from app.models.business import Business  # noqa: F401
from app.models.payment import PaymentTransaction  # noqa: F401
from app.models.chat_session import ChatSession  # noqa: F401
from app.models.widget import WidgetSettings, GuestUser, GuestMessage  # noqa: F401
from app.models.escalation import Escalation  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.analytics import AnalyticsDailySummary  # noqa: F401
from app.core.security import get_password_hash


def main():
    parser = argparse.ArgumentParser(description="Create or promote a user to admin")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", help="Password (required if creating a new user)")
    parser.add_argument("--name", help="User name (used when creating a new user)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()

        if user:
            if user.is_admin:
                print(f"User '{args.email}' is already an admin.")
                return
            user.is_admin = True
            if args.password and not user.hashed_password:
                user.hashed_password = get_password_hash(args.password)
            db.commit()
            print(f"User '{args.email}' has been promoted to admin.")
        else:
            if not args.password:
                print("Error: --password is required when creating a new user.", file=sys.stderr)
                sys.exit(1)
            user = User(
                email=args.email,
                name=args.name or "Admin",
                hashed_password=get_password_hash(args.password),
                is_admin=True,
            )
            db.add(user)
            db.commit()
            print(f"Admin user '{args.email}' created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
