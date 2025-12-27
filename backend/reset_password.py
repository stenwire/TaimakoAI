#!/usr/bin/env python3
"""Quick script to reset a user's password."""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, '/app')

from app.db.session import SessionLocal
from app.models.user import User
from app.models.business import Business  # Import to resolve relationship
from app.core.security import get_password_hash

def reset_password(email: str, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User with email {email} not found!")
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"Password reset successfully for {email}")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    reset_password(email, new_password)
