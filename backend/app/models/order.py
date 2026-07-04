import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


def _uuid():
    return str(uuid.uuid4())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=_uuid)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_address = Column(Text, nullable=True)

    status = Column(String, nullable=False, default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    product_name = Column(String, nullable=False)
    product_sku = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="USD")

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
