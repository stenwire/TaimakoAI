from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from typing import List
from app.services.rag_service import rag_service
from app.services.agent_service import run_conversation
from app.schemas.document import IngestResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.core.security_utils import decrypt_string
import asyncio

from app.core.response_wrapper import success_response

router = APIRouter()

@router.post("/documents/upload", response_model=None)
async def upload_documents(
    files: List[UploadFile] = File(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate that at least one file is provided
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate that all files have valid filenames
    for file in files:
        if not file.filename or file.filename.strip() == "":
            raise HTTPException(status_code=400, detail="Invalid file: filename is missing")
    
    saved_files = []
    for file in files:
        filename = await rag_service.upload_document(file, user_id=current_user.id, db=db)
        saved_files.append(filename)
    return success_response(message="Files uploaded successfully", data={"files": saved_files})

@router.get("/documents", response_model=None)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(data=rag_service.list_documents(user_id=current_user.id, db=db))

@router.delete("/documents/{document_id}", response_model=None)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = rag_service.delete_document(document_id=document_id, user_id=current_user.id, db=db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return success_response(message="Document deleted successfully")

@router.post("/rag/process", response_model=None)
async def start_rag_process(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(data=rag_service.process_documents(user_id=current_user.id, db=db))

@router.post("/chat", response_model=None)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with the agent using user's business configuration."""
    # Import Business model
    from app.models.business import Business
    
    # Fetch user's business profile
    business = db.query(Business).filter(Business.user_id == current_user.id).first()
    if not business:
        raise HTTPException(
            status_code=400, 
            detail="Business profile not found. Please create a business profile before using the chat."
        )
    
    # Decrypt the API key from business profile
    decrypted_key = None
    if business.gemini_api_key:
        decrypted_key = decrypt_string(business.gemini_api_key)
    
    if not decrypted_key:
        raise HTTPException(
            status_code=400,
            detail="API key not configured. Please set your Google Gemini API key in Settings."
        )
    
    # Use user.id as session_id for chat history per user
    response_text = await run_conversation(
        message=request.message,
        user_id=current_user.id,
        business_name=business.business_name,
        custom_instruction=business.custom_agent_instruction,
        session_id=current_user.id,
        intents=business.intents,
        api_key=decrypted_key
    )
    return success_response(data=ChatResponse(response=response_text))