from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Templates ----------


class TemplateCreateRequest(BaseModel):
    name: str
    category: str  # MARKETING / UTILITY / AUTHENTICATION
    language: str = "en_US"
    body_text: str
    header: Optional[dict] = None
    footer: Optional[str] = None
    buttons: Optional[list[dict]] = None


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    body_text: Optional[str] = None
    header: Optional[dict] = None
    footer: Optional[str] = None
    buttons: Optional[list[dict]] = None


class TemplateResponse(BaseModel):
    id: str
    business_id: str
    meta_template_id: Optional[str] = None
    name: str
    category: str
    language: str
    header: Optional[dict] = None
    body_text: str
    footer: Optional[str] = None
    buttons: Optional[list] = None
    variables: Optional[list] = None
    status: str
    rejection_reason: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Contacts ----------


class ContactCreateRequest(BaseModel):
    phone: str
    name: Optional[str] = None
    tags: Optional[list[str]] = None
    opted_in: bool = True


class ContactUpdateRequest(BaseModel):
    name: Optional[str] = None
    tags: Optional[list[str]] = None
    opted_in: Optional[bool] = None


class ContactResponse(BaseModel):
    id: str
    business_id: str
    phone_e164: str
    name: Optional[str] = None
    tags: Optional[list] = None
    source: str
    opted_in: bool
    last_contacted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactCsvImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


class GuestImportRequest(BaseModel):
    min_sessions: int = 1
    last_seen_after: Optional[datetime] = None


class GuestImportResponse(BaseModel):
    imported: int


# ---------- Contact Lists ----------


class ContactListCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ContactListUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ContactListResponse(BaseModel):
    id: str
    business_id: str
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactListMembersRequest(BaseModel):
    contact_ids: list[str]


# ---------- Campaigns ----------


class CampaignCreateRequest(BaseModel):
    name: str
    template_id: str
    audience_type: str  # LIST / GUESTS_FILTER / ADHOC
    audience_ref: dict = Field(default_factory=dict)
    variable_mapping: dict = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    send_now: bool = False


class CampaignSendRequest(BaseModel):
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: str
    business_id: str
    name: str
    template_id: str
    audience_type: str
    audience_ref: Optional[dict] = None
    variable_mapping: Optional[dict] = None
    status: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignMessageResponse(BaseModel):
    id: str
    campaign_id: str
    contact_phone: str
    variables_snapshot: Optional[dict] = None
    meta_message_id: Optional[str] = None
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
