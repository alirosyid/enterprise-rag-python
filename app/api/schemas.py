from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="The user query to be processed by the RAG engine.")
    department: Optional[str] = Field("general", description="Business department for FinOps tracking.")
    callback_url: Optional[HttpUrl] = Field(None, description="Optional webhook URL for asynchronous result delivery to external systems.")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class IngestRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Raw text content to be embedded and stored in the vector database.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata tags for semantic filtering.")

class IngestResponse(BaseModel):
    status: str
    chunks_inserted: int
    message: str