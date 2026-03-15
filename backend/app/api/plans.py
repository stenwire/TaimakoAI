from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.plan import Plan
from app.core.response_wrapper import success_response, error_response
from app.services.subscription.factory import SubscriptionServiceFactory
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/public/plans", response_model=Dict[str, Any])
def get_plans(db: Session = Depends(get_db)):
    """
    Retrieve all active plans (public endpoint, no auth required).
    """
    try:
        plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.tier.asc()).all()

        plans_data = []
        for p in plans:
            import ast
            features = p.features
            if isinstance(features, str):
                try:
                    features = ast.literal_eval(features)
                except Exception:
                    features = {}

            if isinstance(features, dict):
                if features == {}:
                    features = []
                else:
                    formatted_features = []
                    for k, v in features.items():
                        key_str = k.replace("_", " ").title()
                        formatted_features.append(f"{v} {key_str}")
                    features = formatted_features
            elif not isinstance(features, list):
                features = [str(features)] if features else []

            plans_data.append({
                "id": p.id,
                "plan_code": p.plan_code,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "currency": p.currency,
                "interval": p.interval,
                "tier": p.tier,
                "features": features
            })

        return success_response(data=plans_data, message="Plans retrieved successfully")
    except Exception as e:
        logger.error(f"Failed to retrieve plans: {e}")
        return error_response(message="Failed to retrieve plans", error=str(e))


class SyncPlansRequest(BaseModel):
    provider: Optional[str] = "paystack"


@router.post("/plans/sync", response_model=None)
def sync_plans(
    req: SyncPlansRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync plans from the payment provider into the local database.
    Protected endpoint — requires authentication.
    Upserts plans: updates existing ones by plan_code, creates new ones.
    """
    try:
        service = SubscriptionServiceFactory.get_service(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        remote_plans = service.sync_plans()
    except Exception as e:
        logger.error(f"Failed to fetch plans from provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch plans from payment provider")

    synced = 0
    created = 0

    for rp in remote_plans:
        plan_code = rp.get("plan_code")
        if not plan_code:
            continue

        existing = db.query(Plan).filter(Plan.plan_code == plan_code).first()
        if existing:
            # Update existing plan
            existing.name = rp.get("name", existing.name)
            existing.price = rp.get("amount", existing.price)
            existing.currency = rp.get("currency", existing.currency)
            existing.interval = rp.get("interval", existing.interval)
            synced += 1
        else:
            # Create new plan
            new_plan = Plan(
                plan_code=plan_code,
                name=rp.get("name", ""),
                price=rp.get("amount", 0),
                currency=rp.get("currency", "NGN"),
                interval=rp.get("interval", "monthly"),
                tier=0,  # Default tier, update manually later
                features={},  # Features to be set manually after sync
                description=""
            )
            db.add(new_plan)
            created += 1

    db.commit()
    logger.info(f"Plans synced: {synced} updated, {created} created")

    return success_response(
        message=f"Plans synced successfully. {synced} updated, {created} created.",
        data={"updated": synced, "created": created}
    )
