from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.response_wrapper import success_response
from app.models.escalation import Escalation, EscalationStatus
from app.models.widget import GuestMessage
from app.api.business import get_business

router = APIRouter()

@router.get("/", response_model=None)
async def get_escalations(business_id: str, db: Session = Depends(get_db)):
    """List escalations for a business."""
    # Security note: In production, verify current_user owns business_id
    escalations = db.query(Escalation).filter(Escalation.business_id == business_id).order_by(Escalation.created_at.desc()).all()
    
    results = []
    for esc in escalations:
        results.append({
            "id": esc.id,
            "business_id": esc.business_id,
            "session_id": esc.session_id,
            "status": esc.status,
            "summary": esc.summary,
            "sentiment": esc.sentiment,
            "created_at": esc.created_at.isoformat() if esc.created_at else ""
        })
    return success_response(data=results)

@router.get("/{escalation_id}", response_model=None)
async def get_escalation_details(escalation_id: str, db: Session = Depends(get_db)):
    """Get details of a specific escalation including conversation thread."""
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # Fetch messages for the session
    messages = db.query(GuestMessage).filter(GuestMessage.session_id == esc.session_id).order_by(GuestMessage.created_at.asc()).all()
    
    message_data = []
    for msg in messages:
        message_data.append({
            "id": msg.id,
            "sender": msg.sender, # 'user' or 'agent'
            "message": msg.message_text,
            "created_at": msg.created_at.isoformat() if msg.created_at else ""
        })
        
    # Fetch guest details from the session
    guest = esc.session.guest
    guest_data = {
        "name": guest.name if guest else "Unknown",
        "email": guest.email if guest else None,
        "phone": guest.phone if guest else None,
        "location": f"{esc.session.city}, {esc.session.country}" if esc.session.city and esc.session.country else "Unknown"
    }

    result = {
        "id": esc.id,
        "business_id": esc.business_id,
        "session_id": esc.session_id,
        "status": esc.status,
        "summary": esc.summary,
        "sentiment": esc.sentiment,
        "top_intent": esc.session.top_intent,
        "created_at": esc.created_at.isoformat() if esc.created_at else "",
        "guest": guest_data,
        "messages": message_data
    }
    
    return success_response(data=result)

@router.post("/{escalation_id}/resolve", response_model=None)
async def resolve_escalation(escalation_id: str, db: Session = Depends(get_db)):
    """Mark an escalation as resolved."""
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    esc.status = EscalationStatus.RESOLVED.value
    db.commit()
    db.refresh(esc)
    
    return success_response(message="Escalation resolved", data={"status": esc.status})
