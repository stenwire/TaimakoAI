import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.router import get_current_user
from app.core.response_wrapper import success_response
from app.db.session import get_db
from app.models.business import Business
from app.models.user import User
from app.models.whatsapp_broadcast import TemplateStatus, WhatsAppTemplate
from app.schemas.whatsapp import (
    TemplateCreateRequest,
    TemplateResponse,
    TemplateUpdateRequest,
)
from app.services.whatsapp import templates as template_service
from app.services.whatsapp.client import WhatsAppAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


def _meta_user_message(err: WhatsAppAPIError) -> str:
    """Extract Meta's human-readable error, falling back to generic text."""
    body = err.body if isinstance(err.body, dict) else {}
    meta_error = body.get("error") if isinstance(body.get("error"), dict) else {}
    return (
        meta_error.get("error_user_msg")
        or meta_error.get("error_user_title")
        or meta_error.get("message")
        or f"Meta rejected the request (status {err.status_code})"
    )


def _get_business_or_404(db: Session, user: User) -> Business:
    business = db.query(Business).filter(Business.user_id == user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return business


@router.get("/templates", response_model=None)
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    rows = (
        db.query(WhatsAppTemplate)
        .filter(WhatsAppTemplate.business_id == business.id)
        .order_by(WhatsAppTemplate.created_at.desc())
        .all()
    )
    data = [TemplateResponse.model_validate(r).model_dump(mode="json") for r in rows]
    return success_response(data=data)


@router.post("/templates", response_model=None)
async def create_template(
    payload: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    try:
        template = template_service.create_draft(
            db,
            business.id,
            name=payload.name,
            category=payload.category,
            language=payload.language,
            body_text=payload.body_text,
            header=payload.header,
            footer=payload.footer,
            buttons=payload.buttons,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return success_response(
        message="Template draft created",
        data=TemplateResponse.model_validate(template).model_dump(mode="json"),
    )


@router.get("/templates/{template_id}", response_model=None)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return success_response(
        data=TemplateResponse.model_validate(template).model_dump(mode="json")
    )


@router.patch("/templates/{template_id}", response_model=None)
async def update_template(
    template_id: str,
    payload: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        template = template_service.update_draft(
            db,
            template,
            name=payload.name,
            category=payload.category,
            language=payload.language,
            body_text=payload.body_text,
            header=payload.header,
            footer=payload.footer,
            buttons=payload.buttons,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return success_response(
        message="Template updated",
        data=TemplateResponse.model_validate(template).model_dump(mode="json"),
    )


@router.post("/templates/{template_id}/submit", response_model=None)
async def submit_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.status != TemplateStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Template is already in status {template.status}",
        )
    try:
        template = await template_service.submit_to_meta(db, template)
    except WhatsAppAPIError as e:
        logger.exception("Meta rejected template submission (status=%s body=%s)", e.status_code, e.body)
        raise HTTPException(status_code=502, detail=_meta_user_message(e))
    except Exception as e:
        logger.exception("Unexpected error submitting template to Meta")
        raise HTTPException(status_code=502, detail=f"Meta API error: {e}")
    return success_response(
        message="Template submitted to Meta",
        data=TemplateResponse.model_validate(template).model_dump(mode="json"),
    )


@router.post("/templates/import", response_model=None)
async def import_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    try:
        imported = await template_service.import_from_meta(db, business.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WhatsAppAPIError as e:
        logger.exception("Meta rejected template import (status=%s body=%s)", e.status_code, e.body)
        raise HTTPException(status_code=502, detail=_meta_user_message(e))
    except Exception as e:
        logger.exception("Unexpected error importing templates from Meta")
        raise HTTPException(status_code=502, detail=f"Meta API error: {e}")
    data = [TemplateResponse.model_validate(t).model_dump(mode="json") for t in imported]
    return success_response(
        message=f"Imported {len(imported)} approved template(s)", data=data
    )


@router.delete("/templates/{template_id}", response_model=None)
async def delete_template_endpoint(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business_or_404(db, current_user)
    template = (
        db.query(WhatsAppTemplate)
        .filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.business_id == business.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await template_service.delete_template(db, template)
    return success_response(message="Template deleted")
