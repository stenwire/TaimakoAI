from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DocumentMetadata(BaseModel):
    filename: str
    content_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    chunk_id: Optional[int] = None

class DocumentChunk(BaseModel):
    text: str
    metadata: DocumentMetadata

class IngestResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime
    error_message: Optional[str] = None
