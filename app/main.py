from fastapi import FastAPI
import logging

# Konfigurasi logging standar produksi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise RAG API Gateway",
    description="Event-driven API Gateway routing requests to Celery workers.",
    version="1.0.0"
)

# Endpoint dasar untuk mengecek apakah server hidup (Health Check)
@app.get("/")
async def health_check():
    return {"status": "online", "service": "API Gateway", "version": "1.0.0"}