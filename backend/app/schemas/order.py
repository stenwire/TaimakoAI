from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]


class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    product_id: Optional[str] = None
    product_name: str
    product_sku: str
    quantity: int
    unit_price: float
    total_price: float
    currency: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    business_id: str
    session_id: Optional[str] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    status: str
    total_amount: float
    currency: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
