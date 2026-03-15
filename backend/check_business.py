import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.business import Business

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

businesses = db.query(Business).all()
for b in businesses:
    print(f"Business: {b.business_name} | Email: {b.user.email if b.user else 'No User'}")
    print(f"Tier: {b.subscription_tier}")
    print(f"AI Responses: {b.allocated_ai_responses}")
    print(f"Daily Sessions: {b.allocated_daily_sessions}")
    print("-" * 40)
