import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import SerializerMixin


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class ContactSource(str, enum.Enum):
    MANUAL = "manual"
    CSV = "csv"
    GUEST_IMPORT = "guest_import"


class TemplateCategory(str, enum.Enum):
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"
    AUTHENTICATION = "AUTHENTICATION"


class TemplateStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"


class TemplateSource(str, enum.Enum):
    CREATED = "CREATED"
    IMPORTED = "IMPORTED"


class CampaignAudienceType(str, enum.Enum):
    LIST = "LIST"
    GUESTS_FILTER = "GUESTS_FILTER"
    ADHOC = "ADHOC"


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    SENDING = "SENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class CampaignMessageStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"


class WhatsAppContact(Base, SerializerMixin):
    __tablename__ = "whatsapp_contacts"
    __table_args__ = (
        UniqueConstraint("business_id", "phone_e164", name="uq_whatsapp_contacts_business_phone"),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    phone_e164 = Column(String, nullable=False)
    name = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    source = Column(String, default=ContactSource.MANUAL.value, nullable=False)
    opted_in = Column(Boolean, default=True, nullable=False)
    last_contacted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    business = relationship("Business", backref="whatsapp_contacts")
    list_memberships = relationship(
        "WhatsAppContactListMember", back_populates="contact", cascade="all, delete-orphan"
    )


class WhatsAppContactList(Base, SerializerMixin):
    __tablename__ = "whatsapp_contact_lists"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    business = relationship("Business", backref="whatsapp_contact_lists")
    members = relationship(
        "WhatsAppContactListMember", back_populates="contact_list", cascade="all, delete-orphan"
    )


class WhatsAppContactListMember(Base, SerializerMixin):
    __tablename__ = "whatsapp_contact_list_members"

    contact_list_id = Column(
        String, ForeignKey("whatsapp_contact_lists.id"), primary_key=True
    )
    contact_id = Column(
        String, ForeignKey("whatsapp_contacts.id"), primary_key=True
    )
    created_at = Column(DateTime, default=utcnow, nullable=False)

    contact_list = relationship("WhatsAppContactList", back_populates="members")
    contact = relationship("WhatsAppContact", back_populates="list_memberships")


class WhatsAppTemplate(Base, SerializerMixin):
    __tablename__ = "whatsapp_templates"
    __table_args__ = (
        UniqueConstraint(
            "business_id", "name", "language", name="uq_whatsapp_templates_business_name_lang"
        ),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    meta_template_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    language = Column(String, nullable=False, default="en_US")
    header = Column(JSON, nullable=True)
    body_text = Column(Text, nullable=False)
    footer = Column(String, nullable=True)
    buttons = Column(JSON, nullable=True)
    variables = Column(JSON, nullable=True)
    status = Column(String, default=TemplateStatus.DRAFT.value, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    source = Column(String, default=TemplateSource.CREATED.value, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    business = relationship("Business", backref="whatsapp_templates")


class WhatsAppCampaign(Base, SerializerMixin):
    __tablename__ = "whatsapp_campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    template_id = Column(String, ForeignKey("whatsapp_templates.id"), nullable=False)

    audience_type = Column(String, nullable=False)
    audience_ref = Column(JSON, nullable=True)
    variable_mapping = Column(JSON, nullable=True)

    status = Column(String, default=CampaignStatus.DRAFT.value, nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    total_recipients = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    read_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)

    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    business = relationship("Business", backref="whatsapp_campaigns")
    template = relationship("WhatsAppTemplate")
    messages = relationship(
        "WhatsAppCampaignMessage", back_populates="campaign", cascade="all, delete-orphan"
    )


class WhatsAppCampaignMessage(Base, SerializerMixin):
    __tablename__ = "whatsapp_campaign_messages"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "contact_phone", name="uq_whatsapp_campaign_messages_campaign_phone"
        ),
        Index("ix_whatsapp_campaign_messages_meta_id", "meta_message_id"),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(
        String, ForeignKey("whatsapp_campaigns.id"), nullable=False, index=True
    )
    contact_phone = Column(String, nullable=False)
    variables_snapshot = Column(JSON, nullable=True)
    meta_message_id = Column(String, nullable=True)
    status = Column(String, default=CampaignMessageStatus.QUEUED.value, nullable=False)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    campaign = relationship("WhatsAppCampaign", back_populates="messages")
