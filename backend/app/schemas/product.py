from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str = "USD"
    sku: str
    stock_quantity: int = 0
    category: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    sku: Optional[str] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductBulkUpload(BaseModel):
    products: List[ProductCreate]
