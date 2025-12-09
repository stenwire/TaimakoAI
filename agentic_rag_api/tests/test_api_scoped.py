import pytest
from unittest.mock import patch, MagicMock
from app.core.security import create_access_token
from app.models.user import User

def test_api_upload_documents_scoped(client, db_session):
    # 1. Auth Headers
    token = create_access_token(subject="u1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create User
    db_session.add(User(id="u1", email="u1@test.com", google_id="g1"))
    db_session.commit()
    
    # 3. Upload
    with patch("app.services.rag_service.rag_service.upload_document", return_value="f1.txt") as mock_upload:
        files = {'files': ('test.txt', b'content', 'text/plain')}
        response = client.post("/documents/upload", files=files, headers=headers)
        
        assert response.status_code == 200
        mock_upload.assert_called_once()
        # Verify user_id was passed
        args, kwargs = mock_upload.call_args
        assert kwargs['user_id'] == "u1"

def test_api_list_documents_scoped(client, db_session):
    # 1. Auth Headers
    token = create_access_token(subject="u1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create User
    db_session.add(User(id="u1", email="u1@test.com", google_id="g1"))
    db_session.commit()
    
    # 3. List
    with patch("app.services.rag_service.rag_service.list_documents", return_value=["f1.txt"]) as mock_list:
        response = client.get("/documents", headers=headers)
        
        assert response.status_code == 200
        mock_list.assert_called_once()
        args, kwargs = mock_list.call_args
        assert kwargs['user_id'] == "u1"

def test_api_process_documents_scoped(client, db_session):
    # 1. Auth Headers
    token = create_access_token(subject="u1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create User
    db_session.add(User(id="u1", email="u1@test.com", google_id="g1"))
    db_session.commit()
    
    # 3. Process
    with patch("app.services.rag_service.rag_service.process_documents", return_value=[]) as mock_process:
        response = client.post("/rag/process", headers=headers)
        
        assert response.status_code == 200
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert kwargs['user_id'] == "u1"

def test_api_chat_scoped(client, db_session):
    # 1. Auth Headers
    token = create_access_token(subject="u1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create User
    db_session.add(User(id="u1", email="u1@test.com", google_id="g1"))
    db_session.commit()
    
    # 3. Chat
    with patch("app.api.routes.run_conversation", return_value="Bot says hi") as mock_chat:
        response = client.post("/chat", json={"message": "hello"}, headers=headers)
        
        assert response.status_code == 200
        mock_chat.assert_called_once()
        args, kwargs = mock_chat.call_args
        assert kwargs['user_id'] == "u1"
        assert kwargs['session_id'] == "u1"
