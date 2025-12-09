from unittest.mock import MagicMock

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Agentic RAG API"}

def test_upload_documents(client, monkeypatch):
    # Mock RAGService.upload_document
    async def mock_upload(file):
        return file.filename
    monkeypatch.setattr("app.services.rag_service.rag_service.upload_document", mock_upload)

    files = [
        ('files', ('test.txt', b'content', 'text/plain')),
    ]
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 200
    assert response.json()["files"] == ["test.txt"]

def test_process_documents(client, monkeypatch):
    # Mock RAGService.process_documents
    monkeypatch.setattr("app.services.rag_service.rag_service.process_documents", lambda: [])
    
    response = client.post("/rag/process")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_endpoint(client, mock_genai, monkeypatch):
    # Mock RAGService.query
    monkeypatch.setattr("app.services.rag_service.rag_service.query", lambda x: ["context"])
    
    mock_genai.generate_content.return_value.text = "Response"
    
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json()["response"] == "Response"
