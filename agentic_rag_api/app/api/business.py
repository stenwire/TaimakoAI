from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.core.response_wrapper import success_response
from app.services.analysis_agent import generate_business_intents

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
        custom_agent_instruction=business_data.custom_agent_instruction
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    
    return success_response(
        message="Business profile created successfully",
        data=BusinessResponse.model_validate(business)
    )

@router.get("/business", response_model=None)
async def get_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's business profile."""
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found. Please create one first.")
    
    return success_response(data=BusinessResponse.model_validate(business))

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
    
    db.commit()
    db.refresh(business)
    
    return success_response(
        message="Business profile updated successfully",
        data=BusinessResponse.model_validate(business)
    )

@router.post("/business/generate-intents", response_model=None)
async def generate_intents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business or not business.description:
        raise HTTPException(status_code=400, detail="Business description is required to generate intents.")
        
    intents = await generate_business_intents(business.description)
    return success_response(data={"intents": intents})
