import logging
import httpx
from celery import shared_task
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import FinOpsLog
from app.services.llm_engine import generate_llama_response

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_rag_query", max_retries=2)
def process_rag_query(self, query: str, department: str, callback_url: str = None):
    """
    Executes the RAG pipeline. Logs state to DB, processes via LLM, 
    and sends a webhook callback to n8n (if URL is provided).
    """
    db = SessionLocal()
    task_id = self.request.id
    
    # ENTERPRISE FIX: Menggunakan db.merge() untuk Upsert alih-alih db.add()
    # Jika API Gateway sudah membuat task_id ini, Celery hanya akan meniban/meng-update-nya 
    # tanpa memicu error Duplicate Key dari PostgreSQL.
    finops_record = FinOpsLog(
        task_id=task_id,
        query_type="rag_generation",
        status="processing"
    )
    finops_record = db.merge(finops_record) 
    db.commit()
    
    try:
        logger.info(f"Task {task_id}: Executing vector search for query: {query}")
        context = "Simulated contextual data from Vector DB."
        
        augmented_prompt = f"Context: {context}\n\nQuery: {query}"
        llm_result = generate_llama_response(augmented_prompt)
        
        finops_record.status = "success"
        finops_record.total_tokens = llm_result["tokens"]
        finops_record.cost_usd = llm_result["tokens"] * 0.0001 
        db.commit()
        
        payload = {
            "status": "success", 
            "task_id": task_id,
            "answer": llm_result["answer"], 
            "tokens_burned": llm_result["tokens"]
        }
        
        # Enterprise Callback Engine: Push results back to n8n webhook
        if callback_url:
            with httpx.Client() as client:
                client.post(callback_url, json=payload)
                logger.info(f"Successfully transmitted callback to {callback_url}")
                
        return payload

    except Exception as e:
        finops_record.status = "failed"
        db.commit()
        logger.error(f"Task {task_id} failed: {str(e)}")
        
        if callback_url:
            with httpx.Client() as client:
                client.post(callback_url, json={"status": "failed", "task_id": task_id, "error": str(e)})
                
        raise self.retry(exc=e, countdown=10)
        
    finally:
        db.close()