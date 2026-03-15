from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.plan import Plan
from app.models.payment import PaymentTransaction
from app.core.config import settings
from app.core.response_wrapper import success_response
from app.core.subscription import TIER_LIMITS, TIER_HIERARCHY
from app.services.subscription.factory import SubscriptionServiceFactory
from app.utils.email_helpers import (
    send_subscription_created_email,
    send_subscription_cancelled_email,
    send_payment_success_email,
    send_payment_failed_email,
    send_plan_upgraded_email,
)
from datetime import datetime, timezone


# --- Request Schemas ---

class SubscriptionInitRequest(BaseModel):
    plan_id: int
    provider: Optional[str] = "paystack"


class SubscriptionCancelRequest(BaseModel):
    provider: Optional[str] = "paystack"


class SubscriptionUpgradeRequest(BaseModel):
    new_plan_id: int
    provider: Optional[str] = "paystack"


# --- Router & Logger ---

router = APIRouter()
logger = logging.getLogger(__name__)


# --- Helper: get business or 404 ---

def _get_user_business(db: Session, user: User) -> Business:
    business = db.query(Business).filter(Business.user_id == user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/subscription/initialize", response_model=None)
async def initialize_subscription(
    req: SubscriptionInitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize a subscription payment transaction.
    Uses the Plan ID to look up the Paystack plan_code from the local DB.
    """
    business = _get_user_business(db, current_user)

    # Look up plan from DB
    plan = db.query(Plan).filter(Plan.id == req.plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")

    # Get service
    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    callback_url = f"{settings.FRONTEND_URI}/dashboard/settings/subscription"

    try:
        data = service.initialize_subscription(
            email=current_user.email,
            plan_code=plan.plan_code,
            callback_url=callback_url,
            metadata={
                "business_id": business.id,
                "user_id": current_user.id,
                "plan_id": plan.id,
                "tier": plan.name.lower()
            },
            amount=0 # required by paystack, but will be overridden by the plan amount
        )
        print(f"\n\n data: {data}\n\n")
        return success_response(data=data)
    except Exception as e:
        logger.error(f"Subscription Init Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize subscription")


@router.post("/subscription/cancel", response_model=None)
async def cancel_subscription(
    req: SubscriptionCancelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel the current subscription. Sets status to 'non-renewing'.
    The subscription remains active until the end of the billing cycle.
    """
    business = _get_user_business(db, current_user)

    if not business.payment_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    if business.subscription_status in ("cancelled", "non-renewing"):
        raise HTTPException(status_code=400, detail="Subscription is already cancelled or non-renewing")

    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Cancel via provider
    success = service.cancel_subscription(
        subscription_code=business.payment_subscription_id,
        email_token=business.subscription_email_token or ""
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription with payment provider")

    # Update local state
    business.subscription_status = "non-renewing"
    db.commit()

    # Send email notification in background
    background_tasks.add_task(send_subscription_cancelled_email, current_user.email)

    return success_response(message="Subscription cancelled. Access continues until end of billing period.")


@router.post("/subscription/upgrade", response_model=None)
async def upgrade_subscription(
    req: SubscriptionUpgradeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upgrade subscription plan.
    Redirects user to Paystack to initialize a new subscription for the higher tier.
    Webhooks handle the actual swapping and cancelling the old one.
    """
    print(f"\n\nRequest for upgrade: {req}\n\n")
    business = _get_user_business(db, current_user)

    # Validate new plan
    new_plan = db.query(Plan).filter(Plan.id == req.new_plan_id, Plan.is_active == True).first()
    print(f"\n\n New Plan: {new_plan.to_dict()}\n\n")
    if not new_plan:
        raise HTTPException(status_code=404, detail="New plan not found or inactive")

    if not business.payment_customer_id:
        raise HTTPException(status_code=400, detail="Customer profile not found with payment provider")

    old_tier_name = business.subscription_tier or "spark"
    current_plan = db.query(Plan).filter(Plan.name.ilike(old_tier_name)).first()
    print(f"\n\n Plan before upgrade: {current_plan.to_dict()}\n\n")
    old_tier_level = current_plan.tier if current_plan else 0
    new_tier_level = new_plan.tier

    if new_tier_level < old_tier_level:
        raise HTTPException(status_code=400, detail="Downgrades are not allowed")

    new_tier = new_plan.name.lower()

    if old_tier_name.lower() == new_tier:
        logger.info("[UPGRADE/RECHARGE] User is on the same plan. Triggering a recharge/renewal initialization.")
        
    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    callback_url = f"{settings.FRONTEND_URI}/dashboard/settings/subscription"

    try:
        data = service.initialize_subscription(
            email=current_user.email,
            plan_code=new_plan.plan_code,
            callback_url=callback_url,
            metadata={
                "business_id": business.id,
                "user_id": current_user.id,
                "plan_id": new_plan.id,
                "tier": new_tier,
                "is_upgrade": True,
                "old_subscription_id": business.payment_subscription_id,
                "old_email_token": business.subscription_email_token
            },
            amount=0 # required by paystack, but will be overridden by the plan amount
        )
        return success_response(data=data)
    except Exception as e:
        logger.error(f"Subscription Upgrade Failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize upgrade subscription")


class SubscriptionVerifyRequest(BaseModel):
    reference: str
    provider: Optional[str] = "paystack"

@router.post("/subscription/verify", response_model=None)
async def verify_subscription_transaction(
    req: SubscriptionVerifyRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually verify a transaction.
    This acts as a fallback or immediate processor if the webhook is delayed.
    """
    business = _get_user_business(db, current_user)
    reference = req.reference

    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Idempotency Check
    existing_tx = db.query(PaymentTransaction).filter(
        PaymentTransaction.reference == reference
    ).first()
    if existing_tx:
        logger.info(f"[VERIFY] Transaction {reference} already processed.")
        return success_response(message="Transaction already processed")

    # Verify explicitly with provider
    try:
        # verify_transaction should standardize the payload similar to webhook parse
        event = service.verify_transaction(reference)
    except Exception as e:
        logger.error(f"[VERIFY] Verification failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify transaction with provider")

    # If the transaction wasn't a success (could be pending or failed), we still process it
    try:
        if event["event_type"] == "RENEWAL_SUCCESS":
            updated_business = _process_renewal_success(db, event)
            if updated_business:
                background_tasks.add_task(
                    send_payment_success_email,
                    event["customer_email"],
                    updated_business.subscription_tier.capitalize(),
                    int(event.get("amount") or 0)
                )

        elif event["event_type"] == "PAYMENT_FAILED":
            _process_payment_failed(db, event)

        # Record the transaction
        tx = PaymentTransaction(
            business_id=business.id,
            amount=int(event.get("amount") or 0),
            currency="NGN",
            status="success" if event["event_type"] == "RENEWAL_SUCCESS" else "failed",
            reference=reference,
            provider=req.provider,
            transaction_type=event["event_type"],
            transaction_metadata=event.get("raw_payload"),
            raw_webhook_payload=event.get("raw_payload")
        )
        db.add(tx)
        db.commit()
        return success_response(message="Transaction verified successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"[VERIFY] ❌ Verification Processing Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Processing Error")

class SubscriptionEnableRequest(BaseModel):
    provider: Optional[str] = "paystack"

@router.post("/subscription/enable", response_model=None)
async def enable_subscription_endpoint(
    req: SubscriptionEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enable/un-cancel a subscription that is non-renewing.
    For Paystack, we must create a new subscription (initialize a new checkout).
    """
    business = _get_user_business(db, current_user)

    if not business.payment_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    if business.subscription_status != "non-renewing":
        raise HTTPException(status_code=400, detail="Subscription is not in non-renewing state")

    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # We must initialize a new subscription for Paystack
    tier_name = business.subscription_tier or "spark"
    plan = db.query(Plan).filter(Plan.name.ilike(tier_name), Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Current plan not found or inactive")

    callback_url = f"{settings.FRONTEND_URI}/dashboard/settings/subscription"

    try:
        data = service.initialize_subscription(
            email=current_user.email,
            plan_code=plan.plan_code,
            callback_url=callback_url,
            metadata={
                "business_id": business.id,
                "user_id": current_user.id,
                "plan_id": plan.id,
                "tier": plan.name.lower(),
                "is_upgrade": True, # triggers cancellation of the old non-renewing subscription
                "old_subscription_id": business.payment_subscription_id,
                "old_email_token": business.subscription_email_token
            },
            amount=0
        )
        return success_response(data=data)
    except Exception as e:
        logger.error(f"Failed to initialize auto-recharge enable: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable subscription with payment provider")


# =============================================================================
# WEBHOOK HANDLER
# =============================================================================


@router.post("/webhooks/{provider}")
async def subscription_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle webhooks from payment providers.
    Uses idempotency check and atomic transactions.
    Sends email notifications for key events.
    """
    try:
        service = SubscriptionServiceFactory.get_service(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not supported")

    # Verify Signature
    body = await request.body()
    headers = dict(request.headers)

    logger.info(f"[WEBHOOK] Provider: {provider}")
    logger.info(f"[WEBHOOK] Headers keys: {list(headers.keys())}")
    logger.info(f"[WEBHOOK] x-paystack-signature present: {'x-paystack-signature' in headers}")
    logger.info(f"[WEBHOOK] Body preview (first 200 chars): {body[:200]}")

    if not service.verify_webhook_signature(headers, body):
        logger.warning(f"[WEBHOOK] ❌ Invalid Webhook Signature from {provider}")
        logger.warning(f"[WEBHOOK] Received signature: {headers.get('x-paystack-signature', 'NONE')}")
        raise HTTPException(status_code=401, detail="Invalid Signature")

    payload = await request.json()
    event = service.parse_webhook_event(payload)

    logger.info(f"[WEBHOOK] ✅ Signature verified successfully")
    logger.info(f"[WEBHOOK] Event type: {event['event_type']}")
    logger.info(f"[WEBHOOK] Customer email: {event.get('customer_email')}")
    logger.info(f"[WEBHOOK] Customer code: {event.get('customer_code')}")
    logger.info(f"[WEBHOOK] Subscription code: {event.get('subscription_code')}")
    logger.info(f"[WEBHOOK] Reference: {event.get('reference')}")
    logger.info(f"[WEBHOOK] Authorization code: {event.get('authorization_code')}")
    logger.info(f"[WEBHOOK] Email token: {event.get('email_token')}")

    # Idempotency Check
    reference = event.get("reference")
    if reference:
        existing_tx = db.query(PaymentTransaction).filter(
            PaymentTransaction.reference == reference
        ).first()
        if existing_tx:
            logger.info(f"[WEBHOOK] ⚠️ Duplicate reference: {reference}. Skipping.")
            return success_response(message="Duplicate Event Processed")
        logger.info(f"[WEBHOOK] Reference {reference} is new, processing...")

    try:
        business = None
        business_id = None

        if event["event_type"] == "SUBSCRIPTION_CREATED":
            business = _process_subscription_created(db, event)
            if business:
                business_id = business.id
                background_tasks.add_task(
                    send_subscription_created_email,
                    event["customer_email"],
                    business.subscription_tier.capitalize()
                )

        elif event["event_type"] == "RENEWAL_SUCCESS":
            business = _process_renewal_success(db, event)
            if business:
                business_id = business.id
                background_tasks.add_task(
                    send_payment_success_email,
                    event["customer_email"],
                    business.subscription_tier.capitalize(),
                    int(event.get("amount") or 0)
                )

        elif event["event_type"] == "SUBSCRIPTION_CANCELLED":
            business = _process_subscription_cancelled(db, event)
            if business:
                business_id = business.id
                background_tasks.add_task(
                    send_subscription_cancelled_email,
                    event["customer_email"]
                )

        elif event["event_type"] == "PAYMENT_FAILED":
            business = _process_payment_failed(db, event)
            if business:
                business_id = business.id
                background_tasks.add_task(
                    send_payment_failed_email,
                    event["customer_email"],
                    business.subscription_tier.capitalize()
                )

        elif event["event_type"] == "SUBSCRIPTION_NON_RENEWING":
            business = _process_non_renewing(db, event)
            if business:
                business_id = business.id

        # Log transaction if meaningful
        if reference and business_id:
            tx = PaymentTransaction(
                business_id=business_id,
                amount=int(event.get("amount") or 0),
                currency="NGN",
                status="success" if event["event_type"] != "PAYMENT_FAILED" else "failed",
                reference=reference,
                provider=provider,
                transaction_type=event["event_type"],
                transaction_metadata=event.get("raw_payload"),
                raw_webhook_payload=event.get("raw_payload")
            )
            db.add(tx)

        db.commit()
        logger.info(f"[WEBHOOK] ✅ Webhook processed. business_id={business_id}, event={event['event_type']}")
        return success_response(message="Webhook Processed Successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"[WEBHOOK] ❌ Processing Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Processing Error")


# =============================================================================
# WEBHOOK PROCESSING HELPERS
# =============================================================================


def _find_business(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Find business by email or customer_code from webhook event."""
    email = event.get("customer_email")
    customer_code = event.get("customer_code")
    logger.info(f"[WEBHOOK] Finding business for email={email}, customer_code={customer_code}")

    if email:
        user = db.query(User).filter(User.email == email).first()
        if user and user.business:
            logger.info(f"[WEBHOOK] ✅ Found business {user.business.id} via email")
            return user.business
        else:
            logger.info(f"[WEBHOOK] User lookup by email: user={'found' if user else 'NOT FOUND'}, business={'found' if user and user.business else 'NOT FOUND'}")

    if customer_code:
        business = db.query(Business).filter(
            Business.payment_customer_id == customer_code
        ).first()
        if business:
            logger.info(f"[WEBHOOK] ✅ Found business {business.id} via customer_code")
            return business
        else:
            logger.info(f"[WEBHOOK] Business lookup by customer_code: NOT FOUND")

    logger.error(f"[WEBHOOK] ❌ Business not found for email={email} / customer_code={customer_code}")
    return None


def _process_subscription_created(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Handle subscription.create — store subscription code, email token, authorization code."""
    logger.info(f"[WEBHOOK] Processing SUBSCRIPTION_CREATED")
    business = _find_business(db, event)
    if not business:
        return None

    # Store Paystack identifiers
    if event.get("customer_code"):
        business.payment_customer_id = event["customer_code"]
        logger.info(f"[WEBHOOK] Set payment_customer_id={event['customer_code']}")
    if event.get("subscription_code"):
        business.payment_subscription_id = event["subscription_code"]
        logger.info(f"[WEBHOOK] Set payment_subscription_id={event['subscription_code']}")
    if event.get("email_token"):
        business.subscription_email_token = event["email_token"]
        logger.info(f"[WEBHOOK] Set subscription_email_token={event['email_token']}")

    metadata = event.get("raw_payload", {}).get("data", {}).get("metadata", {})
    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    is_upgrade = metadata.get("is_upgrade", False)
    if is_upgrade:
        logger.info("[WEBHOOK] Subscription creation is an upgrade. Cancelling old subscription.")
        old_sub_id = metadata.get("old_subscription_id")
        old_token = metadata.get("old_email_token")
        if old_sub_id and old_token:
            try:
                from app.services.subscription.factory import SubscriptionServiceFactory
                service = SubscriptionServiceFactory.get_service("paystack")
                cancelled = service.cancel_subscription(subscription_code=old_sub_id, email_token=old_token)
                if not cancelled:
                    logger.warning(f"[WEBHOOK] Failed to cancel old subscription {old_sub_id}")
            except Exception as e:
                logger.error(f"[WEBHOOK] Error cancelling old subscription: {e}")

    business.subscription_status = "active"
    logger.info(f"[WEBHOOK] ✅ Business {business.id} subscription_status -> active")
    db.add(business)
    return business


def _process_renewal_success(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Handle charge.success — refresh credits, store authorization code, update payment date."""
    logger.info(f"[WEBHOOK] Processing RENEWAL_SUCCESS")
    business = _find_business(db, event)
    if not business:
        return None

    # Store/update Paystack identifiers
    if event.get("customer_code"):
        business.payment_customer_id = event["customer_code"]
    if event.get("subscription_code"):
        business.payment_subscription_id = event["subscription_code"]
    if event.get("authorization_code"):
        business.authorization_code = event["authorization_code"]
        logger.info(f"[WEBHOOK] Stored authorization_code for future upgrades")

    business.subscription_status = "active"
    business.last_payment_date = datetime.now(timezone.utc)

    metadata = event.get("raw_payload", {}).get("data", {}).get("metadata", {})
    if isinstance(metadata, str):
        import json
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}

    is_upgrade = metadata.get("is_upgrade", False)
    new_tier = metadata.get("tier")

    # Capture previous state before updating tier
    old_tier = business.subscription_tier or "spark"
    prev_allocated_ai = business.allocated_ai_responses or 0
    prev_used_ai = business.used_ai_responses or 0
    prev_allocated_escalations = business.allocated_escalations or 0
    prev_used_escalations = business.used_escalations or 0

    if new_tier:
        business.subscription_tier = new_tier

    # New plan allocation limits
    tier = business.subscription_tier or "spark"
    tier_info = TIER_LIMITS.get(tier, {})
    plan_ai = tier_info.get("monthly_credits", 100)
    plan_escalations = tier_info.get("max_monthly_escalations", 5)

    # Remaining quota from previous cycle: R = max(0, A - U)
    remaining_ai = max(0, prev_allocated_ai - prev_used_ai)
    remaining_escalations = max(0, prev_allocated_escalations - prev_used_escalations)

    is_tier_change = is_upgrade and new_tier and new_tier.lower() != old_tier.lower()

    if is_tier_change:
        # Upgrade to a different tier: proportional carry-over to prevent abuse
        # credit_ratio = remaining / previous_allocated
        # carryover = credit_ratio * new_plan_allocation
        if prev_allocated_ai > 0:
            ai_ratio = remaining_ai / prev_allocated_ai
            ai_carryover = ai_ratio * plan_ai
        else:
            ai_carryover = 0

        if prev_allocated_escalations > 0:
            esc_ratio = remaining_escalations / prev_allocated_escalations
            esc_carryover = esc_ratio * plan_escalations
        else:
            esc_carryover = 0

        new_ai = plan_ai + ai_carryover
        new_escalations = plan_escalations + esc_carryover
        logger.info(f"[WEBHOOK] Upgrade ({old_tier} -> {tier}). AI: {plan_ai} + {ai_carryover:.0f} carryover. Escalations: {plan_escalations} + {esc_carryover:.0f} carryover.")
    else:
        # Renewal or same-tier recharge: N = P + R
        new_ai = plan_ai + remaining_ai
        new_escalations = plan_escalations + remaining_escalations
        logger.info(f"[WEBHOOK] Renewal/recharge. AI: {plan_ai} + {remaining_ai} carryover = {new_ai}. Escalations: {plan_escalations} + {remaining_escalations} carryover = {new_escalations}.")

    # Cap carry-over at 2x plan allocation to prevent unlimited accumulation
    carryover_cap_ai = plan_ai * 2
    carryover_cap_escalations = plan_escalations * 2
    business.allocated_ai_responses = int(min(new_ai, carryover_cap_ai))
    business.allocated_escalations = int(min(new_escalations, carryover_cap_escalations))

    # Always reset usage counters
    business.used_ai_responses = 0
    business.used_escalations = 0

    logger.info(f"[WEBHOOK] Final allocations — AI: {business.allocated_ai_responses} (cap {carryover_cap_ai}), Escalations: {business.allocated_escalations} (cap {carryover_cap_escalations})")

    # Limit-based features: always set to new plan value (no carry-over)
    business.allocated_messages_per_session = tier_info.get("max_messages_per_session", 20)
    business.allocated_daily_sessions = tier_info.get("max_daily_sessions", 50)
    business.allocated_whitelisted_domains = tier_info.get("max_whitelisted_domains", 1)

    business.credits_last_refilled = datetime.now(timezone.utc)
    logger.info(f"[WEBHOOK] ✅ Business {business.id}: responses={business.allocated_ai_responses}, tier={tier}, status=active")

    db.add(business)
    return business


def _process_subscription_cancelled(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Handle subscription.disable — mark as cancelled."""
    business = _find_business(db, event)
    if not business:
        return None

    business.subscription_status = "cancelled"
    db.add(business)
    return business


def _process_payment_failed(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Handle invoice.payment_failed — mark as attention (needs user action)."""
    business = _find_business(db, event)
    if not business:
        return None

    business.subscription_status = "attention"
    db.add(business)
    return business


def _process_non_renewing(db: Session, event: Dict[str, Any]) -> Optional[Business]:
    """Handle subscription.not_renew — mark as non-renewing."""
    business = _find_business(db, event)
    if not business:
        return None

    business.subscription_status = "non-renewing"
    db.add(business)
    return business
