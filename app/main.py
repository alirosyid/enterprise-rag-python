from fastapi import FastAPI, HTTPException, Depends
import logging
from celery.result import AsyncResult
from prometheus_client import make_asgi_app, Counter, Histogram
from app.db.session import engine, Base
from app.db.models import FinOpsLog
from app.api.schemas import QueryRequest, TaskResponse, IngestRequest, IngestResponse
from app.core.celery_app import celery_app
from app.core.tasks import process_rag_query
from app.services.ingest import ingest_document
from app.api.auth import verify_api_key

# Production standard logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-migrate database tables
logger.info("Verifying database schema...")
Base.metadata.create_all(bind=engine)

# ==========================================
# ENTERPRISE OBSERVABILITY (PROMETHEUS)
# ==========================================
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'API request latency', ['endpoint'])

app = FastAPI(
    title="Enterprise RAG API Gateway",
    description="Event-driven API Gateway routing requests to Celery background workers and Qdrant Vector DB.",
    version="1.0.0"
)

# Ekspos endpoint /metrics untuk dipantau oleh Grafana
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
# ==========================================

@app.get("/", tags=["System"])
async def health_check():
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    return {"status": "online", "service": "API Gateway", "database_synced": True}

@app.post("/ingest", response_model=IngestResponse, tags=["Knowledge Base"], dependencies=[Depends(verify_api_key)])
def upload_document(request: IngestRequest):
    REQUEST_COUNT.labels(method='POST', endpoint='/ingest').inc()
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
    REQUEST_COUNT.labels(method='POST', endpoint='/ask').inc()
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

@app.get("/tasks/{task_id}", tags=["RAG Engine"], dependencies=[Depends(verify_api_key)])
async def get_task_status(task_id: str):
    REQUEST_COUNT.labels(method='GET', endpoint='/tasks/{task_id}').inc()
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "pending", "message": "Task is queued or processing."}
    elif task_result.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": task_result.result}
    elif task_result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task_result.info)}
    else:
        return {"task_id": task_id, "status": task_result.state.lower()}