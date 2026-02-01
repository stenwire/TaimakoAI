from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.db.base import Base

class EscalationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

def generate_uuid():
    return str(uuid.uuid4())

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), unique=True, nullable=False)
    
    status = Column(String, default=EscalationStatus.PENDING.value)
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    business = relationship("Business", backref="escalations")
    session = relationship("ChatSession", backref="escalation")
