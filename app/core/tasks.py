import logging
from celery import shared_task
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import FinOpsLog
from app.services.llm_engine import generate_llama_response

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_rag_query", max_retries=2)
def process_rag_query(self, query: str, department: str):
    """
    Background Celery task that executes the RAG pipeline.
    It logs state to PostgreSQL, calls LLM, and updates FinOps metrics.
    """
    db = SessionLocal()
    task_id = self.request.id
    
    # 1. Stateful Logging: Initialize task in PostgreSQL
    finops_record = FinOpsLog(
        task_id=task_id,
        query_type="rag_generation",
        status="processing"
    )
    db.add(finops_record)
    db.commit()
    
    try:
        # 2. Vector Search (Placeholder for Qdrant integration coming next)
        logger.info(f"Task {task_id}: Executing vector search for query: {query}")
        context = "Simulated contextual data from Vector DB."
        
        # 3. LLM Generation via Groq API
        augmented_prompt = f"Context: {context}\n\nQuery: {query}"
        llm_result = generate_llama_response(augmented_prompt)
        
        # 4. Update FinOps Logging (Success)
        finops_record.status = "success"
        finops_record.total_tokens = llm_result["tokens"]
        # Dummy cost calculation: $0.0001 per token for example purposes
        finops_record.cost_usd = llm_result["tokens"] * 0.0001 
        db.commit()
        
        return {"status": "success", "answer": llm_result["answer"], "tokens_burned": llm_result["tokens"]}

    except Exception as e:
        # 5. Update FinOps Logging (Failed)
        finops_record.status = "failed"
        db.commit()
        logger.error(f"Task {task_id} failed: {str(e)}")
        raise self.retry(exc=e, countdown=10)
        
    finally:
        db.close()