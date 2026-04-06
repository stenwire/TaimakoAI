
from app.db.session import SessionLocal
from app.models.plan import Plan

def main():
    db = SessionLocal()
    tiers_map = {
        "spark": 1,
        "ignite": 2,
        "blaze": 3,
        "inferno": 4
    }
    
    plans = db.query(Plan).all()
    for plan in plans:
        name = plan.name.lower()
        if name in tiers_map:
            plan.tier = tiers_map[name]
        else:
            plan.tier = 0
            
    db.commit()
    db.close()
    print("Tiers updated successfully.")

if __name__ == "__main__":
    main()
