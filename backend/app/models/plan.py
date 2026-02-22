from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from datetime import datetime
from app.db.base import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, default=0, nullable=False)
    currency = Column(String, default="NGN", nullable=False)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

from sqladmin import ModelView

class PlanAdmin(ModelView, model=Plan):
    column_list = [Plan.id, Plan.name, Plan.plan_code, Plan.price, Plan.is_active]

