import logging
import httpx
from celery import shared_task
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import FinOpsLog
from app.services.llm_engine import generate_llama_response
from app.services.semantic_cache import get_cached_response, set_cached_response

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_rag_query", max_retries=2)
def process_rag_query(self, query: str, department: str, callback_url: str = None):
    """
    Executes the RAG pipeline with Semantic Caching. Logs state to DB,
    checks Redis cache, executes LLM on cache miss, and handles callbacks.
    """
    db = SessionLocal()
    task_id = self.request.id
    
    finops_record = FinOpsLog(
        task_id=task_id,
        query_type="rag_generation",
        status="processing"
    )
    finops_record = db.merge(finops_record) 
    db.commit()
    
    try:
        logger.info(f"Task {task_id}: Checking Semantic Cache for query: {query}")
        
        # 1. Check Semantic Cache (Redis)
        cached_result = get_cached_response(query)
        if cached_result:
            finops_record.status = "success_cached"
            finops_record.total_tokens = 0
            finops_record.cost_usd = 0.0
            db.commit()

            payload = {
                "status": "success",
                "task_id": task_id,
                "answer": cached_result["answer"],
                "tokens_burned": 0,
                "cache_hit": True
            }
            
            if callback_url:
                with httpx.Client() as client:
                    client.post(callback_url, json=payload)
                    
            return payload

        # 2. Vector Search & LLM Inference on Cache Miss
        logger.info(f"Task {task_id}: Executing vector search for query: {query}")
        context = "Simulated contextual data from Vector DB."
        augmented_prompt = f"Context: {context}\n\nQuery: {query}"
        
        llm_result = generate_llama_response(augmented_prompt)
        
        # 3. Store Result in Semantic Cache
        set_cached_response(query=query, answer=llm_result["answer"])

        finops_record.status = "success"
        finops_record.total_tokens = llm_result["tokens"]
        finops_record.cost_usd = llm_result["tokens"] * 0.0001 
        db.commit()
        
        payload = {
            "status": "success", 
            "task_id": task_id,
            "answer": llm_result["answer"], 
            "tokens_burned": llm_result["tokens"],
            "cache_hit": False
        }
        
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