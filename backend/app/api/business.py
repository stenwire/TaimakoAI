from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.core.response_wrapper import success_response
from app.services.analysis_agent import generate_business_intents
from app.core.security_utils import encrypt_string, decrypt_string


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
        gemini_api_key=encrypt_string(business_data.gemini_api_key) if business_data.gemini_api_key else None
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    
    response = BusinessResponse.model_validate(business)
    response.is_api_key_set = bool(business.gemini_api_key)
    
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
    response.is_api_key_set = bool(business.gemini_api_key)
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
    if business_data.gemini_api_key is not None and business_data.gemini_api_key != "":
        # Only update API key if a non-empty value is provided
        business.gemini_api_key = encrypt_string(business_data.gemini_api_key)
    
    db.commit()
    db.refresh(business)
    
    response = BusinessResponse.model_validate(business)
    response.is_api_key_set = bool(business.gemini_api_key)

    return success_response(
        message="Business profile updated successfully",
        data=response
    )

@router.post("/business/validate-key", response_model=None)
async def validate_api_key(
    key_data: dict, # Using dict to avoid importing ValidateKeyRequest for now or just generic
    current_user: User = Depends(get_current_user)
):
    """Validate a Google Gemini API Key."""
    api_key = key_data.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
        
    try:
        from google import genai
        # Initialize client with the key
        client = genai.Client(api_key=api_key)
        # Attempt a simple lightweight call. Validating 'models.list' or similar is usually cheapest/fastest.
        # Or just sending "Hello"?
        # Checking list of models is a good connectivity test.
        # However, listing models might not verify if the key has access to generate content?
        # Let's try to list models.
        # Note: genai v2 SDK usage might differ slightly. Assuming standard google-genai usage.
        # If the environment is using `google.generativeai` (old sdk) or `google-genai` (new SDK).
        # Based on imports in agent_service.py: `from google.genai import types` -> It's the new SDK.
        
        # New SDK supports `client.models.list()`?
        # Or we can just try generating "test".
        
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents='Test'
        )
        # If no exception, we are good?
        
    except Exception as e:
        print(f"Key Validation Failed: {e}")
        # Return 200 with success=False to let frontend handle message? 
        # Or 400? 400 is better for 'Invalid Request/Input'.
        raise HTTPException(status_code=400, detail=f"Invalid API Key: {str(e)}")

    return success_response(message="API Key is valid")

@router.post("/business/generate-intents", response_model=None)
async def generate_intents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business or not business.description:
        raise HTTPException(status_code=400, detail="Business description is required to generate intents.")
        
    api_key = None
    if business.gemini_api_key:
        api_key = decrypt_string(business.gemini_api_key)
        
    intents = await generate_business_intents(business.description, api_key=api_key)
    return success_response(data={"intents": intents})
