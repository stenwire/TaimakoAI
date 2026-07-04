from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.auth.router import get_current_user
from app.core.response_wrapper import success_response
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.models.whatsapp_broadcast import (
    WhatsAppContact,
    WhatsAppContactList,
    WhatsAppContactListMember,
)
from app.schemas.whatsapp import (
    ContactCreateRequest,
    ContactCsvImportResponse,
    ContactListCreateRequest,
    ContactListMembersRequest,
    ContactListResponse,
    ContactListUpdateRequest,
    ContactResponse,
    ContactUpdateRequest,
    GuestImportRequest,
    GuestImportResponse,
)
from app.services.whatsapp import contacts as contact_service

router = APIRouter()


def _get_business_or_404(db: Session, user: User) -> Business:
    business = db.query(Business).filter(Business.user_id == user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return business


# ---------- Contacts ----------


@router.get("/contacts", response_model=None)
async def list_contacts(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    query = db.query(WhatsAppContact).filter(WhatsAppContact.business_id == business.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (WhatsAppContact.phone_e164.ilike(like))
            | (WhatsAppContact.name.ilike(like))
        )
    total = query.count()
    rows = (
        query.order_by(WhatsAppContact.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    data = {
        "items": [ContactResponse.model_validate(r).model_dump(mode="json") for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    return success_response(data=data)


@router.post("/contacts", response_model=None)
async def create_contact(
    payload: ContactCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    try:
        contact = contact_service.create_contact(
            db,
            business.id,
            phone=payload.phone,
            name=payload.name,
            tags=payload.tags,
            opted_in=payload.opted_in,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return success_response(
        message="Contact saved",
        data=ContactResponse.model_validate(contact).model_dump(mode="json"),
    )


@router.patch("/contacts/{contact_id}", response_model=None)
async def update_contact(
    contact_id: str,
    payload: ContactUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    contact = (
        db.query(WhatsAppContact)
        .filter(
            WhatsAppContact.id == contact_id,
            WhatsAppContact.business_id == business.id,
        )
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if payload.name is not None:
        contact.name = payload.name
    if payload.tags is not None:
        contact.tags = payload.tags
    if payload.opted_in is not None:
        contact.opted_in = payload.opted_in
    db.commit()
    db.refresh(contact)
    return success_response(
        data=ContactResponse.model_validate(contact).model_dump(mode="json")
    )


@router.delete("/contacts/{contact_id}", response_model=None)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    contact = (
        db.query(WhatsAppContact)
        .filter(
            WhatsAppContact.id == contact_id,
            WhatsAppContact.business_id == business.id,
        )
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return success_response(message="Contact deleted")


@router.post("/contacts/csv", response_model=None)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    content = await file.read()
    result = contact_service.import_csv(db, business.id, content)
    return success_response(
        message=f"Imported {result.imported}, skipped {result.skipped}",
        data=ContactCsvImportResponse(
            imported=result.imported, skipped=result.skipped, errors=result.errors
        ).model_dump(mode="json"),
    )


@router.post("/contacts/import-guests", response_model=None)
async def import_guests(
    payload: GuestImportRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    payload = payload or GuestImportRequest()
    count = contact_service.import_from_guests(
        db,
        business.id,
        min_sessions=payload.min_sessions,
        last_seen_after=payload.last_seen_after,
    )
    return success_response(
        message=f"Imported {count} contacts from WhatsApp chats",
        data=GuestImportResponse(imported=count).model_dump(mode="json"),
    )


# ---------- Contact Lists ----------


def _serialize_list(db: Session, lst: WhatsAppContactList) -> dict:
    member_count = (
        db.query(WhatsAppContactListMember)
        .filter(WhatsAppContactListMember.contact_list_id == lst.id)
        .count()
    )
    base = ContactListResponse.model_validate(lst).model_dump(mode="json")
    base["member_count"] = member_count
    return base


@router.get("/contact-lists", response_model=None)
async def list_contact_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    rows = (
        db.query(WhatsAppContactList)
        .filter(WhatsAppContactList.business_id == business.id)
        .order_by(WhatsAppContactList.created_at.desc())
        .all()
    )
    data = [_serialize_list(db, r) for r in rows]
    return success_response(data=data)


@router.post("/contact-lists", response_model=None)
async def create_contact_list(
    payload: ContactListCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    lst = contact_service.create_list(
        db, business.id, name=payload.name, description=payload.description
    )
    return success_response(
        message="Contact list created", data=_serialize_list(db, lst)
    )


@router.patch("/contact-lists/{list_id}", response_model=None)
async def update_contact_list(
    list_id: str,
    payload: ContactListUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    lst = (
        db.query(WhatsAppContactList)
        .filter(
            WhatsAppContactList.id == list_id,
            WhatsAppContactList.business_id == business.id,
        )
        .first()
    )
    if not lst:
        raise HTTPException(status_code=404, detail="Contact list not found")
    if payload.name is not None:
        lst.name = payload.name
    if payload.description is not None:
        lst.description = payload.description
    db.commit()
    db.refresh(lst)
    return success_response(data=_serialize_list(db, lst))


@router.delete("/contact-lists/{list_id}", response_model=None)
async def delete_contact_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    lst = (
        db.query(WhatsAppContactList)
        .filter(
            WhatsAppContactList.id == list_id,
            WhatsAppContactList.business_id == business.id,
        )
        .first()
    )
    if not lst:
        raise HTTPException(status_code=404, detail="Contact list not found")
    db.delete(lst)
    db.commit()
    return success_response(message="Contact list deleted")


@router.post("/contact-lists/{list_id}/members", response_model=None)
async def add_list_members(
    list_id: str,
    payload: ContactListMembersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    lst = (
        db.query(WhatsAppContactList)
        .filter(
            WhatsAppContactList.id == list_id,
            WhatsAppContactList.business_id == business.id,
        )
        .first()
    )
    if not lst:
        raise HTTPException(status_code=404, detail="Contact list not found")
    added = contact_service.add_members(db, lst, payload.contact_ids)
    return success_response(message=f"Added {added} member(s)", data=_serialize_list(db, lst))


@router.delete("/contact-lists/{list_id}/members", response_model=None)
async def remove_list_members(
    list_id: str,
    payload: ContactListMembersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    lst = (
        db.query(WhatsAppContactList)
        .filter(
            WhatsAppContactList.id == list_id,
            WhatsAppContactList.business_id == business.id,
        )
        .first()
    )
    if not lst:
        raise HTTPException(status_code=404, detail="Contact list not found")
    removed = contact_service.remove_members(db, lst, payload.contact_ids)
    return success_response(message=f"Removed {removed} member(s)", data=_serialize_list(db, lst))
