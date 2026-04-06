import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine
from sqlalchemy.orm import sessionmaker

from app.models.payment import PaymentTransaction

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

txs = db.query(PaymentTransaction).order_by(PaymentTransaction.created_at.desc()).limit(5).all()
for tx in txs:
    print(f"TX {tx.id} - TYPE: {tx.transaction_type} - REF: {tx.reference} - CREATED_AT: {tx.created_at}")
    if tx.transaction_metadata:
        meta = tx.transaction_metadata
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (ValueError, TypeError):
                pass
        
        data = meta.get('data', {}) if isinstance(meta, dict) else {}
        print("Metadata inside payload:", dict(data.get('metadata', {})))
        print("-" * 40)
