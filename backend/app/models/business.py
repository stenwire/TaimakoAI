import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from app.models.mixins import SerializerMixin

# Detailed placeholder instruction used when a business does not provide a custom one.
DEFAULT_AGENT_INSTRUCTION_PLACEHOLDER = (
    "You are a helpful, friendly, and professional customer support assistant. "
    "Always address the user politely, reference the business name where appropriate, and "
    "provide concise, accurate answers based on the provided context. "
    "If you do not know the answer, admit it and suggest how the user might obtain the information. "
    "Maintain a tone that reflects the brand's values and ensure data privacy."
)

def generate_uuid():
    return str(uuid.uuid4())

class Business(Base, SerializerMixin):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    business_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    custom_agent_instruction = Column(Text, nullable=True, default=DEFAULT_AGENT_INSTRUCTION_PLACEHOLDER)
    intents = Column(JSON, nullable=True)
    is_escalation_enabled = Column(Boolean, default=False)
    escalation_emails = Column(JSON, nullable=True) # List of emails
    
    # Subscription Fields
    subscription_tier = Column(String, default="spark", nullable=False)
    
    # AI Responses
    allocated_ai_responses = Column(Integer, default=0, nullable=False)
    used_ai_responses = Column(Integer, default=0, nullable=False)
    credits_last_refilled = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Escalations
    allocated_escalations = Column(Integer, default=0, nullable=False)
    used_escalations = Column(Integer, default=0, nullable=False)
    
    # Other Limits
    allocated_messages_per_session = Column(Integer, default=0, nullable=False)
    allocated_daily_sessions = Column(Integer, default=0, nullable=False)
    allocated_whitelisted_domains = Column(Integer, default=0, nullable=False)

    # Payment / Subscription (Generic)
    payment_provider = Column(String, default="paystack") # paystack, stripe
    payment_customer_id = Column(String, nullable=True)     # generic customer id
    payment_subscription_id = Column(String, nullable=True) # generic subscription id
    subscription_status = Column(String, default="active")  # active, non-renewing, attention, cancelled, trial
    authorization_code = Column(String, nullable=True)       # saved card token for upgrades
    subscription_email_token = Column(String, nullable=True) # required to cancel/disable subscription
    last_payment_date = Column(DateTime, nullable=True)      # most recent successful charge

    logo_url = Column(String, nullable=True) # URL to business logo
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="business")
    transactions = relationship("PaymentTransaction", back_populates="business", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="business", cascade="all, delete-orphan")

    # metadata = Column(JSON, nullable=True)

