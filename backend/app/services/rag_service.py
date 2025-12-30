import uuid
import os
import shutil
from typing import List, Optional
from fastapi import UploadFile
from pypdf import PdfReader
import io
import google.generativeai as genai
from app.services.vector_db import vector_db
from app.utils.text_splitter import recursive_character_text_splitter
from app.schemas.document import IngestResponse
from app.models.document import Document
from app.models.business import Business
from app.services.file_storage import file_storage
from app.core.security_utils import decrypt_string
from sqlalchemy.orm import Session

class RAGService:
    def __init__(self):
        self.vector_db = vector_db
        self.file_storage = file_storage

    def _get_embedding(self, text: str, api_key: str) -> List[float]:
        """Generate embedding using Google's Generative AI."""
        if not api_key:
            raise ValueError("API Key is required for generating embeddings.")
        
        try:
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise e

    def _get_query_embedding(self, text: str, api_key: str) -> List[float]:
        """Generate query embedding."""
        if not api_key:
            raise ValueError("API Key is required for generating query embeddings.")
            
        try:
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            raise e

    async def upload_document(self, file: UploadFile, user_id: str, db: Session) -> str:
        # Save to file storage
        file_path = self.file_storage.save(file.file, file.filename, user_id)
        
        # Save to DB
        doc = Document(
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return doc.filename

    def process_documents(self, user_id: str, db: Session) -> List[IngestResponse]:
        results = []
        
        # Fetch business to get API Key
        business = db.query(Business).filter(Business.user_id == user_id).first()
        api_key = None
        if business and business.gemini_api_key:
             api_key = decrypt_string(business.gemini_api_key)
             
        if not api_key:
            # Cannot process without API Key
            print(f"Cannot process documents for user {user_id}: No API Key found.")
            # We fail all pending docs for this user to avoid getting stuck
            # Or just return error
            return [IngestResponse(filename="Error", chunks_created=0, status="Error: Business API Key not configured.")]

        # Fetch pending documents for user
        documents = db.query(Document).filter(
            Document.user_id == user_id, 
            Document.status == "pending"
        ).all()
        
        for doc in documents:
            try:
                text = ""
                full_path = self.file_storage.get_full_path(doc.file_path)
                
                if not os.path.exists(full_path):
                     raise FileNotFoundError(f"File not found at {full_path}")

                if doc.filename.endswith(".pdf"):
                    reader = PdfReader(full_path)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                else:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()
                
                chunks = recursive_character_text_splitter(text)
                ids = [str(uuid.uuid4()) for _ in chunks]
                
                # Generate embeddings for all chunks
                embeddings = [self._get_embedding(chunk, api_key) for chunk in chunks]
                
                # Embed chunks with user_id metadata for filtering
                metadatas = [{"filename": doc.filename, "chunk_index": i, "user_id": user_id} for i in range(len(chunks))]
                
                if chunks:
                    self.vector_db.add_documents(documents=chunks, metadatas=metadatas, ids=ids, embeddings=embeddings)
                
                doc.status = "processed"
                results.append(IngestResponse(
                    filename=doc.filename,
                    chunks_created=len(chunks),
                    status="success"
                ))
            except Exception as e:
                print(f"Error processing {doc.filename}: {e}")
                doc.status = "error"
                doc.error_message = str(e)
                results.append(IngestResponse(
                    filename=doc.filename,
                    chunks_created=0,
                    status=f"error: {str(e)}"
                ))
        
        db.commit()
        return results

    def list_documents(self, user_id: str, db: Session) -> List[dict]:
        # Return docs from DB
        docs = db.query(Document).filter(Document.user_id == user_id).all()
        return [
            {
                "id": doc.id,
                "filename": doc.filename, 
                "status": doc.status, 
                "created_at": doc.created_at,
                "error_message": doc.error_message
            } 
            for doc in docs
        ]

    def query(self, text: str, user_id: str, api_key: Optional[str] = None, db: Session = None) -> List[str]:
        # If API key is not provided (e.g. legacy call? unlikely), try to fetch from DB
        if not api_key:
            if db:
                business = db.query(Business).filter(Business.user_id == user_id).first()
                if business and business.gemini_api_key:
                    api_key = decrypt_string(business.gemini_api_key)
        
        if not api_key:
            print(f"Query failed: No API Key available for user {user_id}")
            return []

        try:
             query_embedding = self._get_query_embedding(text, api_key)
             # Query with user_id filter and query_embedding
             # Wrap in list as vector_db expects list of embeddings
             results = self.vector_db.query(query_embeddings=[query_embedding], where={"user_id": user_id})
             
             if results and results['documents']:
                 return results['documents'][0]
             return []
        except Exception as e:
            print(f"Error querying RAG: {e}")
            return []

    def delete_document(self, document_id: str, user_id: str, db: Session) -> bool:
        doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            return False
            
        # Delete from Chroma
        # Using $and operator for multiple conditions as required by newer Chroma versions
        self.vector_db.delete(where={"$and": [{"filename": doc.filename}, {"user_id": user_id}]})
        
        # Delete file
        try:
            self.file_storage.delete(doc.file_path)
        except Exception:
            # Continue even if file delete fails (maybe already gone)
            pass
        
        # Delete from DB
        db.delete(doc)
        db.commit()
        
        return True

rag_service = RAGService()
