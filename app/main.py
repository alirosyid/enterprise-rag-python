from fastapi import FastAPI, HTTPException, BackgroundTasks
import logging
from app.db.session import engine, Base
from app.db import models 
from app.api.schemas import QueryRequest, TaskResponse
from app.core.tasks import process_rag_query

# Production standard logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-migrate database tables
logger.info("Verifying database schema...")
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise RAG API Gateway",
    description="Event-driven API Gateway routing requests to Celery background workers.",
    version="1.0.0"
)

@app.get("/", tags=["System"])
async def health_check():
    return {"status": "online", "service": "API Gateway", "database_synced": True}

@app.post("/ask", response_model=TaskResponse, status_code=202, tags=["RAG Engine"])
async def submit_query(request: QueryRequest):
    """
    Receives a query, validates it, and dispatches it to the Celery worker queue.
    Returns a 202 Accepted with a task_id for asynchronous polling.
    """
    try:
        # Dispatch task to Celery worker
        task = process_rag_query.delay(query=request.query, department=request.department)
        
        logger.info(f"Task dispatched to worker queue. Task ID: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="processing",
            message="Query accepted and dispatched to background worker."
        )
    except Exception as e:
        logger.error(f"Failed to dispatch task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal message broker error.")

@app.get("/status/{task_id}", tags=["System"])
async def get_task_status(task_id: str):
    """
    Retrieves the current status of a background task from the Celery backend.
    """
    from app.core.celery_app import celery_app
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        return {"task_id": task_id, "status": "pending"}
    elif task_result.state == 'SUCCESS':
        return {"task_id": task_id, "status": "success", "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"task_id": task_id, "status": "failed", "error": str(task_result.info)}
    else:
        return {"task_id": task_id, "status": task_result.state}