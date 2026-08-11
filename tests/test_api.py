from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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

# Enterprise Upgrade: Mock the Task Dispatcher, not the internal worker logic
@patch("app.main.process_rag_query.delay")
def test_submit_query_success(mock_delay):
    """
    Tests API routing by intercepting the Celery dispatcher.
    In enterprise unit tests, API and Background Workers must be tested in total isolation.
    """
    # Simulate Celery returning an AsyncResult with a fake UUID
    mock_task = MagicMock()
    mock_task.id = "mocked-uuid-1234"
    mock_delay.return_value = mock_task
    
    payload = {
        "query": "What is the standard procedure for B2B pipeline deployment?", 
        "department": "engineering"
    }
    response = client.post("/ask", json=payload, headers=HEADERS)
    
    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    assert response.json()["task_id"] == "mocked-uuid-1234"
    mock_delay.assert_called_once()

@patch("app.main.ingest_document")
def test_ingest_success(mock_ingest):
    """
    Tests the document ingestion API layer isolation.
    """
    mock_ingest.return_value = 5 
    
    payload = {
        "text": "This is a valid long document text for enterprise retrieval augmented generation.", 
        "metadata": {"author": "system_admin"}
    }
    response = client.post("/ingest", json=payload, headers=HEADERS)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["chunks_inserted"] == 5