import pytest
from unittest.mock import patch
from celery.exceptions import Retry
from app.main import app  # Ensures DB tables are created prior to test
from app.core.tasks import process_rag_query
from app.db.models import FinOpsLog
from app.db.session import SessionLocal

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_success(mock_llm):
    """
    Validates the core Celery worker logic natively using eager execution.
    Ensures stateful FinOps logging without hacking internal worker objects.
    """
    # 1. Setup Mock Data for Llama-3 extraction
    mock_llm.return_value = {"answer": "Enterprise backend response", "tokens": 150}
    
    # 2. Execute natively via .delay() (Runs synchronously due to task_always_eager=True)
    task = process_rag_query.delay(
        query="Test high-frequency data extraction", 
        department="engineering",
        callback_url=None
    )
    
    # 3. Retrieve EagerResult
    result = task.result
    
    # 4. Verify Output Task
    assert result["status"] == "success"
    assert result["answer"] == "Enterprise backend response"
    assert result["tokens_burned"] == 150
    
    # 5. Verify Stateful Database FinOps Logging using the native Celery Task ID
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == task.id).first()
    
    assert log_entry is not None
    assert log_entry.query_type == "rag_generation"
    assert log_entry.status == "success"
    assert log_entry.total_tokens == 150
    assert log_entry.cost_usd == 0.015 
    
    db.close()

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_failure(mock_llm):
    """
    Ensures the worker correctly handles LLM failures, triggers native Celery Retry,
    and logs the error state.
    """
    # Force a timeout on the Groq API
    mock_llm.side_effect = Exception("Groq API Timeout")
    
    # Eager execution with task_eager_propagates=True natively throws the Retry exception
    with pytest.raises(Retry):
        process_rag_query.delay(
            query="Test failure handling", 
            department="engineering",
            callback_url=None
        )
    
    # Verify the FinOps log recorded the failure state
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.status == "failed").first()
    
    assert log_entry is not None
    
    db.close()