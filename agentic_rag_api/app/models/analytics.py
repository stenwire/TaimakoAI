import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date
from datetime import datetime, timezone
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class AnalyticsDailySummary(Base):
    __tablename__ = "analytics_daily_summary"

    id = Column(String, primary_key=True, default=generate_uuid)
    # Linking to User (business owner) instead of specific business object if 'Business' table exists and is linked to User.
    # Assuming 'Business' table exists based on previous file listings, but commonly analytics might just aggregate by user_id if that's the tenant key.
    # Checking widget.py, WidgetSettings links to User. So we should link to User or Business.
    # Plan mentioned 'business_id', but let's check if Business model exists. 'business.py' was in the list.
    # Let's assume linking to Business is proper if we have multi-tenant.
    # For now, I'll link to User as the 'tenant' or Business if clearer. 
    # Let's use 'business_id' as per user request "id, business_id...".
    
    # Wait, I need to be sure Business ID is available.
    # Let's check 'business.py' quickly or just link to 'WidgetSettings' which is 1:1 with business usually?
    # Actually, the user request explicitly said: "analytics_daily_summary: id, business_id, date..."
    # I'll check business.py content to be sure.
    
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    total_sessions = Column(Integer, default=0)
    total_guests = Column(Integer, default=0)
    new_guests = Column(Integer, default=0)
    returning_guests = Column(Integer, default=0)
    leads_captured = Column(Integer, default=0)
    
    # Simple top stats storage (could be JSON or just text for simplicity)
    top_intent = Column(String, nullable=True) 
    top_location = Column(String, nullable=True)
    top_referrer = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
