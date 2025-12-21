import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from typing import List, Dict, Any

class VectorDBService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        self.collection = self.client.get_or_create_collection(name="rag_documents")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 5, where: Dict[str, Any] = None):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )

    def delete(self, where: Dict[str, Any]):
        self.collection.delete(where=where)

vector_db = VectorDBService()
