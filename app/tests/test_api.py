from fastapi.testclient import TestClient
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
    # This will now correctly match our custom 401 error handler in auth.py
    assert response.status_code == 401 

def test_submit_query_validation():
    """
    Ensures Pydantic catches invalid short queries on secured endpoint.
    """
    payload = {
        "query": "hi", # Less than 5 characters (should fail validation)
        "department": "sales"
    }
    response = client.post("/ask", json=payload, headers=HEADERS)
    assert response.status_code == 422 

def test_ingest_validation():
    """
    Ensures Pydantic catches invalid short texts on secured ingestion endpoint.
    """
    payload = {
        "text": "short", # Less than 10 characters (should fail)
        "metadata": {"source": "test"}
    }
    response = client.post("/ingest", json=payload, headers=HEADERS)
    assert response.status_code == 422