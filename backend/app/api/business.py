from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.plan import Plan
from app.models.widget import WidgetSettings
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.core.response_wrapper import success_response
from app.services.analysis_agent import generate_business_intents
from app.core.config import settings

from app.core.subscription import SubscriptionTier

router = APIRouter()

@router.post("/business", response_model=None)
async def create_business(
    business_data: BusinessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a business profile for the current user."""
    # Check if user already has a business
    existing_business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if existing_business:
        raise HTTPException(status_code=400, detail="Business profile already exists. Use PUT to update.")
    
    # Create new business
    business = Business(
        user_id=current_user.id,
        business_name=business_data.business_name,
        description=business_data.description,
        website=business_data.website,
        custom_agent_instruction=business_data.custom_agent_instruction,
        logo_url=business_data.logo_url,
        is_escalation_enabled=business_data.is_escalation_enabled,
        escalation_emails=business_data.escalation_emails,
        # Subscription Defaults
        subscription_tier=SubscriptionTier.SPARK.value
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    
    # Sync logo_url to WidgetSettings if exists
    if business.logo_url:
        widget_settings = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
        if widget_settings:
            widget_settings.logo_url = business.logo_url
            db.commit()

    
    response = BusinessResponse.model_validate(business)
    _enrich_plan_fields(response, business, db)

    return success_response(
        message="Business profile created successfully",
        data=response
    )

@router.get("/business", response_model=None)
async def get_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's business profile."""
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        return success_response(data=None)

    response = BusinessResponse.model_validate(business)
    _enrich_plan_fields(response, business, db)
    return success_response(data=response)

@router.put("/business", response_model=None)
async def update_business(
    business_data: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's business profile."""
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found. Please create one first.")
    
    # Update fields if provided
    if business_data.business_name is not None:
        business.business_name = business_data.business_name
    if business_data.description is not None:
        business.description = business_data.description
    if business_data.website is not None:
        business.website = business_data.website
    if business_data.custom_agent_instruction is not None:
        business.custom_agent_instruction = business_data.custom_agent_instruction
    if business_data.intents is not None:
        business.intents = business_data.intents
    if business_data.logo_url is not None:
        business.logo_url = business_data.logo_url
    if business_data.is_escalation_enabled is not None:
        business.is_escalation_enabled = business_data.is_escalation_enabled
    if business_data.escalation_emails is not None:
        business.escalation_emails = business_data.escalation_emails
    
    # Sync logo_url to WidgetSettings
    if business_data.logo_url is not None:
        widget_settings = db.query(WidgetSettings).filter(WidgetSettings.user_id == current_user.id).first()
        if widget_settings:
            widget_settings.logo_url = business_data.logo_url
            # If we don't commit here, the final commit below will handle it?
            # Yes, standard SQLAlchemy session behavior.

    
    db.commit()
    db.refresh(business)
    
    response = BusinessResponse.model_validate(business)
    _enrich_plan_fields(response, business, db)

    return success_response(
        message="Business profile updated successfully",
        data=response
    )

def _enrich_plan_fields(response: BusinessResponse, business: Business, db: Session):
    """Look up the Plan by subscription_tier and populate plan fields on the response."""
    plan = db.query(Plan).filter(Plan.name.ilike(business.subscription_tier)).first()
    if plan:
        response.plan_name = plan.name
        response.plan_code = plan.plan_code
        response.plan_price = plan.price
        response.plan_currency = plan.currency
        response.plan_interval = plan.interval
        features = plan.features
        if isinstance(features, str):
            import ast
            try:
                features = ast.literal_eval(features)
            except Exception:
                features = {}
        response.plan_features = features


@router.post("/business/generate-intents", response_model=None)
async def generate_intents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business or not business.description:
        raise HTTPException(status_code=400, detail="Business description is required to generate intents.")
        
    intents = await generate_business_intents(business.description, api_key=settings.GOOGLE_API_KEY)
    return success_response(data={"intents": intents})
