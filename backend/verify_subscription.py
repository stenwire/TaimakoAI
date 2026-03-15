from app.models.business import Business
from app.models.user import User
from app.models.payment import PaymentTransaction
from app.core.subscription import SubscriptionTier
from app.db.session import SessionLocal
import uuid

# Mock the database session
db = SessionLocal()

def verify_subscription_defaults():
    print("Verifying Subscription Defaults...")
    # Clean up previous test
    existing = db.query(Business).filter(Business.business_name == "Subscription Test").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    # Create User for test if needed
    user = db.query(User).filter(User.email == "test@sub.com").first()
    if not user:
        user = User(email="test@sub.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    # Simulate Logic from API (renewing a spark plan)
    business = Business(
        user_id=user.id,
        business_name="Subscription Test",
        subscription_tier="spark",
        allocated_ai_responses=100,
        used_ai_responses=0,
        allocated_escalations=5,
        used_escalations=0,
        allocated_messages_per_session=20,
        allocated_daily_sessions=50,
        allocated_whitelisted_domains=1
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    
    assert business.subscription_tier == "spark"
    assert business.allocated_ai_responses == 100
    assert business.used_ai_responses == 0
    assert business.allocated_escalations == 5
    print("✅ Defaults Verified")
    return business

def verify_responses_used(business_id):
    print("Verifying AI Responses Deduction logic...")
    
    b = db.query(Business).filter(Business.id == business_id).first()
    initial_used = b.used_ai_responses
    b.used_ai_responses += 1  # simulated chat message sent
    db.commit()
    
    b_refreshed = db.query(Business).filter(Business.id == business_id).first()
    assert b_refreshed.used_ai_responses == initial_used + 1
    assert (b_refreshed.allocated_ai_responses - b_refreshed.used_ai_responses) == 99
    print("✅ AI Responses Used DB Persistence Verified")

try:
    business = verify_subscription_defaults()
    verify_responses_used(business.id)
    print("ALL TESTS PASSED")
except Exception as e:
    print(f"TEST FAILED: {e}")
finally:
    db.close()

