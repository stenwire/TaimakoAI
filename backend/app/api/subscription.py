from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.core.config import settings
from app.core.response_wrapper import success_response
from app.services.subscription.factory import SubscriptionServiceFactory
from app.core.subscription import TIER_LIMITS
from datetime import datetime, timezone

class SubscriptionInitRequest(BaseModel):
    tier: str # spark, flux, nexus
    provider: Optional[str] = "paystack"

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/subscription/initialize", response_model=None)
def initialize_subscription(
    req: SubscriptionInitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize a subscription payment transaction.
    """
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    # Validate Tier
    if req.tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail="Invalid Subscription Tier")
        
    # Get Service
    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Init
    # We pass the plan code. In reality, we need to map Tier -> Provider Plan Code.
    # For now, let's assume the frontend passes the simpler Tier name, and we map it (or use env vars).
    # Since we don't have real plan codes yet, we will use a placeholder or assume the tier name matches if created on Paystack.
    # TODO: Map req.tier to Paystack Plan Code via Config.
    # e.g., settings.PAYSTACK_PLAN_MAP = {"spark": "PLN_xxx", ...}
    
    # Using a fake map for now or the tier name if creating dynamic? No, plans must exist.
    # Using 'PLN_xxx' placeholder logic or relying on metadata.
    plan_code = f"PLN_{req.tier.upper()}" # Placeholder
    
    callback_url = f"{settings.FRONTEND_URI}/settings/subscription"
    
    try:
        data = service.initialize_subscription(
            email=current_user.email,
            plan_code=plan_code,
            callback_url=callback_url,
            metadata={
                "business_id": business.id,
                "tier": req.tier
            }
        )
        return success_response(data=data)
    except Exception as e:
        logger.error(f"Subscription Init Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize subscription")


from app.models.payment import PaymentTransaction

@router.post("/webhooks/{provider}")
async def subscription_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle webhooks from payment providers.
    Uses idempotency check and atomic transactions.
    """
    try:
        service = SubscriptionServiceFactory.get_service(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not supported")
        
    # Verify Signature
    body = await request.body()
    headers = dict(request.headers)
    
    if not service.verify_webhook_signature(headers, body):
        logger.warning(f"Invalid Webhook Signature from {provider}")
        raise HTTPException(status_code=401, detail="Invalid Signature")
        
    payload = await request.json()
    event = service.parse_webhook_event(payload)
    
    logger.info(f"Received Webhook Event: {event['event_type']} from {provider}")
    
    # Idempotency Check
    reference = event.get("reference")
    if reference:
        existing_tx = db.query(PaymentTransaction).filter(PaymentTransaction.reference == reference).first()
        if existing_tx:
            logger.info(f"Duplicate Webhook Reference: {reference}. Skipping.")
            return success_response(message="Duplicate Event Processed")
    
    try:
        # Transactional Logic
        with db.begin():
            # 1. Process Event Logic (Update Business)
            business_id = None
            if event["event_type"] in ["RENEWAL_SUCCESS", "SUBSCRIPTION_CREATED"]:
                business = process_renewal_logic(db, event["customer_email"], event)
                if business:
                    business_id = business.id
            elif event["event_type"] == "SUBSCRIPTION_CANCELLED":
                business = process_cancellation_logic(db, event["customer_email"])
                if business:
                    business_id = business.id
            
            # 2. Log Transaction if meaningful
            if reference and business_id:
                tx = PaymentTransaction(
                    business_id=business_id,
                    amount=int(event.get("amount") or 0),
                    currency="NGN", # Default or extract from event
                    status="success",
                    reference=reference,
                    provider=provider,
                    transaction_type=event["event_type"],
                    transaction_metadata=event.get("raw_payload")
                )
                db.add(tx)
                
        # Commit happens automatically if block exits without error
        return success_response(message="Webhook Processed Successfully")

    except Exception as e:
        logger.error(f"Webhook Processing Failed: {e}")
        raise HTTPException(status_code=500, detail="Processing Error")


def process_renewal_logic(db: Session, email: str, event: Dict[str, Any]) -> Optional[Business]:
    # Find business
    customer_code = event.get("customer_code")
    user = db.query(User).filter(User.email == email).first()
    business = None
    
    if user and user.business:
        business = user.business
    elif customer_code:
        business = db.query(Business).filter(Business.payment_customer_id == customer_code).first()
    
    if not business:
        logger.error(f"Webhook: Business not found for {email} / {customer_code}")
        return None
        
    # Update Subscription Info
    if customer_code:
        business.payment_customer_id = customer_code
    if event.get("subscription_code"):
        business.payment_subscription_id = event.get("subscription_code")
        
    business.subscription_status = "active"
    
    # Refill Credits
    tier = business.subscription_tier or "spark"
    limit = TIER_LIMITS.get(tier, {}).get("monthly_credits", 100)
    
    business.credits_balance = limit
    business.credits_last_refilled = datetime.now(timezone.utc)
    business.total_escalations_used = 0
    
    db.add(business) # Ensure session tracks it
    return business

def process_cancellation_logic(db: Session, email: str) -> Optional[Business]:
    user = db.query(User).filter(User.email == email).first()
    if user and user.business:
        user.business.subscription_status = "cancelled"
        db.add(user.business)
        return user.business
    return None
