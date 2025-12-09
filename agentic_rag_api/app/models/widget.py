import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

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

    # Relationships
    widget = relationship("WidgetSettings", back_populates="guests")
    messages = relationship("GuestMessage", back_populates="guest")

class GuestMessage(Base):
    __tablename__ = "guest_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    guest_id = Column(String, ForeignKey("guest_users.id"), nullable=False)
    sender = Column(String, nullable=False) # "guest" or "ai"
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    guest = relationship("GuestUser", back_populates="messages")
