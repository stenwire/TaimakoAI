"""Contact CRUD, CSV import, and GuestUser import."""
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.chat_session import ChatSession, SessionChannel
from app.models.widget import GuestUser, WidgetSettings
from app.models.whatsapp_broadcast import (
    ContactSource,
    WhatsAppContact,
    WhatsAppContactList,
    WhatsAppContactListMember,
)

# Minimal E.164 validator: leading +, 8–15 digits total.
E164_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")


def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    cleaned = re.sub(r"[\s\-()]", "", raw.strip())
    if not cleaned:
        return None
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned if E164_PATTERN.match(cleaned) else None


@dataclass
class CsvImportResult:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def create_contact(
    db: Session,
    business_id: str,
    *,
    phone: str,
    name: str | None = None,
    tags: list[str] | None = None,
    source: str = ContactSource.MANUAL.value,
    opted_in: bool = True,
) -> WhatsAppContact:
    normalized = normalize_phone(phone)
    if not normalized:
        raise ValueError(f"Invalid phone number: {phone}")

    existing = (
        db.query(WhatsAppContact)
        .filter(
            WhatsAppContact.business_id == business_id,
            WhatsAppContact.phone_e164 == normalized,
        )
        .first()
    )
    if existing:
        if name is not None:
            existing.name = name
        if tags is not None:
            existing.tags = tags
        existing.opted_in = opted_in
        db.commit()
        db.refresh(existing)
        return existing

    contact = WhatsAppContact(
        business_id=business_id,
        phone_e164=normalized,
        name=name,
        tags=tags,
        source=source,
        opted_in=opted_in,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def import_csv(db: Session, business_id: str, file_bytes: bytes) -> CsvImportResult:
    """Import contacts from a CSV with headers: phone, name (optional), tags (optional, comma-sep)."""
    result = CsvImportResult()
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.errors.append("File is not valid UTF-8")
        return result

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "phone" not in [h.lower() for h in reader.fieldnames]:
        result.errors.append("CSV must have a 'phone' header column")
        return result

    # Normalize headers to lowercase for lookup
    for row_num, row in enumerate(reader, start=2):
        row_lower = {(k or "").lower(): v for k, v in row.items()}
        raw_phone = (row_lower.get("phone") or "").strip()
        if not raw_phone:
            result.skipped += 1
            continue
        normalized = normalize_phone(raw_phone)
        if not normalized:
            result.errors.append(f"Row {row_num}: invalid phone '{raw_phone}'")
            result.skipped += 1
            continue

        name = (row_lower.get("name") or "").strip() or None
        tags_raw = (row_lower.get("tags") or "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

        existing = (
            db.query(WhatsAppContact)
            .filter(
                WhatsAppContact.business_id == business_id,
                WhatsAppContact.phone_e164 == normalized,
            )
            .first()
        )
        if existing:
            if name and not existing.name:
                existing.name = name
            if tags:
                existing.tags = tags
            result.skipped += 1
            continue

        contact = WhatsAppContact(
            business_id=business_id,
            phone_e164=normalized,
            name=name,
            tags=tags,
            source=ContactSource.CSV.value,
            opted_in=True,
        )
        db.add(contact)
        result.imported += 1

    db.commit()
    return result


def import_from_guests(
    db: Session,
    business_id: str,
    *,
    min_sessions: int = 1,
    last_seen_after: datetime | None = None,
) -> int:
    """Import phone-bearing GuestUsers from WhatsApp channel sessions into contacts."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return 0

    widget_ids = [
        w.id
        for w in db.query(WidgetSettings)
        .filter(WidgetSettings.user_id == business.user_id)
        .all()
    ]
    if not widget_ids:
        return 0

    query = (
        db.query(GuestUser)
        .join(ChatSession, ChatSession.guest_id == GuestUser.id)
        .filter(
            GuestUser.widget_id.in_(widget_ids),
            GuestUser.phone.isnot(None),
            ChatSession.channel == SessionChannel.WHATSAPP.value,
        )
    )
    if min_sessions > 1:
        query = query.filter(GuestUser.total_sessions >= min_sessions)
    if last_seen_after:
        query = query.filter(GuestUser.last_seen_at >= last_seen_after)

    guests = query.distinct().all()

    imported = 0
    for guest in guests:
        normalized = normalize_phone(guest.phone)
        if not normalized:
            continue
        existing = (
            db.query(WhatsAppContact)
            .filter(
                WhatsAppContact.business_id == business_id,
                WhatsAppContact.phone_e164 == normalized,
            )
            .first()
        )
        if existing:
            continue
        contact = WhatsAppContact(
            business_id=business_id,
            phone_e164=normalized,
            name=guest.name,
            source=ContactSource.GUEST_IMPORT.value,
            opted_in=True,
        )
        db.add(contact)
        imported += 1

    db.commit()
    return imported


def create_list(
    db: Session, business_id: str, *, name: str, description: str | None = None
) -> WhatsAppContactList:
    lst = WhatsAppContactList(
        business_id=business_id, name=name, description=description
    )
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return lst


def add_members(
    db: Session, contact_list: WhatsAppContactList, contact_ids: list[str]
) -> int:
    existing_ids = {
        m.contact_id
        for m in db.query(WhatsAppContactListMember)
        .filter(WhatsAppContactListMember.contact_list_id == contact_list.id)
        .all()
    }
    added = 0
    valid_contacts = (
        db.query(WhatsAppContact.id)
        .filter(
            WhatsAppContact.id.in_(contact_ids),
            WhatsAppContact.business_id == contact_list.business_id,
        )
        .all()
    )
    for (cid,) in valid_contacts:
        if cid in existing_ids:
            continue
        db.add(
            WhatsAppContactListMember(
                contact_list_id=contact_list.id, contact_id=cid
            )
        )
        added += 1
    db.commit()
    return added


def remove_members(
    db: Session, contact_list: WhatsAppContactList, contact_ids: list[str]
) -> int:
    deleted = (
        db.query(WhatsAppContactListMember)
        .filter(
            WhatsAppContactListMember.contact_list_id == contact_list.id,
            WhatsAppContactListMember.contact_id.in_(contact_ids),
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted
