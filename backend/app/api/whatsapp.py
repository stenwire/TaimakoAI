import traceback
from fastapi import APIRouter, Request, Response, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.models.widget import WidgetSettings, GuestUser
from app.models.chat_session import ChatSession, SessionChannel
from app.models.user import User
from app.models.business import Business
from app.core.config import settings
from app.services.whatsapp_service import send_whatsapp_message, verify_webhook_signature

router = APIRouter()


@router.get("/webhook")
async def whatsapp_verify(request: Request):
    """Meta webhook verification challenge."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def whatsapp_incoming(request: Request):
    """Handle incoming WhatsApp messages from Meta Cloud API."""
    body = await request.body()

    # Verify signature if app secret is configured
    if settings.WHATSAPP_APP_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(body, signature, settings.WHATSAPP_APP_SECRET):
            print(f"WhatsApp webhook signature verification failed")
            return Response(status_code=200)

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=200)

    # Extract message data from Meta webhook payload
    entry = payload.get("entry", [])
    if not entry:
        return Response(status_code=200)

    changes = entry[0].get("changes", [])
    if not changes:
        return Response(status_code=200)

    value = changes[0].get("value", {})
    messages = value.get("messages")
    if not messages:
        # Status update or other non-message webhook — ignore
        return Response(status_code=200)

    message = messages[0]
    from_phone = message.get("from")
    phone_number_id = value.get("metadata", {}).get("phone_number_id")

    if not from_phone or not phone_number_id:
        return Response(status_code=200)

    print(f"WhatsApp incoming: from={from_phone}, phone_number_id={phone_number_id}, type={message.get('type')}")

    message_text = message.get("text", {}).get("body", "") if message.get("type") == "text" else None

    # Process message with database session
    db = next(get_db())
    try:
        if not message_text:
            # Non-text message — send unsupported notice
            widget = db.query(WidgetSettings).filter(
                WidgetSettings.whatsapp_phone_number_id == phone_number_id,
                WidgetSettings.whatsapp_enabled == True,
            ).first()
            if widget and widget.whatsapp_access_token:
                await send_whatsapp_message(
                    phone_number_id,
                    widget.whatsapp_access_token,
                    from_phone,
                    "I can only process text messages at this time.",
                )
        else:
            await _process_whatsapp_message(db, phone_number_id, from_phone, message_text)
    except Exception as e:
        print(f"WhatsApp processing error: {e}")
        traceback.print_exc()
    finally:
        db.close()

    return Response(status_code=200)


async def _process_whatsapp_message(
    db: Session,
    phone_number_id: str,
    from_phone: str,
    message_text: str,
):
    """Process an incoming WhatsApp text message."""
    # 1. Find widget by phone_number_id
    widget = db.query(WidgetSettings).filter(
        WidgetSettings.whatsapp_phone_number_id == phone_number_id,
        WidgetSettings.whatsapp_enabled == True,
    ).first()

    if not widget:
        print(f"No widget found for phone_number_id: {phone_number_id}")
        return
    if not widget.whatsapp_access_token:
        print(f"Widget found but no access token configured for phone_number_id: {phone_number_id}")
        return
    print(f"WhatsApp: matched widget {widget.id} for phone_number_id {phone_number_id}")

    # 2. Find or create guest user by phone number
    guest = db.query(GuestUser).filter(
        GuestUser.widget_id == widget.id,
        GuestUser.phone == from_phone,
    ).first()

    if not guest:
        guest = GuestUser(
            widget_id=widget.id,
            name=f"WhatsApp {from_phone}",
            phone=from_phone,
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)

    # 3. Find active WhatsApp session (< 24h) or create new one
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    session = db.query(ChatSession).filter(
        ChatSession.guest_id == guest.id,
        ChatSession.channel == SessionChannel.WHATSAPP.value,
        ChatSession.is_active == True,
        ChatSession.created_at >= cutoff,
    ).order_by(ChatSession.created_at.desc()).first()

    if not session:
        # Check daily session limit
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        sessions_today = db.query(ChatSession).filter(
            ChatSession.guest_id == guest.id,
            ChatSession.created_at >= today_start,
        ).count()

        limit = 50
        user = db.query(User).filter(User.id == widget.user_id).first()
        if user and user.business:
            limit = user.business.allocated_daily_sessions

        if sessions_today >= limit:
            await send_whatsapp_message(
                phone_number_id,
                widget.whatsapp_access_token,
                from_phone,
                "Daily session limit reached. Please try again tomorrow.",
            )
            return

        session = ChatSession(
            guest_id=guest.id,
            origin="auto-start",
            channel=SessionChannel.WHATSAPP.value,
        )
        db.add(session)

        # Update guest stats
        guest.last_seen_at = datetime.now(timezone.utc)
        if guest.total_sessions is None:
            guest.total_sessions = 0
        guest.total_sessions += 1
        if guest.total_sessions > 1:
            guest.is_returning = True

        db.commit()
        db.refresh(session)

    # 4. Process message through existing AI pipeline
    from app.api.widget import process_chat_message

    result = await process_chat_message(db, widget, guest, session.id, message_text)

    # 5. Extract AI response and send via WhatsApp
    ai_text = result.response.message_text
    await send_whatsapp_message(
        phone_number_id,
        widget.whatsapp_access_token,
        from_phone,
        ai_text,
    )
