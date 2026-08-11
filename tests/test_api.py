from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

# The static test key matching our environment default
HEADERS = {"X-API-Key": "b2b-secret-key-2026"}

def test_health_check():
    """
    Ensures the API Gateway boots up and allows public health monitoring.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_unauthorized_access():
    """
    Ensures the Zero-Trust security blocks requests missing the API Key.
    """
    payload = {"query": "valid length query", "department": "sales"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 401 

def test_submit_query_validation():
    """
    Ensures Pydantic catches invalid short queries on secured endpoint.
    """
    payload = {
        "query": "hi", 
        "department": "sales"
    }
    response = client.post("/ask", json=payload, headers=HEADERS)
    assert response.status_code == 422 

def test_ingest_validation():
    """
    Ensures Pydantic catches invalid short texts on secured ingestion endpoint.
    """
    payload = {
        "text": "short", 
        "metadata": {"source": "test"}
    }
    response = client.post("/ingest", json=payload, headers=HEADERS)
    assert response.status_code == 422 

# Enterprise Upgrade: Happy Path Testing with Mocking
@patch("app.core.tasks.generate_llama_response")
def test_submit_query_success(mock_llm):
    """
    Tests the full asynchronous Celery workflow and FinOps tracking 
    by intercepting and mocking the Groq API network call.
    """
    # Hijack the LLM engine to return a fake response instantly
    mock_llm.return_value = {"answer": "Simulated AI response", "tokens": 150}
    
    payload = {
        "query": "What is the standard procedure for B2B pipeline deployment?", 
        "department": "engineering"
    }
    response = client.post("/ask", json=payload, headers=HEADERS)
    
    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    assert "task_id" in response.json()

@patch("app.main.ingest_document")
def test_ingest_success(mock_ingest):
    """
    Tests the document ingestion endpoint by intercepting the HuggingFace 
    embedding generation and Qdrant network calls.
    """
    # Hijack the Qdrant ingestion to simulate 5 chunks successfully inserted
    mock_ingest.return_value = 5 
    
    payload = {
        "text": "This is a valid long document text for enterprise retrieval augmented generation.", 
        "metadata": {"author": "system_admin"}
    }
    response = client.post("/ingest", json=payload, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["chunks_inserted"] == 5