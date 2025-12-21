import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from app.models.user import User
from app.models.business import Business
# Note: ChatSession is imported via string reference in relationships to avoid circular imports

def generate_uuid():
    return str(uuid.uuid4())

class WidgetSettings(Base):
    __tablename__ = "widget_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    public_widget_id = Column(String, unique=True, index=True, nullable=False, default=generate_uuid)
    theme = Column(String, default="light")
    primary_color = Column(String, default="#000000")
    icon_url = Column(String, nullable=True)
    welcome_message = Column(Text, default="Hi there! 👋")
    initial_ai_message = Column(Text, default="How can I help you today?")
    initial_ai_message = Column(Text, default="How can I help you today?")
    send_initial_message_automatically = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=False)
    whatsapp_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="widgets")
    guests = relationship("GuestUser", back_populates="widget")

class GuestUser(Base):
    __tablename__ = "guest_users"

    id = Column(String, primary_key=True, default=generate_uuid)
    widget_id = Column(String, ForeignKey("widget_settings.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Analytics
    first_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_sessions = Column(Integer, default=0)
    is_returning = Column(Boolean, default=False)

    # Relationships
    widget = relationship("WidgetSettings", back_populates="guests")
    messages = relationship("GuestMessage", back_populates="guest")
    sessions = relationship("ChatSession", back_populates="guest")

class GuestMessage(Base):
    __tablename__ = "guest_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    guest_id = Column(String, ForeignKey("guest_users.id"), nullable=False)
    # Make nullable for backward compatibility / migration, but logic should enforce it for new messages
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=True) 
    sender = Column(String, nullable=False) # "guest" or "ai"
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    guest = relationship("GuestUser", back_populates="messages")
    session = relationship("ChatSession", back_populates="messages")
