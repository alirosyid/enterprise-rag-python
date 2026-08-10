from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .session import Base

class FinOpsLog(Base):
    __tablename__ = "finops_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Tracking ID untuk Celery Worker (Asynchronous tracking)
    task_id = Column(String, index=True, nullable=True)
    
    # Metadata Eksekusi
    query_type = Column(String, index=True)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    
    # Status Pipeline (pending, success, failed)
    status = Column(String, default="pending")
    
    # Timestamp Otomatis
    created_at = Column(DateTime(timezone=True), server_default=func.now())