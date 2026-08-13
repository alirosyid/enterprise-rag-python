from fastapi.testclient import TestClient
from app.main import app

# Inisialisasi klien penguji bawaan FastAPI
client = TestClient(app)

def test_api_gateway_health():
    """
    Memvalidasi bahwa API Gateway dapat melakukan inisialisasi awal 
    tanpa dependensi database yang crash atau routing yang rusak.
    """
    response = client.get("/")
    
    # Validasi deterministik status sistem
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert response.json()["service"] == "API Gateway"