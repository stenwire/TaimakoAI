import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

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

class Business(Base):
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
    logo_url = Column(String, nullable=True) # URL to business logo
    gemini_api_key = Column(String, nullable=True) # Encrypted API Key
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="business")
