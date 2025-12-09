import pytest
from unittest.mock import MagicMock, patch
from app.services.rag_service import rag_service
from app.models.document import Document
from app.models.user import User

@pytest.fixture
def mock_file_storage(monkeypatch):
    mock = MagicMock()
    mock.save.return_value = "saved/path/test.txt"
    mock.get_full_path.return_value = "/tmp/saved/path/test.txt"
    monkeypatch.setattr(rag_service, "file_storage", mock)
    return mock

@pytest.fixture
def mock_vector_db_service(monkeypatch):
    # This should mock the service instance 'vector_db' imported in rag_service
    mock = MagicMock()
    monkeypatch.setattr(rag_service, "vector_db", mock)
    return mock

def test_upload_document_scoped(db_session, mock_file_storage):
    user_id = "user_123"
    file_mock = MagicMock()
    file_mock.filename = "test.txt"
    
    # Run async function in sync test? pytest-asyncio handles this if marked async
    # But RAGService.upload_document is async.
    import asyncio
    loop = asyncio.new_event_loop()
    filename = loop.run_until_complete(rag_service.upload_document(file_mock, user_id, db_session))
    
    assert filename == "test.txt"
    mock_file_storage.save.assert_called_once()
    
    # Verify DB
    doc = db_session.query(Document).filter(Document.user_id == user_id).first()
    assert doc is not None
    assert doc.filename == "test.txt"
    assert doc.status == "pending"

def test_process_documents_scoped(db_session, mock_file_storage, mock_vector_db_service):
    user1 = "u1"
    user2 = "u2"
    
    # Setup DB with pending docs for both users
    doc1 = Document(user_id=user1, filename="doc1.txt", file_path="p1", status="pending")
    doc2 = Document(user_id=user2, filename="doc2.txt", file_path="p2", status="pending")
    db_session.add_all([doc1, doc2])
    db_session.commit()
    
    # Mock file content
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "content"
        with patch("os.path.exists", return_value=True):
            # Process for User 1
            results = rag_service.process_documents(user1, db_session)
            
            assert len(results) == 1
            assert results[0].filename == "doc1.txt"
            
            # Verify DB updates
            db_session.refresh(doc1)
            db_session.refresh(doc2)
            assert doc1.status == "processed"
            assert doc2.status == "pending" # User 2 doc untouched
            
            # Verify Vector DB add with user metadata
            args, kwargs = mock_vector_db_service.add_documents.call_args
            metadatas = kwargs['metadatas']
            assert metadatas[0]['user_id'] == user1

def test_list_documents_scoped(db_session):
    db_session.add(Document(user_id="u1", filename="a.txt", file_path="p", status="processed"))
    db_session.add(Document(user_id="u2", filename="b.txt", file_path="p", status="processed"))
    db_session.commit()
    
    docs1 = rag_service.list_documents("u1", db_session)
    assert docs1 == ["a.txt"]
    
    docs2 = rag_service.list_documents("u2", db_session)
    assert docs2 == ["b.txt"]

def test_query_scoped(mock_vector_db_service):
    rag_service.query("check", "u1")
    
    mock_vector_db_service.query.assert_called_once()
    args, kwargs = mock_vector_db_service.query.call_args
    assert kwargs['where'] == {"user_id": "u1"}
