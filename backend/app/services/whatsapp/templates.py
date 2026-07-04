"""Template business logic: draft → submit → import lifecycle."""
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.widget import WidgetSettings
from app.models.whatsapp_broadcast import (
    TemplateSource,
    TemplateStatus,
    WhatsAppTemplate,
)
from app.services.whatsapp import client as wa_client

VARIABLE_PATTERN = re.compile(r"\{\{\s*(\d+)\s*\}\}")


def extract_variables(body_text: str) -> list[str]:
    """Extract ordered, unique `{{n}}` variable placeholders."""
    seen: list[str] = []
    for match in VARIABLE_PATTERN.finditer(body_text or ""):
        key = match.group(1)
        if key not in seen:
            seen.append(key)
    return seen


def _get_waba_credentials(db: Session, business_id: str) -> tuple[str, str] | None:
    """Return (waba_id, access_token) for the business, or None if unconfigured."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return None
    widget = (
        db.query(WidgetSettings)
        .filter(WidgetSettings.user_id == business.user_id)
        .first()
    )
    if not widget or not widget.whatsapp_business_account_id or not widget.whatsapp_access_token:
        return None
    return widget.whatsapp_business_account_id, widget.whatsapp_access_token


def build_components(template: WhatsAppTemplate) -> list[dict]:
    """Build Meta's component schema from a WhatsAppTemplate row."""
    components: list[dict] = []
    if template.header:
        components.append(template.header)
    components.append({"type": "BODY", "text": template.body_text})
    if template.footer:
        components.append({"type": "FOOTER", "text": template.footer})
    if template.buttons:
        components.append({"type": "BUTTONS", "buttons": template.buttons})
    return components


def create_draft(
    db: Session,
    business_id: str,
    *,
    name: str,
    category: str,
    language: str,
    body_text: str,
    header: dict | None = None,
    footer: str | None = None,
    buttons: list | None = None,
) -> WhatsAppTemplate:
    template = WhatsAppTemplate(
        business_id=business_id,
        name=name,
        category=category,
        language=language,
        body_text=body_text,
        header=header,
        footer=footer,
        buttons=buttons,
        variables=extract_variables(body_text),
        status=TemplateStatus.DRAFT.value,
        source=TemplateSource.CREATED.value,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_draft(
    db: Session,
    template: WhatsAppTemplate,
    *,
    name: str | None = None,
    category: str | None = None,
    language: str | None = None,
    body_text: str | None = None,
    header: dict | None = None,
    footer: str | None = None,
    buttons: list | None = None,
) -> WhatsAppTemplate:
    if template.status != TemplateStatus.DRAFT.value:
        raise ValueError(
            f"Cannot edit template in status {template.status}; only DRAFT templates are editable"
        )
    if name is not None:
        template.name = name
    if category is not None:
        template.category = category
    if language is not None:
        template.language = language
    if body_text is not None:
        template.body_text = body_text
        template.variables = extract_variables(body_text)
    if header is not None:
        template.header = header or None
    if footer is not None:
        template.footer = footer or None
    if buttons is not None:
        template.buttons = buttons or None
    db.commit()
    db.refresh(template)
    return template


async def submit_to_meta(db: Session, template: WhatsAppTemplate) -> WhatsAppTemplate:
    creds = _get_waba_credentials(db, template.business_id)
    if not creds:
        raise ValueError("WhatsApp Business Account not configured for this business")

    waba_id, access_token = creds
    components = build_components(template)
    data = await wa_client.create_template(
        waba_id=waba_id,
        access_token=access_token,
        name=template.name,
        category=template.category,
        language=template.language,
        components=components,
    )
    template.meta_template_id = data.get("id")
    status = (data.get("status") or "PENDING").upper()
    template.status = status
    db.commit()
    db.refresh(template)
    return template


async def import_from_meta(db: Session, business_id: str) -> list[WhatsAppTemplate]:
    """Fetch templates from Meta and upsert APPROVED ones as IMPORTED rows."""
    creds = _get_waba_credentials(db, business_id)
    if not creds:
        raise ValueError("WhatsApp Business Account not configured for this business")

    waba_id, access_token = creds
    remote = await wa_client.list_templates(waba_id, access_token)

    imported: list[WhatsAppTemplate] = []
    for remote_tpl in remote:
        if (remote_tpl.get("status") or "").upper() != "APPROVED":
            continue
        name = remote_tpl.get("name")
        language = remote_tpl.get("language")
        if not name or not language:
            continue

        existing = (
            db.query(WhatsAppTemplate)
            .filter(
                WhatsAppTemplate.business_id == business_id,
                WhatsAppTemplate.name == name,
                WhatsAppTemplate.language == language,
            )
            .first()
        )

        components = remote_tpl.get("components", []) or []
        body_text = ""
        header = None
        footer = None
        buttons = None
        for comp in components:
            ctype = (comp.get("type") or "").upper()
            if ctype == "BODY":
                body_text = comp.get("text", "")
            elif ctype == "HEADER":
                header = comp
            elif ctype == "FOOTER":
                footer = comp.get("text")
            elif ctype == "BUTTONS":
                buttons = comp.get("buttons")

        fields: dict[str, Any] = {
            "meta_template_id": remote_tpl.get("id"),
            "category": remote_tpl.get("category", "MARKETING"),
            "header": header,
            "body_text": body_text,
            "footer": footer,
            "buttons": buttons,
            "variables": extract_variables(body_text),
            "status": TemplateStatus.APPROVED.value,
            "source": TemplateSource.IMPORTED.value,
        }

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            imported.append(existing)
        else:
            tpl = WhatsAppTemplate(
                business_id=business_id,
                name=name,
                language=language,
                **fields,
            )
            db.add(tpl)
            imported.append(tpl)

    db.commit()
    for tpl in imported:
        db.refresh(tpl)
    return imported


async def delete_template(db: Session, template: WhatsAppTemplate) -> None:
    if template.meta_template_id:
        creds = _get_waba_credentials(db, template.business_id)
        if creds:
            waba_id, access_token = creds
            try:
                await wa_client.delete_template(waba_id, access_token, template.name)
            except Exception:
                pass
    db.delete(template)
    db.commit()
