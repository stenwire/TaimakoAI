from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BusinessBase(BaseModel):
    business_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    custom_agent_instruction: Optional[str] = None
    intents: Optional[List[str]] = None
    logo_url: Optional[str] = None
    is_escalation_enabled: Optional[bool] = False
    escalation_emails: Optional[List[str]] = []

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    business_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    custom_agent_instruction: Optional[str] = None
    intents: Optional[List[str]] = None
    logo_url: Optional[str] = None
    is_escalation_enabled: Optional[bool] = None
    escalation_emails: Optional[List[str]] = None

class BusinessResponse(BusinessBase):
    id: str
    user_id: str
    subscription_tier: str
    subscription_status: Optional[str] = None

    allocated_ai_responses: int
    used_ai_responses: int
    credits_last_refilled: Optional[datetime] = None

    allocated_escalations: int
    used_escalations: int

    allocated_messages_per_session: int
    allocated_daily_sessions: int
    allocated_whitelisted_domains: int

    last_payment_date: Optional[datetime] = None

    plan_name: Optional[str] = None
    plan_code: Optional[str] = None
    plan_price: Optional[int] = None
    plan_currency: Optional[str] = None
    plan_interval: Optional[str] = None
    plan_features: Optional[dict] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


