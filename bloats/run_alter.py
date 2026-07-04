import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE payment_transactions ADD COLUMN raw_webhook_payload JSON;"))
        print("Successfully added column raw_webhook_payload to payment_transactions")
    except Exception as e:
        print(f"Error adding column: {e}")
