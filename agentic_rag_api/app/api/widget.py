from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.widget import WidgetSettings, GuestUser, GuestMessage
from app.models.user import User
from app.models.business import Business
from app.schemas.widget import (
    GuestStartRequest, GuestStartResponse,
    WidgetChatRequest, WidgetChatResponse, GuestMessageSchema,
    WidgetConfigResponse, GuestUserResponse
)
from app.services.agent_service import run_conversation
from app.auth.router import get_current_user

# Additional Schema for Updating Settings
from pydantic import BaseModel
class WidgetUpdate(BaseModel):
    theme: Optional[str] = None
    primary_color: Optional[str] = None
    icon_url: Optional[str] = None



router = APIRouter()

@router.get("/config/{public_widget_id}", response_model=WidgetConfigResponse)
def get_widget_config(public_widget_id: str, db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

@router.get("/my-settings", response_model=WidgetConfigResponse)
def get_my_widget_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        # Create default if not exists
        widget = WidgetSettings(user_id=current_user.id)
        db.add(widget)
        db.commit()
        db.refresh(widget)
    return widget

@router.put("/my-settings", response_model=WidgetConfigResponse)
def update_my_widget_settings(
    settings: WidgetUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        widget = WidgetSettings(user_id=current_user.id)
        db.add(widget)
    
    if settings.theme:
        widget.theme = settings.theme
    if settings.primary_color:
        widget.primary_color = settings.primary_color
    if settings.icon_url:
        widget.icon_url = settings.icon_url
        
    db.commit()
    db.refresh(widget)
    db.commit()
    db.refresh(widget)
    return widget

@router.get("/guests", response_model=List[GuestUserResponse])
def get_my_widget_guests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return []
    
    guests = db.query(GuestUser).filter(GuestUser.widget_id == widget.id).order_by(GuestUser.created_at.desc()).all()
    return guests

@router.get("/interactions/{guest_id}", response_model=List[GuestMessageSchema])
def get_guest_interactions(
    guest_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verify ownership
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    guest = db.query(GuestUser).filter(GuestUser.id == guest_id, GuestUser.widget_id == widget.id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest session not found or access denied")
        
    messages = db.query(GuestMessage).filter(GuestMessage.guest_id == guest_id).order_by(GuestMessage.created_at).all()
    return messages

@router.post("/guest/start/{public_widget_id}", response_model=GuestStartResponse)
def start_guest_session(public_widget_id: str, guest_in: GuestStartRequest, db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Determine if we should reuse an existing guest (e.g. by email/phone matching?)
    # For now, let's create a new one every time strictly based on request, or maybe we just create.
    # The requirement says "Create or identify a guest user".
    # Logic: if email is provided, check if exists for this widget.
    
    existing_guest = None
    if guest_in.email:
        existing_guest = db.query(GuestUser).filter(
            GuestUser.widget_id == widget.id, 
            GuestUser.email == guest_in.email
        ).first()
    elif guest_in.phone:
        existing_guest = db.query(GuestUser).filter(
            GuestUser.widget_id == widget.id, 
            GuestUser.phone == guest_in.phone
        ).first()
        
    if existing_guest:
        guest = existing_guest
        # Update name if changed? Let's just keep matching one.
    else:
        guest = GuestUser(
            widget_id=widget.id,
            name=guest_in.name,
            email=guest_in.email,
            phone=guest_in.phone
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)

    return GuestStartResponse(
        guest_id=guest.id,
        widget_owner_id=widget.user_id,
        status="ready"
    )

@router.post("/chat/{public_widget_id}/{guest_id}", response_model=WidgetChatResponse)
async def chat_interaction(
    public_widget_id: str, 
    guest_id: str, 
    chat_in: WidgetChatRequest, 
    db: Session = Depends(get_db)
):
    # Verify widget and guest
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    guest = db.query(GuestUser).filter(GuestUser.id == guest_id, GuestUser.widget_id == widget.id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest session not found")

    # 1. Store guest message
    guest_msg = GuestMessage(
        guest_id=guest.id,
        sender="guest",
        message_text=chat_in.message
    )
    db.add(guest_msg)
    db.commit()
    db.refresh(guest_msg)

    # 2. Get business context
    # widget.user is the owner.
    # We need to fetch the business linked to the user.
    # Using relationship access.
    owner_user = db.query(User).filter(User.id == widget.user_id).first()
    if not owner_user or not owner_user.business:
        # Fallback if no business configured?
        business_name = "Sten"
        instruction = None
    else:
        business_name = owner_user.business.business_name
        instruction = owner_user.business.custom_agent_instruction

    # 3. Call AI
    # user_id passed to run_conversation should be the OWNER ID so tools access owner's data.
    # session_id should be guest_id to maintain guest's thread.
    ai_response_text = await run_conversation(
        message=chat_in.message,
        user_id=widget.user_id,
        business_name=business_name,
        custom_instruction=instruction,
        session_id=guest_id
    )

    # 4. Store AI response
    ai_msg = GuestMessage(
        guest_id=guest.id,
        sender="ai",
        message_text=ai_response_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return WidgetChatResponse(
        message=GuestMessageSchema.model_validate(guest_msg),
        response=GuestMessageSchema.model_validate(ai_msg)
    )

@router.get("/messages/{guest_id}", response_model=List[GuestMessageSchema])
def get_chat_history(guest_id: str, db: Session = Depends(get_db)):
    # Maybe verify guest exists, or just return empty
    messages = db.query(GuestMessage).filter(GuestMessage.guest_id == guest_id).order_by(GuestMessage.created_at).all()
    return messages
