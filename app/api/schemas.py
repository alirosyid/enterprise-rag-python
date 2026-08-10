from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The user query to be processed by the RAG engine.")
    department: Optional[str] = Field("general", description="Business department for FinOps tracking.")
    callback_url: Optional[HttpUrl] = Field(None, description="Optional webhook URL for asynchronous result delivery to n8n/external APIs.")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str