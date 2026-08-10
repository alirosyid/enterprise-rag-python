from fastapi import FastAPI
import logging
from app.db.session import engine, Base
# Import models so SQLAlchemy metadata recognizes it
from app.db import models 

# Production standard logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instruct SQLAlchemy to create tables in PostgreSQL based on models.py
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise RAG API Gateway",
    description="Event-driven API Gateway routing requests to Celery workers.",
    version="1.0.0"
)

# Basic endpoint to check if the server is alive (Health Check)
@app.get("/")
async def health_check():
    return {"status": "online", "service": "API Gateway", "database_synced": True}