from fastapi import FastAPI, HTTPException, Depends
import logging
from app.db.session import engine, Base
from app.db.models import FinOpsLog  # ENTERPRISE FIX: Load models into memory before create_all
from app.api.schemas import QueryRequest, TaskResponse, IngestRequest, IngestResponse
from app.core.tasks import process_rag_query
from app.services.ingest import ingest_document
from app.api.auth import verify_api_key

# Production standard logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-migrate database tables
logger.info("Verifying database schema...")
# SQLAlchemy requires models to be imported before this execution
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise RAG API Gateway",
    description="Event-driven API Gateway routing requests to Celery background workers and Qdrant Vector DB.",
    version="1.0.0"
)

@app.get("/", tags=["System"])
async def health_check():
    return {"status": "online", "service": "API Gateway", "database_synced": True}

@app.post("/ingest", response_model=IngestResponse, tags=["Knowledge Base"], dependencies=[Depends(verify_api_key)])
def upload_document(request: IngestRequest):
    """
    Ingests raw text into the Qdrant Vector Database.
    Secured endpoint requiring valid X-API-Key header.
    """
    try:
        chunks_count = ingest_document(text_content=request.text, metadata=request.metadata)
        return IngestResponse(
            status="success",
            chunks_inserted=chunks_count,
            message="Document successfully embedded and stored in Qdrant."
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

@app.post("/ask", response_model=TaskResponse, status_code=202, tags=["RAG Engine"], dependencies=[Depends(verify_api_key)])
async def submit_query(request: QueryRequest):
    """
    Receives a query, validates it, and dispatches it to the Celery worker queue.
    Secured endpoint requiring valid X-API-Key header.
    """
    try:
        task = process_rag_query.delay(
            query=request.query, 
            department=request.department,
            callback_url=str(request.callback_url) if request.callback_url else None
        )
        
        logger.info(f"Task dispatched to worker queue. Task ID: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="processing",
            message="Query accepted and dispatched to background worker."
        )
    except Exception as e:
        logger.error(f"Failed to dispatch task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal message broker error.")