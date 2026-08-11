import pytest
from unittest.mock import patch, MagicMock
# Mengimpor app untuk menjamin Base.metadata.create_all() tereksekusi sebelum pengujian
from app.main import app 
from app.core.tasks import process_rag_query
from app.db.models import FinOpsLog
from app.db.session import SessionLocal

# Mock LLM engine untuk mencegah pembakaran token API nyata selama CI/CD berjalan
@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_success(mock_llm):
    """
    Validates the core Celery worker logic in total isolation.
    Ensures stateful FinOps logging and robust execution.
    """
    # 1. Setup Mock Data
    mock_llm.return_value = {"answer": "Enterprise backend response", "tokens": 150}
    
    # 2. Membajak objek 'self' Celery untuk mengeksekusi fungsi tanpa Redis broker
    mock_self = MagicMock()
    mock_self.request.id = "simulated-celery-task-id-999"
    
    # 3. Eksekusi worker secara langsung (Sinkron untuk pengujian internal)
    result = process_rag_query(
        mock_self, 
        query="Test B2B pipeline integration", 
        department="engineering",
        callback_url=None
    )
    
    # 4. Verifikasi Output Task
    assert result["status"] == "success"
    assert result["answer"] == "Enterprise backend response"
    assert result["tokens_burned"] == 150
    
    # 5. Verifikasi Stateful Database FinOps Logging
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == "simulated-celery-task-id-999").first()
    
    assert log_entry is not None
    assert log_entry.query_type == "rag_generation"
    assert log_entry.status == "success"
    assert log_entry.total_tokens == 150
    assert log_entry.cost_usd == 0.015  # 150 tokens * $0.0001
    
    db.close()

@patch("app.core.tasks.generate_llama_response")
def test_process_rag_query_failure(mock_llm):
    """
    Ensures the worker correctly handles LLM failures, logs the error state,
    and triggers the Celery retry mechanism.
    """
    # Memaksa kegagalan/timeout pada Groq API
    mock_llm.side_effect = Exception("Groq API Timeout")
    
    mock_self = MagicMock()
    mock_self.request.id = "simulated-celery-task-id-888"
    mock_self.retry.side_effect = Exception("RetryTriggered")
    
    # Worker harus menangkap kegagalan LLM dan memicu Retry
    with pytest.raises(Exception, match="RetryTriggered"):
        process_rag_query(
            mock_self, 
            query="Test failure handling", 
            department="engineering",
            callback_url=None
        )
    
    # Verifikasi bahwa FinOps log merekam status kegagalan tersebut
    db = SessionLocal()
    log_entry = db.query(FinOpsLog).filter(FinOpsLog.task_id == "simulated-celery-task-id-888").first()
    
    assert log_entry is not None
    assert log_entry.status == "failed"
    
    db.close()