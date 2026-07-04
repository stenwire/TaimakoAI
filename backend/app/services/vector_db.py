import chromadb
from app.core.config import settings
from typing import List, Dict, Any

class VectorDBService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        
        # Initialize without a default embedding function
        # We will pass specific embeddings for each operation
        try:
             # Get existing or new - logic is same since we overwrite functionality via args
             self.collection = self.client.get_or_create_collection(name="rag_documents")
             
             # Check if it has an embedding function set that might conflict
             # Ideally we want it to be None/Default, but if we pass 'embeddings' param to add/query, 
             # Chroma should ignore the internal EF.
             # However, to be safe and clean given our previous switches:
             if self.collection.metadata is None: # Just a heuristic, real check is complex
                 pass 
                 
        except Exception as e:
            print(f"Error getting collection: {e}")
            self.collection = self.client.create_collection(name="rag_documents")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: List[List[float]] = None):
        """Add documents with their pre-computed embeddings."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings 
        )

    def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Dict[str, Any] = None):
        """Query using pre-computed query embeddings."""
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

    def delete(self, where: Dict[str, Any]):
        self.collection.delete(where=where)

vector_db = VectorDBService()
