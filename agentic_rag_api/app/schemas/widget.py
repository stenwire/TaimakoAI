from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Guest Start
class GuestStartRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class GuestStartResponse(BaseModel):
    guest_id: str
    widget_owner_id: str
    status: str

# Guest Listing
class GuestUserResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Chat
class WidgetChatRequest(BaseModel):
    message: str

class GuestMessageSchema(BaseModel):
    id: str
    guest_id: str
    sender: str  # "guest" or "ai"
    message_text: str
    created_at: datetime

    class Config:
        from_attributes = True

class WidgetChatResponse(BaseModel):
    message: GuestMessageSchema
    response: GuestMessageSchema

# Config
class WidgetConfigResponse(BaseModel):
    public_widget_id: str
    theme: str
    primary_color: str
    icon_url: Optional[str]
    # We might want to add owner info if needed, but usually not exposed
    
    class Config:
        from_attributes = True
