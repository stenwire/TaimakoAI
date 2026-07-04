from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.router import get_current_user
from app.core.response_wrapper import success_response
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.models.whatsapp_broadcast import (
    WhatsAppCampaign,
    WhatsAppCampaignMessage,
)
from app.schemas.whatsapp import (
    CampaignCreateRequest,
    CampaignMessageResponse,
    CampaignResponse,
    CampaignSendRequest,
)
from app.services.whatsapp import campaigns as campaign_service

router = APIRouter()


def _get_business_or_404(db: Session, user: User) -> Business:
    business = db.query(Business).filter(Business.user_id == user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return business


def _serialize_campaign(campaign: WhatsAppCampaign) -> dict:
    return CampaignResponse.model_validate(campaign).model_dump(mode="json")


@router.get("/campaigns", response_model=None)
async def list_campaigns(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    query = db.query(WhatsAppCampaign).filter(WhatsAppCampaign.business_id == business.id)
    if status:
        query = query.filter(WhatsAppCampaign.status == status)
    total = query.count()
    rows = (
        query.order_by(WhatsAppCampaign.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    data = {
        "items": [_serialize_campaign(c) for c in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    return success_response(data=data)


@router.post("/campaigns", response_model=None)
async def create_campaign(
    payload: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    try:
        campaign = campaign_service.create_campaign(
            db,
            business.id,
            name=payload.name,
            template_id=payload.template_id,
            audience_type=payload.audience_type,
            audience_ref=payload.audience_ref,
            variable_mapping=payload.variable_mapping,
            created_by_user_id=current_user.id,
            scheduled_at=payload.scheduled_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if payload.send_now or payload.scheduled_at:
        campaign = campaign_service.schedule_campaign(db, campaign, payload.scheduled_at)

    return success_response(
        message="Campaign created", data=_serialize_campaign(campaign)
    )


@router.get("/campaigns/{campaign_id}", response_model=None)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    campaign = (
        db.query(WhatsAppCampaign)
        .filter(
            WhatsAppCampaign.id == campaign_id,
            WhatsAppCampaign.business_id == business.id,
        )
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return success_response(data=_serialize_campaign(campaign))


@router.get("/campaigns/{campaign_id}/messages", response_model=None)
async def list_campaign_messages(
    campaign_id: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    campaign = (
        db.query(WhatsAppCampaign)
        .filter(
            WhatsAppCampaign.id == campaign_id,
            WhatsAppCampaign.business_id == business.id,
        )
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    query = db.query(WhatsAppCampaignMessage).filter(
        WhatsAppCampaignMessage.campaign_id == campaign.id
    )
    if status:
        query = query.filter(WhatsAppCampaignMessage.status == status)
    total = query.count()
    rows = (
        query.order_by(WhatsAppCampaignMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    data = {
        "items": [CampaignMessageResponse.model_validate(r).model_dump(mode="json") for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    return success_response(data=data)


@router.post("/campaigns/{campaign_id}/send", response_model=None)
async def send_campaign(
    campaign_id: str,
    payload: CampaignSendRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    campaign = (
        db.query(WhatsAppCampaign)
        .filter(
            WhatsAppCampaign.id == campaign_id,
            WhatsAppCampaign.business_id == business.id,
        )
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    scheduled_at = payload.scheduled_at if payload else None
    if scheduled_at is None:
        scheduled_at = datetime.now(timezone.utc)
    try:
        campaign = campaign_service.schedule_campaign(db, campaign, scheduled_at)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return success_response(message="Campaign scheduled", data=_serialize_campaign(campaign))


@router.post("/campaigns/{campaign_id}/cancel", response_model=None)
async def cancel_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    campaign = (
        db.query(WhatsAppCampaign)
        .filter(
            WhatsAppCampaign.id == campaign_id,
            WhatsAppCampaign.business_id == business.id,
        )
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    try:
        campaign = campaign_service.cancel_campaign(db, campaign)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return success_response(message="Campaign cancelled", data=_serialize_campaign(campaign))
