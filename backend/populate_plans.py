import sys
import os

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.plan import Plan
from app.core.subscription import TIER_LIMITS

def populate_plans():
    db = SessionLocal()
    try:
        print("Starting plan population...")
        for tier_name, features in TIER_LIMITS.items():
            plan_code = tier_name
            name = tier_name.capitalize()
            description = features.get("description", "")
            
            # Check if plan exists
            existing_plan = db.query(Plan).filter(Plan.plan_code == plan_code).first()
            if existing_plan:
                print(f"Updating plan: {name}")
                existing_plan.name = name
                existing_plan.description = description
                existing_plan.features = features
                # Keep existing price/currency if set manually, otherwise defaults apply for new
            else:
                print(f"Creating plan: {name}")
                new_plan = Plan(
                    plan_code=plan_code,
                    name=name,
                    description=description,
                    features=features,
                    price=0,
                    currency="NGN"
                )
                db.add(new_plan)
        
        db.commit()
        print("Plan population completed successfully.")
    except Exception as e:
        print(f"Error populating plans: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_plans()
