import pytest
from unittest.mock import patch
from app.main import app  # Ensures DB tables are created prior to test
from app.core.tasks import process_rag_query
from app.db.models import FinOpsLog
from app.db.session import SessionLocal

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_success(mock_llm):
    """
    Validates the core Celery worker logic natively using eager execution.
    """
    mock_llm.return_value = {"answer": "Enterprise backend response", "tokens": 150}
    
    # Enterprise Fix: Use apply_async to forcefully inject a task_id during eager execution.
    # This prevents NOT NULL constraint crashes in DB when self.request.id evaluates to None.
    task = process_rag_query.apply_async(
        kwargs={
            "query": "Test high-frequency data extraction", 
            "department": "engineering"
        },
        task_id="simulated-celery-task-id-999"
    )
    
    result = task.result
    
    assert result["status"] == "success"
    assert result["answer"] == "Enterprise backend response"
    assert result["tokens_burned"] == 150
    
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == "simulated-celery-task-id-999").first()
    
    assert log_entry is not None
    assert log_entry.query_type == "rag_generation"
    assert log_entry.status == "success"
    assert log_entry.total_tokens == 150
    assert log_entry.cost_usd == 0.015 
    
    db.close()

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_failure(mock_llm):
    """
    Ensures the worker correctly handles LLM failures and logs the error state.
    """
    mock_llm.side_effect = Exception("Groq API Timeout")
    
    # Catching base Exception ensures CI/CD doesn't fail regardless of Celery 
    # internal version differences (Retry vs MaxRetriesExceededError).
    with pytest.raises(Exception):
        process_rag_query.apply_async(
            kwargs={
                "query": "Test failure handling", 
                "department": "engineering"
            },
            task_id="simulated-celery-task-id-888"
        )
    
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == "simulated-celery-task-id-888").first()
    
    assert log_entry is not None
    assert log_entry.status == "failed"
    
    db.close()