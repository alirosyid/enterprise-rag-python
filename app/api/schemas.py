from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The user query to be processed by the RAG engine.")
    department: Optional[str] = Field("general", description="Business department for FinOps tracking.")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str