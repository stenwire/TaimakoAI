from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx

from app.db.session import get_db
from app.models.widget import WidgetSettings, GuestUser, GuestMessage
from app.models.user import User
from app.models.business import Business
from app.models.chat_session import ChatSession, SessionOrigin
from app.schemas.widget import (
    GuestStartRequest, GuestStartResponse,
    WidgetChatRequest, WidgetChatResponse, GuestMessageSchema,
    WidgetConfigResponse, GuestUserResponse,
    SessionStartRequest, SessionHistoryResponse
)
from app.services.agent_service import run_conversation
from app.auth.router import get_current_user
from app.core.response_wrapper import success_response

# Additional Schema for Updating Settings
from pydantic import BaseModel
class WidgetUpdate(BaseModel):
    theme: Optional[str] = None
    primary_color: Optional[str] = None
    icon_url: Optional[str] = None
    welcome_message: Optional[str] = None
    initial_ai_message: Optional[str] = None
    initial_ai_message: Optional[str] = None
    send_initial_message_automatically: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    whatsapp_number: Optional[str] = None



router = APIRouter()

@router.get("/config/{public_widget_id}", response_model=WidgetConfigResponse)
def get_widget_config(public_widget_id: str, db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

@router.get("/my-settings", response_model=None)
def get_my_widget_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        # Create default if not exists
        widget = WidgetSettings(user_id=current_user.id)
        db.add(widget)
        db.commit()
        db.refresh(widget)
    return success_response(data=WidgetConfigResponse.model_validate(widget))

@router.put("/my-settings", response_model=None)
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
    if settings.welcome_message is not None:
        val = settings.welcome_message.strip()
        if val == "":
            widget.welcome_message = None
        else:
            if len(val) > 1000:
                raise HTTPException(status_code=400, detail="Welcome message too long")
            widget.welcome_message = val
            
    if settings.initial_ai_message is not None:
        val = settings.initial_ai_message.strip()
        if val == "":
            widget.initial_ai_message = None
        else:
            if len(val) > 1000:
                raise HTTPException(status_code=400, detail="Initial AI message too long")
            widget.initial_ai_message = val

    if settings.send_initial_message_automatically is not None:
        widget.send_initial_message_automatically = settings.send_initial_message_automatically
        
    if settings.whatsapp_enabled is not None:
        widget.whatsapp_enabled = settings.whatsapp_enabled
        
    if settings.whatsapp_number is not None:
        widget.whatsapp_number = settings.whatsapp_number
        
    db.commit()
    db.refresh(widget)
    db.commit()
    db.refresh(widget)
    return success_response(data=WidgetConfigResponse.model_validate(widget))

@router.get("/guests", response_model=None)
def get_my_widget_guests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widget = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
    if not widget:
        return success_response(data=[])
    
    guests = db.query(GuestUser).filter(GuestUser.widget_id == widget.id).order_by(GuestUser.created_at.desc()).all()
    return success_response(data=[GuestUserResponse.model_validate(g) for g in guests])

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

    # Note: We do NOT create a ChatSession here. Session is created on first message.
    # Also, we do NOT send initial AI message here anymore if session logic is used,
    # OR we send it but it's not part of a 'session' until user responds?
    # REQUIREMENT: "A new session_id is created only after the first message is successfully sent."
    # AND: "Guest users should be able to manually start a new chat session... Starting a new session resets the message area."
    
    # If we want an initial AI greeting, it should probably be transient or part of the session start.
    # The requirement says: "No backend call [on manual start]. First user message triggers backend session creation."
    # So `guest/start` is effectively just "Identifying the user".
    # The frontend already uses this to prompt for name/email.
    
    return GuestStartResponse(
        guest_id=guest.id,
        widget_owner_id=widget.user_id,
        status="ready"
    )

# @router.post("/guest/session/init/{public_widget_id}", response_model=WidgetChatResponse)
# async def init_guest_session(
#     public_widget_id: str,
#     session_in: SessionStartRequest,
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """
#     Starts a new chat session for a guest and processes the first message.
#     """
#     widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
#     if not widget:
#         raise HTTPException(status_code=404, detail="Widget not found")
        
#     guest = db.query(GuestUser).filter(GuestUser.id == session_in.guest_id).first()
#     if not guest:
#         # Auto-create guest if ID provided but not found? Or fail?
#         # Usually widget creates guest first. But let's be robust.
#         # Ideally, return 404, but for resilience we could create.
#         # Let's assume Valid Guest ID.
#         raise HTTPException(status_code=404, detail="Guest not found")
        
#     # Create new session
#     session = ChatSession(
#         guest_id=guest.id,
#         origin=session_in.origin
#     )
    
#     # 1. Populate context from Frontend (Device, Referrer, Timezone, simple UTMs)
#     if session_in.context:
#         ctx = session_in.context
#         session.device_type = ctx.device_type
#         session.browser = ctx.browser
#         session.os = ctx.os
#         session.timezone = ctx.timezone
#         session.referrer = ctx.referrer
#         session.utm_source = ctx.utm_source
#         session.utm_medium = ctx.utm_medium
#         session.utm_campaign = ctx.utm_campaign
        
#         # If frontend sent country/city (unlikely yet), use it.
#         session.country = ctx.country
#         session.city = ctx.city

#     # 2. IP Geolocation Fallback
#     # If country is missing, try to resolve via IP
#     if not session.country:
#         try:
#             client_ip = request.client.host
#             # In dev, localhost IP is 127.0.0.1 which resolves to nothing useful.
#             # Only try if not localhost and safe.
#             if client_ip and client_ip not in ["127.0.0.1", "::1"]:
#                 # Using a free, no-key API for demonstration: ip-api.com
#                 # Limit: 45 requests per minute. Fine for prototype/demo.
#                 # Production should use MaxMind GeoIP2 local DB or paid API.
#                 async with httpx.AsyncClient() as client:
#                     resp = await client.get(f"http://ip-api.com/json/{client_ip}", timeout=2.0)
#                     if resp.status_code == 200:
#                         geo = resp.json()
#                         if geo.get("status") == "success":
#                             session.country = geo.get("country")
#                             session.city = geo.get("city")
#                             # If timezone was missing, this is also a good source
#                             if not session.timezone:
#                                 session.timezone = geo.get("timezone")
#         except Exception as e:
#             # log error but don't block session creation
#             print(f"GeoIP Lookup Failed: {e}")

#     db.add(session)
    
#     # Update Guest Stats
#     guest.last_seen_at = datetime.now(timezone.utc)
#     if guest.total_sessions is None:
#         guest.total_sessions = 0
#     guest.total_sessions += 1
    
#     if guest.total_sessions > 1:
#         guest.is_returning = True
        
#     db.commit()
#     db.refresh(session)
    
#     # Process message
#     return await process_chat_message(db, widget, guest, session.id, session_in.message)


@router.post("/guest/session/init/{public_widget_id}", response_model=WidgetChatResponse)
async def init_guest_session(
    public_widget_id: str,
    session_in: SessionStartRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Starts a new chat session for a guest and processes the first message.
    """
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
        
    guest = db.query(GuestUser).filter(GuestUser.id == session_in.guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
        
    # Create new session
    session = ChatSession(
        guest_id=guest.id,
        origin=session_in.origin
    )
    
    # 1. Populate context from Frontend
    if session_in.context:
        ctx = session_in.context
        session.device_type = ctx.device_type
        session.browser = ctx.browser
        session.os = ctx.os
        session.timezone = ctx.timezone
        session.referrer = ctx.referrer
        session.utm_source = ctx.utm_source
        session.utm_medium = ctx.utm_medium
        session.utm_campaign = ctx.utm_campaign
        session.country = ctx.country
        session.city = ctx.city
    
    # 2. IP Geolocation Fallback
    if not session.country:
        try:
            # Get client IP - handle proxies/load balancers
            client_ip = request.client.host if request.client else None
            
            # Check for forwarded IP (if behind proxy/load balancer)
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            
            print(f"Attempting geolocation for IP: {client_ip}")
            
            # Skip localhost IPs
            if client_ip:
                if client_ip in ["127.0.0.1", "::1", "localhost"]:
                    client_ip = "8.8.8.8" # this is purely for testing only
                # Use httpx_client to avoid variable name collision
                async with httpx.AsyncClient() as httpx_client:
                    resp = await httpx_client.get(
                        f"http://ip-api.com/json/{client_ip}",
                        timeout=2.0
                    )
                    
                    if resp.status_code == 200:
                        geo = resp.json()
                        print(f"Geo API response: {geo}")
                        
                        if geo.get("status") == "success":
                            session.country = geo.get("country")
                            session.city = geo.get("city")
                            
                            if not session.timezone:
                                session.timezone = geo.get("timezone")
                            
                            print(f"Geolocation successful: {session.country}, {session.city}")
                        else:
                            print(f"Geo API returned failure: {geo.get('message')}")
            else:
                print(f"Skipping geolocation for localhost IP: {client_ip}")
                
        except httpx.TimeoutException:
            print(f"GeoIP Lookup Timeout")
        except httpx.HTTPError as e:
            print(f"GeoIP HTTP Error: {e}")
        except Exception as e:
            print(f"GeoIP Lookup Failed: {type(e).__name__}: {e}")
    
    db.add(session)
    
    # Update Guest Stats
    guest.last_seen_at = datetime.now(timezone.utc)
    if guest.total_sessions is None:
        guest.total_sessions = 0
    guest.total_sessions += 1
    
    if guest.total_sessions > 1:
        guest.is_returning = True
        
    db.commit()
    db.refresh(session)
    
    # Process message
    return await process_chat_message(db, widget, guest, session.id, session_in.message)

@router.post("/chat/{public_widget_id}/session/{session_id}", response_model=WidgetChatResponse)
async def chat_in_session(
    public_widget_id: str,
    session_id: str,
    chat_in: WidgetChatRequest,
    db: Session = Depends(get_db)
):
    widget = db.query(WidgetSettings).filter(WidgetSettings.public_widget_id == public_widget_id).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
        
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    guest = db.query(GuestUser).filter(GuestUser.id == session.guest_id).first() # Should exist
    
    # Update last_message_at
    session.last_message_at = datetime.now(timezone.utc)
    db.commit()
    
    return await process_chat_message(db, widget, guest, session_id, chat_in.message)


async def process_chat_message(db: Session, widget: WidgetSettings, guest: GuestUser, session_id: str, message_text: str):
    # 1. Store guest message
    guest_msg = GuestMessage(
        guest_id=guest.id,
        session_id=session_id,
        sender="guest",
        message_text=message_text
    )
    db.add(guest_msg)
    db.commit()
    db.refresh(guest_msg)

    # 2. Get business context
    owner_user = db.query(User).filter(User.id == widget.user_id).first()
    if not owner_user or not owner_user.business:
        business_name = "Taimako.AI"
        instruction = None
        intents = None
    else:
        business_name = owner_user.business.business_name
        instruction = owner_user.business.custom_agent_instruction
        intents = owner_user.business.intents

    # 3. Call AI
    ai_response_text = await run_conversation(
        message=message_text,
        user_id=widget.user_id,
        business_name=business_name,
        custom_instruction=instruction,
        session_id=session_id, # Use session_id for thread consistency
        intents=intents
    )

    # 4. Store AI response
    ai_msg = GuestMessage(
        guest_id=guest.id,
        session_id=session_id,
        sender="ai",
        message_text=ai_response_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    # 5. Update Session Stats
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        if session.total_messages is None: session.total_messages = 0
        if session.user_messages is None: session.user_messages = 0
        if session.ai_messages is None: session.ai_messages = 0
        
        session.total_messages += 2 # 1 user + 1 AI
        session.user_messages += 1
        session.ai_messages += 1
        # Calculate duration
        # Ensure session.created_at is aware or naive consistently.
        # DB usually returns naive (implicitly UTC) if not using PostgreSQL with timezone=True explicitly in some configs.
        # But datetime.now(timezone.utc) is aware.
        # Safe strategy: Ensure both are aware.
        
        now_aware = datetime.now(timezone.utc)
        
        if session.created_at:
             created_at = session.created_at
             if created_at.tzinfo is None:
                 created_at = created_at.replace(tzinfo=timezone.utc)
             
             delta = now_aware - created_at
             session.session_duration = int(delta.total_seconds())
        
        # First response time (if not set)
        if session.first_response_time is None:
             # guest_msg.created_at and ai_msg.created_at might be naive or aware.
             # They are freshly created so they might be naive if fetched back from SQLite immediately?
             # Or they are the objects we just added? No, we queried messages or refreshed them.
             
             g_created = guest_msg.created_at
             a_created = ai_msg.created_at
             
             if g_created and a_created:
                 if g_created.tzinfo is None:
                     g_created = g_created.replace(tzinfo=timezone.utc)
                 if a_created.tzinfo is None:
                     a_created = a_created.replace(tzinfo=timezone.utc)
                     
                 frt = a_created - g_created
                 session.first_response_time = int(frt.total_seconds())

        db.commit()

    return WidgetChatResponse(
        message=GuestMessageSchema.model_validate(guest_msg),
        response=GuestMessageSchema.model_validate(ai_msg)
    )

@router.get("/sessions/{guest_id}/history", response_model=None)
def get_guest_session_history(guest_id: str, db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.guest_id == guest_id).order_by(ChatSession.created_at.desc()).all()
    return success_response(data=[SessionHistoryResponse.model_validate(s) for s in sessions])

@router.get("/session/{session_id}/messages", response_model=List[GuestMessageSchema])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(GuestMessage).filter(GuestMessage.session_id == session_id).order_by(GuestMessage.created_at).all()
    return messages

@router.get("/session/{session_id}")
def get_session_details_widget(
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

from app.services.analysis_agent import analyze_session, persist_analysis

@router.post("/session/{session_id}/analyze", response_model=None)
async def analyze_chat_session(session_id: str, db: Session = Depends(get_db)):
    # 1. Verify session exists
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch intents from business if available
    intents = None
    try:
        # ChatSession -> GuestUser -> WidgetSettings -> User -> Business
        guest = db.query(GuestUser).filter(GuestUser.id == session.guest_id).first()
        if guest:
            widget = db.query(WidgetSettings).filter(WidgetSettings.id == guest.widget_id).first()
            if widget:
                owner_user = db.query(User).filter(User.id == widget.user_id).first()
                if owner_user and owner_user.business and owner_user.business.intents:
                    intents = owner_user.business.intents
    except Exception as e:
        print(f"Error fetching intents: {e}")

    # 2. Run analysis
    summary, intent = await analyze_session(db, session_id, intents=intents)
    
    # 3. Persist
    updated_session = await persist_analysis(db, session_id, summary, intent)
    
    if not updated_session:
        raise HTTPException(status_code=500, detail="Failed to persist analysis")
        
    return success_response(data=SessionHistoryResponse.model_validate(updated_session))

# Deprecated or Legacy Support
@router.post("/chat/{public_widget_id}/{guest_id}", response_model=WidgetChatResponse)
async def chat_interaction(
    public_widget_id: str, 
    guest_id: str, 
    chat_in: WidgetChatRequest, 
    db: Session = Depends(get_db)
):
    # This endpoint is deprecated but kept for backward compatibility if needed.
    # It creates a temporary/ad-hoc session if none exists?
    # Or just maps to the new logic with a "default" session?
    # Ideally frontend should switch to /session/init and /session/{id}.
    # Implementing failover: Try to find latest active session or create one.
    
    # For now, let's just forward to init with auto-start if we want to be helpful, 
    # but strictly we should probably error or force frontend update.
    # Given we are updating frontend, we can leave this stub or redirect.
    # Let's implementation basic fallback: Create a session (auto-start) if none provided.
    
    return await init_guest_session(
        public_widget_id=public_widget_id,
        session_in=SessionStartRequest(
            guest_id=guest_id,
            message=chat_in.message,
            origin="auto-start" # Legacy default
        ),
        db=db
    )
