"""Campaign creation, recipient expansion, and execution."""
import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.chat_session import ChatSession, SessionChannel
from app.models.widget import GuestUser, WidgetSettings
from app.models.whatsapp_broadcast import (
    CampaignAudienceType,
    CampaignMessageStatus,
    CampaignStatus,
    TemplateStatus,
    WhatsAppCampaign,
    WhatsAppCampaignMessage,
    WhatsAppContact,
    WhatsAppContactListMember,
    WhatsAppTemplate,
)
from app.services.whatsapp import client as wa_client
from app.services.whatsapp.contacts import normalize_phone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_widget(db: Session, business_id: str) -> WidgetSettings | None:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return None
    return (
        db.query(WidgetSettings)
        .filter(WidgetSettings.user_id == business.user_id)
        .first()
    )


class RecipientExpansion:
    """Per-recipient payload returned by expand_recipients."""

    def __init__(self, phone: str, variables: dict[str, str]):
        self.phone = phone
        self.variables = variables


def expand_recipients(
    db: Session, campaign: WhatsAppCampaign
) -> list[RecipientExpansion]:
    """Resolve audience_ref into a concrete list of (phone, variables)."""
    audience_type = campaign.audience_type
    audience_ref = campaign.audience_ref or {}
    variable_mapping = campaign.variable_mapping or {}

    contacts: list[WhatsAppContact] = []
    ad_hoc_phones: list[str] = []

    if audience_type == CampaignAudienceType.LIST.value:
        list_id = audience_ref.get("list_id")
        if not list_id:
            return []
        contacts = (
            db.query(WhatsAppContact)
            .join(
                WhatsAppContactListMember,
                WhatsAppContactListMember.contact_id == WhatsAppContact.id,
            )
            .filter(
                WhatsAppContactListMember.contact_list_id == list_id,
                WhatsAppContact.business_id == campaign.business_id,
                WhatsAppContact.opted_in.is_(True),
            )
            .all()
        )

    elif audience_type == CampaignAudienceType.GUESTS_FILTER.value:
        widget = _get_widget(db, campaign.business_id)
        if not widget:
            return []
        query = (
            db.query(GuestUser)
            .join(ChatSession, ChatSession.guest_id == GuestUser.id)
            .filter(
                GuestUser.widget_id == widget.id,
                GuestUser.phone.isnot(None),
                ChatSession.channel == SessionChannel.WHATSAPP.value,
            )
        )
        min_sessions = audience_ref.get("min_sessions")
        if min_sessions:
            query = query.filter(GuestUser.total_sessions >= int(min_sessions))
        last_seen_after = audience_ref.get("last_seen_after")
        if last_seen_after:
            query = query.filter(GuestUser.last_seen_at >= datetime.fromisoformat(last_seen_after))
        guests = query.distinct().all()
        for g in guests:
            normalized = normalize_phone(g.phone)
            if normalized:
                ad_hoc_phones.append(normalized)

    elif audience_type == CampaignAudienceType.ADHOC.value:
        phones = audience_ref.get("phones", []) or []
        for p in phones:
            normalized = normalize_phone(p)
            if normalized:
                ad_hoc_phones.append(normalized)

    recipients: list[RecipientExpansion] = []
    seen_phones: set[str] = set()

    for contact in contacts:
        if contact.phone_e164 in seen_phones:
            continue
        seen_phones.add(contact.phone_e164)
        variables = _resolve_variables(variable_mapping, contact=contact)
        recipients.append(RecipientExpansion(contact.phone_e164, variables))

    for phone in ad_hoc_phones:
        if phone in seen_phones:
            continue
        seen_phones.add(phone)
        variables = _resolve_variables(variable_mapping, contact=None)
        recipients.append(RecipientExpansion(phone, variables))

    return recipients


def _resolve_variables(
    variable_mapping: dict[str, Any], *, contact: WhatsAppContact | None
) -> dict[str, str]:
    """Resolve the variable_mapping config into concrete per-recipient values.

    variable_mapping shape: {"1": {"type": "literal", "value": "Hello"}}
    or {"1": {"type": "field", "field": "name"}}.
    """
    resolved: dict[str, str] = {}
    for key, spec in variable_mapping.items():
        if not isinstance(spec, dict):
            resolved[key] = str(spec or "")
            continue
        kind = spec.get("type", "literal")
        if kind == "literal":
            resolved[key] = str(spec.get("value") or "")
        elif kind == "field" and contact is not None:
            field = spec.get("field") or ""
            resolved[key] = str(getattr(contact, field, "") or "")
        else:
            resolved[key] = ""
    return resolved


