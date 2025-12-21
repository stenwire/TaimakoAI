import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
import enum

def generate_uuid():
    return str(uuid.uuid4())

class SessionOrigin(str, enum.Enum):
    MANUAL = "manual"
    AUTO_START = "auto-start"
    RESUMED = "resumed"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    guest_id = Column(String, ForeignKey("guest_users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    origin = Column(String, default=SessionOrigin.AUTO_START.value)
    summary = Column(Text, nullable=True)
    summary_generated_at = Column(DateTime, nullable=True)
    top_intent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Analytics - Context
    device_type = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)

    # Analytics - Metrics
    session_duration = Column(Integer, default=0) # Seconds
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    ai_messages = Column(Integer, default=0)
    first_response_time = Column(Integer, nullable=True) # Seconds

    # Relationships
    guest = relationship("GuestUser", back_populates="sessions")
    messages = relationship("GuestMessage", back_populates="session")
