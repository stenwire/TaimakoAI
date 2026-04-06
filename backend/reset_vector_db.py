import chromadb
from app.core.config import settings

def reset_vector_db():
    print(f"Connecting to ChromaDB at {settings.CHROMA_DB_DIR}...")
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        
        # Try to get the collection to see if it exists
        try:
            client.get_collection(name="rag_documents")
            print("Found existing collection 'rag_documents'. Deleting...")
            client.delete_collection(name="rag_documents")
            print("✅ Collection 'rag_documents' deleted.")
        except Exception as e:
            print(f"Collection 'rag_documents' not found or could not be accessed: {e}")
            
        print("Recreating collection 'rag_documents'...")
        # We recreate it to ensure it's fresh and ready for new embeddings
        client.create_collection(name="rag_documents")
        print("✅ Collection 'rag_documents' created successfully.")
        
    except Exception as e:
        print(f"❌ Error resetting vector DB: {e}")

if __name__ == "__main__":
    reset_vector_db()
