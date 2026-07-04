import uuid
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from datetime import datetime, timezone
from app.db.base import Base
from app.models.mixins import SerializerMixin

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base, SerializerMixin):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    sku = Column(String, nullable=False, index=True)
    stock_quantity = Column(Integer, default=0)
    category = Column(String, nullable=True, index=True)
    image_urls = Column(PG_ARRAY(String).with_variant(JSON, 'sqlite'), nullable=True) # Array of image URLs
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    business = relationship("Business", back_populates="products")
