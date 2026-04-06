from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.chat_session import ChatSession
from app.models.widget import GuestUser, WidgetSettings
from app.models.user import User
from app.auth.router import get_current_user
from pydantic import BaseModel
from app.services.analysis_agent import generate_followup_content
from app.models.widget import GuestMessage
from app.core.response_wrapper import success_response

router = APIRouter()

@router.get("/overview")
def get_analytics_overview(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine date range
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get user's widget (assuming 1 widget per user for now)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data={
            "total_sessions": 0,
            "total_guests": 0,
            "leads_captured": 0,
            "avg_session_duration": 0,
            "returning_guests_percentage": 0
        })

    # Filter sessions by widget -> guest -> session
    # Doing a join: ChatSession -> GuestUser -> WidgetSettings
    query = db.query(ChatSession).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date
    )
    
    total_sessions = query.count()
    
    # Better: Count distinct Guest IDs in sessions query
    total_guests = query.with_entities(ChatSession.guest_id).distinct().count()

    # Leads (marked manually as leads)
    leads_captured = db.query(GuestUser).join(ChatSession).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        GuestUser.is_lead.is_(True)
    ).distinct().count()
    
    # Avg Duration
    avg_duration = query.with_entities(func.avg(ChatSession.session_duration)).scalar() or 0
    
    # Returning Guests %
    # (Returning Guests in period / Total Guests in period) * 100
    # Identifying returning in period: Guests whose 'is_returning' is True? 
    # Or guests who had > 1 session total?
    # Simple metric: Count sessions where is_returning=True? No, is_returning is on Guest.
    # Let's count guests in period who have is_returning=True.
    returning_guests_count = db.query(GuestUser).join(ChatSession).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        GuestUser.is_returning.is_(True)
    ).distinct().count()
    
    returning_percentage = 0
    if total_guests > 0:
        returning_percentage = int((returning_guests_count / total_guests) * 100)

    return success_response(data={
        "total_sessions": total_sessions,
        "total_guests": total_guests,
        "leads_captured": leads_captured,
        "avg_session_duration": int(avg_duration),
        "returning_guests_percentage": returning_percentage
    })

@router.get("/intents")
def get_top_intents(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])

    # Group by top_intent, no limit as requested
    results = db.query(
        ChatSession.top_intent, func.count(ChatSession.id)
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        ChatSession.top_intent.isnot(None)
    ).group_by(ChatSession.top_intent).order_by(func.count(ChatSession.id).desc()).all()
    
    return success_response(data=[{"intent": r[0], "count": r[1]} for r in results])

@router.get("/locations")
def get_top_locations(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])

    # Group by City, Country
    # Prefer City if available, else Country?
    # Let's return list of {country, city, count}
    results = db.query(
        ChatSession.country, ChatSession.city, func.count(ChatSession.id)
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        ChatSession.country.isnot(None)
    ).group_by(ChatSession.country, ChatSession.city).order_by(func.count(ChatSession.id).desc()).limit(10).all()
    
    return success_response(data=[{"country": r[0], "city": r[1] or "Unknown", "count": r[2]} for r in results])

@router.get("/sources")
def get_traffic_sources(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])

    # Count distinct guests per referrer (User asked for per-user basis)
    results = db.query(
        ChatSession.referrer, func.count(func.distinct(ChatSession.guest_id))
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        ChatSession.referrer.isnot(None)
    ).group_by(ChatSession.referrer).order_by(func.count(func.distinct(ChatSession.guest_id)).desc()).all()
    
    return success_response(data=[{"source": r[0], "count": r[1]} for r in results])

@router.get("/trend")
def get_traffic_trend(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])

    # Daily session counts
    # Using func.date for SQLite compatibility (and Postgres sometimes)
    # If using Postgres, might need cast to Date.
    # Assuming standard SQLAlchemy usage.
    results = db.query(
        func.date(ChatSession.created_at).label('date'), func.count(ChatSession.id)
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date
    ).group_by(func.date(ChatSession.created_at)).order_by(func.date(ChatSession.created_at)).all()
    
    return success_response(data=[{"date": str(r[0]), "count": r[1]} for r in results])

class FollowUpRequest(BaseModel):
    session_id: str
    type: str # "email" or "transcript"
    extra_info: Optional[str] = ""

from app.core.config import settings as app_settings

@router.post("/followup", response_model=None)
async def generate_followup(
    request: FollowUpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user's widget
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    session = db.query(ChatSession).join(GuestUser).filter(
        ChatSession.id == request.session_id,
        GuestUser.widget_id == widget.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(GuestMessage).filter(GuestMessage.session_id == request.session_id).order_by(GuestMessage.created_at).all()

    content = await generate_followup_content(messages, request.type, request.extra_info, api_key=app_settings.GOOGLE_API_KEY)

    return success_response(data={"content": content})

@router.get("/sessions")
def get_recent_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])

    # Get recent sessions
    sessions = db.query(ChatSession).join(GuestUser).filter(
        GuestUser.widget_id == widget.id
    ).order_by(ChatSession.created_at.desc()).offset(offset).limit(limit).all()

    # Enhance with guest info
    result = []
    for s in sessions:
        guest = db.query(GuestUser).filter(GuestUser.id == s.guest_id).first()
        result.append({
            "id": s.id,
            "guest_name": guest.name if guest else "Anonymous",
            "guest_email": guest.email,
            "created_at": s.created_at,
            "session_duration": s.session_duration,
            "top_intent": s.top_intent,
            "summary": s.summary,
            "status": "closed" if s.summary else "active" # Simple logic
        })
    
    return success_response(data=result)

@router.get("/sessions/{session_id}")
def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    session = db.query(ChatSession).join(GuestUser).filter(
        ChatSession.id == session_id,
        GuestUser.widget_id == widget.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    guest = db.query(GuestUser).filter(GuestUser.id == session.guest_id).first()
    messages = db.query(GuestMessage).filter(GuestMessage.session_id == session_id).order_by(GuestMessage.created_at).all()
    
    return success_response(data={
        "id": session.id,
        "guest": {
            "id": guest.id,
            "name": guest.name,
            "email": guest.email,
            "location": f"{session.city}, {session.country}" if session.city else session.country
        },
        "created_at": session.created_at,
        "top_intent": session.top_intent,
        "summary": session.summary,
        "sentiment_score": session.sentiment_score,
        "messages": [
            {
                "id": m.id,
                "role": "user" if m.sender == "guest" else "ai",
                "content": m.message_text,
                "created_at": m.created_at
            }
            for m in messages
        ]
    })
