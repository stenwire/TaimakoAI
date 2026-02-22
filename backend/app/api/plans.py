from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.plan import Plan
from app.core.response_wrapper import success_response, error_response
from typing import List, Dict, Any

router = APIRouter()

@router.get("/public/plans", response_model=Dict[str, Any])
def get_plans(db: Session = Depends(get_db)):
    """
    Retrieve all available plans.
    """
    try:
        plans = db.query(Plan).filter(Plan.is_active == True).all()
        
        # Serialize plans (or use Pydantic model response_model=List[PlanSchema])
        # For now, manually dictify to match existing patterns if needed, or rely on auto-conversion if response_model was set.
        # Given response wrapper structure, let's return data dict.
        
        plans_data = []
        for p in plans:
            plans_data.append({
                "id": p.id,
                "plan_code": p.plan_code,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "currency": p.currency,
                "features": p.features
            })
            
        return success_response(data=plans_data, message="Plans retrieved successfully")
    except Exception as e:
        return error_response(message="Failed to retrieve plans", error=str(e))
