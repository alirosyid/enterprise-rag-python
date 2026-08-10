from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """
    Ensures the API Gateway is successfully booting up and responding.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_submit_query_validation():
    """
    Ensures Pydantic catches invalid short queries on the /ask endpoint.
    """
    payload = {
        "query": "hi", # Less than 5 characters (should fail)
        "department": "sales"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 422 

def test_ingest_validation():
    """
    Ensures Pydantic catches invalid short texts on the /ingest endpoint.
    """
    payload = {
        "text": "short", # Less than 10 characters (should fail)
        "metadata": {"source": "test"}
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 422