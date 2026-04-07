from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from datetime import datetime
from app.db.base import Base
from app.models.mixins import SerializerMixin

class Plan(Base, SerializerMixin):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, default=0, nullable=False)
    currency = Column(String, default="NGN", nullable=False)
    interval = Column(String, default="monthly", nullable=False)  # monthly, annually
    tier = Column(Integer, default=0, server_default="0", nullable=False)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

