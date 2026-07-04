import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from app.models.mixins import SerializerMixin

def generate_uuid():
    return str(uuid.uuid4())

class PaymentTransaction(Base, SerializerMixin):
    __tablename__ = "payment_transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    
    amount = Column(Integer, nullable=False) # In minor units (e.g. kobo)
    currency = Column(String, default="NGN")
    
    status = Column(String, nullable=False) # success, failed, pending
    reference = Column(String, unique=True, nullable=False, index=True) # Provider reference
    provider = Column(String, default="paystack")
    
    transaction_type = Column(String, nullable=False) # subscription_creation, renewal
    
    transaction_metadata = Column(JSON, nullable=True)
    raw_webhook_payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    business = relationship("Business", back_populates="transactions")

