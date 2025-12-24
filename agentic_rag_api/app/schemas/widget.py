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
    session_id: str
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
    welcome_message: Optional[str]
    initial_ai_message: Optional[str]
    initial_ai_message: Optional[str]
    send_initial_message_automatically: Optional[bool] = True
    whatsapp_enabled: Optional[bool] = False
    whatsapp_number: Optional[str] = None
    
    class Config:
        from_attributes = True

# Context Data
class WidgetContext(BaseModel):
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

# Session Management
class SessionStartRequest(BaseModel):
    guest_id: str
    message: str
    origin: str = "auto-start" # manual, auto-start, resumed
    context: Optional[WidgetContext] = None

class SessionHistoryResponse(BaseModel):
    id: str
    created_at: datetime
    last_message_at: datetime
    origin: str
    summary: Optional[str] = None
    summary_generated_at: Optional[datetime] = None
    top_intent: Optional[str] = None
    
    # Context
    country: Optional[str] = None
    city: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None

    class Config:
        from_attributes = True
