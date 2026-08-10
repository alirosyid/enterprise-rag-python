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
    Ensures Pydantic catches invalid short queries.
    """
    payload = {
        "query": "hi", # Less than 5 characters (should fail)
        "department": "sales"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code == 422 # Unprocessable Entity