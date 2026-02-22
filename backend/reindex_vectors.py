import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.vector_db import vector_db
from app.services.rag_service import rag_service
from sqlalchemy import text

def reindex():
    print("Starting Re-indexing Process...")
    
    # 1. Reset Vector DB
    try:
        print("Deleting existing vector collection 'rag_documents'...")
        try:
            vector_db.client.delete_collection("rag_documents")
            print("✅ Collection deleted.")
        except Exception as e:
            # It might complain if it doesn't exist
            print(f"⚠️ Delete collection message (proceeding): {e}")

        print("Recreating collection 'rag_documents'...")
        # This updates the reference in the singleton vector_db instance too
        vector_db.collection = vector_db.client.create_collection("rag_documents")
        print("✅ Collection recreated.")
        
    except Exception as e:
        print(f"❌ Error resetting vector DB: {e}")
        return

    db = SessionLocal()
    try:
        # 2. Reset Document Status in Postgres
        print("Resetting all document statuses to 'pending' in Postgres...")
        
        # Using SQLAlchemy Core for bulk update
        db.execute(text("UPDATE documents SET status = 'pending', error_message = NULL"))
        db.commit()
        print("✅ Documents marked as pending.")
        
        # 3. Trigger Processing
        print("Triggering processing for all users...")
        
        # Get all distinct user_ids with documents
        # We need to process per user because RAG service expects user_id
        result = db.execute(text("SELECT DISTINCT user_id FROM documents"))
        user_ids = [row[0] for row in result]
        
        print(f"Found {len(user_ids)} users with documents.")
        
        for user_id in user_ids:
            print(f"Processing documents for user: {user_id}...")
            # process_documents handles fetching the API key via Business model
            results = rag_service.process_documents(user_id, db)
            
            success_count = sum(1 for r in results if r.status == "success")
            error_count = len(results) - success_count
            print(f"  User {user_id}: {success_count} succeeded, {error_count} failed.")
            
        print("\n✅ Re-indexing Complete!")
        
    except Exception as e:
        print(f"\n❌ Error during re-indexing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reindex()