def create_campaign(
    db: Session,
    business_id: str,
    *,
    name: str,
    template_id: str,
    audience_type: str,
    audience_ref: dict,
    variable_mapping: dict,
    created_by_user_id: str | None,
    scheduled_at: datetime | None = None,
) -> WhatsAppCampaign:
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business_id,
        )
        .first()
    )
    if not template:
        raise ValueError("Template not found")
    if template.status != TemplateStatus.APPROVED.value:
        raise ValueError("Template must be APPROVED before it can be used in a campaign")

    campaign = WhatsAppCampaign(
        business_id=business_id,
        name=name,
        template_id=template_id,
        audience_type=audience_type,
        audience_ref=audience_ref,
        variable_mapping=variable_mapping,
        status=CampaignStatus.DRAFT.value,
        scheduled_at=scheduled_at,
        created_by_user_id=created_by_user_id,
    )
    db.add(campaign)
    db.flush()

    recipients = expand_recipients(db, campaign)
    campaign.total_recipients = len(recipients)
    for r in recipients:
        db.add(
            WhatsAppCampaignMessage(
                campaign_id=campaign.id,
                contact_phone=r.phone,
                variables_snapshot=r.variables,
                status=CampaignMessageStatus.QUEUED.value,
            )
        )
    db.commit()
    db.refresh(campaign)
    return campaign


def schedule_campaign(
    db: Session, campaign: WhatsAppCampaign, scheduled_at: datetime | None
) -> WhatsAppCampaign:
    if campaign.status != CampaignStatus.DRAFT.value:
        raise ValueError(f"Cannot schedule campaign in status {campaign.status}")
    campaign.scheduled_at = scheduled_at or utcnow()
    campaign.status = CampaignStatus.SCHEDULED.value
    db.commit()
    db.refresh(campaign)
    return campaign


def cancel_campaign(db: Session, campaign: WhatsAppCampaign) -> WhatsAppCampaign:
    if campaign.status not in (
        CampaignStatus.DRAFT.value,
        CampaignStatus.SCHEDULED.value,
        CampaignStatus.SENDING.value,
    ):
        raise ValueError(f"Cannot cancel campaign in status {campaign.status}")
    campaign.status = CampaignStatus.CANCELLED.value
    campaign.completed_at = utcnow()
    db.commit()
    db.refresh(campaign)
    return campaign


def _build_components_for_send(
    template: WhatsAppTemplate, variables: dict[str, str]
) -> list[dict]:
    """Assemble the per-message components payload from the template + variable values."""
    ordered_keys = template.variables or []
    components: list[dict] = []
    if ordered_keys:
        parameters = [
            {"type": "text", "text": variables.get(key, "")} for key in ordered_keys
        ]
        components.append({"type": "body", "parameters": parameters})
    return components


async def execute_campaign(
    db: Session,
    campaign: WhatsAppCampaign,
    *,
    rate_per_second: int = 20,
) -> None:
    """Send all QUEUED messages for a campaign. Caller must hold the row lock."""
    widget = _get_widget(db, campaign.business_id)
    if not widget or not widget.whatsapp_phone_number_id or not widget.whatsapp_access_token:
        campaign.status = CampaignStatus.FAILED.value
        campaign.completed_at = utcnow()
        db.commit()
        return

    template = (
        db.query(WhatsAppTemplate).filter(WhatsAppTemplate.id == campaign.template_id).first()
    )
    if not template:
        campaign.status = CampaignStatus.FAILED.value
        campaign.completed_at = utcnow()
        db.commit()
        return

    campaign.started_at = utcnow()
    campaign.status = CampaignStatus.SENDING.value
    db.commit()

    delay = 1.0 / rate_per_second if rate_per_second > 0 else 0.0

    queued_messages = (
        db.query(WhatsAppCampaignMessage)
        .filter(
            WhatsAppCampaignMessage.campaign_id == campaign.id,
            WhatsAppCampaignMessage.status == CampaignMessageStatus.QUEUED.value,
        )
        .all()
    )

    for msg in queued_messages:
        # Re-check cancellation between sends.
        db.refresh(campaign)
        if campaign.status == CampaignStatus.CANCELLED.value:
            return

        components = _build_components_for_send(template, msg.variables_snapshot or {})
        try:
            resp = await wa_client.send_template_message(
                phone_number_id=widget.whatsapp_phone_number_id,
                access_token=widget.whatsapp_access_token,
                to_phone=msg.contact_phone,
                template_name=template.name,
                language=template.language,
                components=components,
            )
            meta_id = None
            try:
                meta_id = (resp.get("messages") or [{}])[0].get("id")
            except Exception:
                meta_id = None
            msg.meta_message_id = meta_id
            msg.status = CampaignMessageStatus.SENT.value
            msg.sent_at = utcnow()
            campaign.sent_count += 1
        except Exception as e:
            msg.status = CampaignMessageStatus.FAILED.value
            msg.error_message = str(e)[:500]
            campaign.failed_count += 1

        db.commit()

        if delay > 0:
            await asyncio.sleep(delay)

    campaign.status = CampaignStatus.COMPLETED.value
    campaign.completed_at = utcnow()
    db.commit()
