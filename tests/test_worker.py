import pytest
from unittest.mock import patch, MagicMock
from app.main import app  # Ensures DB tables are created prior to test
from app.core.tasks import process_rag_query
from app.db.models import FinOpsLog
from app.db.session import SessionLocal

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_success(mock_llm):
    """
    Validates the core Celery worker logic natively.
    Bypasses Celery decorator quirks by calling the original unwrapped function via .run()
    """
    mock_llm.return_value = {"answer": "Enterprise backend response", "tokens": 150}
    
    # 1. Create a bulletproof Mock for the bound 'self' object
    mock_self = MagicMock()
    mock_self.request.id = "simulated-celery-task-id-999"
    
    # 2. Call .run() to execute the underlying python function directly, 
    # bypassing the broken eager execution context entirely.
    result = process_rag_query.run(
        mock_self,
        query="Test high-frequency data extraction", 
        department="engineering",
        callback_url=None
    )
    
    # 3. Verify Output Task
    assert result["status"] == "success"
    assert result["answer"] == "Enterprise backend response"
    assert result["tokens_burned"] == 150
    
    # 4. Verify Stateful Database FinOps Logging
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
    Ensures the worker correctly handles LLM failures and triggers native Celery Retry.
    """
    mock_llm.side_effect = Exception("Groq API Timeout")
    
    mock_self = MagicMock()
    mock_self.request.id = "simulated-celery-task-id-888"
    # Simulate the retry mechanism throwing an exception to halt execution
    mock_self.retry.side_effect = Exception("CeleryRetryTriggered")
    
    with pytest.raises(Exception, match="CeleryRetryTriggered"):
        process_rag_query.run(
            mock_self,
            query="Test failure handling", 
            department="engineering",
            callback_url=None
        )
    
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == "simulated-celery-task-id-888").first()
    
    assert log_entry is not None
    assert log_entry.status == "failed"
    
    db.close()