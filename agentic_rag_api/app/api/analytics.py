from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
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
        return {
            "total_sessions": 0,
            "total_guests": 0,
            "leads_captured": 0,
            "avg_session_duration": 0,
            "returning_guests_percentage": 0
        }

    # Filter sessions by widget -> guest -> session
    # Doing a join: ChatSession -> GuestUser -> WidgetSettings
    query = db.query(ChatSession).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date
    )
    
    total_sessions = query.count()
    
    # Guests
    guests_query = db.query(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        GuestUser.created_at >= start_date # Logic for 'New Visitors' in period? Or Active?
        # Standard: Total Unique Visitors in period (based on session activity or creation?)
        # Let's use Active Visitors (had a session in period)
    )
    # Better: Count distinct Guest IDs in sessions query
    total_guests = query.with_entities(ChatSession.guest_id).distinct().count()

    # Leads (Phone or Email captured)
    # We count Guests with email/phone who had a session in this period
    leads_captured = db.query(GuestUser).join(ChatSession).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        (GuestUser.email.isnot(None) | GuestUser.phone.isnot(None))
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
        GuestUser.is_returning == True
    ).distinct().count()
    
    returning_percentage = 0
    if total_guests > 0:
        returning_percentage = int((returning_guests_count / total_guests) * 100)

    return {
        "total_sessions": total_sessions,
        "total_guests": total_guests,
        "leads_captured": leads_captured,
        "avg_session_duration": int(avg_duration),
        "returning_guests_percentage": returning_percentage
    }

@router.get("/intents")
def get_top_intents(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return []

    # Group by top_intent, no limit as requested
    results = db.query(
        ChatSession.top_intent, func.count(ChatSession.id)
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        ChatSession.top_intent.isnot(None)
    ).group_by(ChatSession.top_intent).order_by(func.count(ChatSession.id).desc()).all()
    
    return [{"intent": r[0], "count": r[1]} for r in results]

@router.get("/locations")
def get_top_locations(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return []

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
    
    return [{"country": r[0], "city": r[1] or "Unknown", "count": r[2]} for r in results]

@router.get("/sources")
def get_traffic_sources(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return []

    # Count distinct guests per referrer (User asked for per-user basis)
    results = db.query(
        ChatSession.referrer, func.count(func.distinct(ChatSession.guest_id))
    ).join(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        ChatSession.created_at >= start_date,
        ChatSession.referrer.isnot(None)
    ).group_by(ChatSession.referrer).order_by(func.count(func.distinct(ChatSession.guest_id)).desc()).all()
    
    return [{"source": r[0], "count": r[1]} for r in results]

class FollowUpRequest(BaseModel):
    session_id: str
    type: str # "email" or "transcript"
    extra_info: Optional[str] = ""

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
    
    content = await generate_followup_content(messages, request.type, request.extra_info)
    
    return success_response(data={"content": content})
