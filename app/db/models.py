from sqlalchemy import Column, String, Integer, Float, DateTime
from datetime import datetime
from app.db.session import Base

class FinOpsLog(Base):
    """
    Enterprise Data Model for tracking LLM inference costs and worker states.
    Ensures every async Celery task has an immutable audit trail.
    """
    __tablename__ = "finops_logs"

    task_id = Column(String, primary_key=True, index=True)
    query_type = Column(String, index=True, default="rag_generation")
    status = Column(String, default="pending")
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    
    # Enterprise Fix: Using utcnow (naive datetime) prevents fatal ValueError 
    # crashes in SQLite during CI/CD automated testing.
    created_at = Column(DateTime, default=datetime.utcnow)