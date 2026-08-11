import os
import logging
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Enterprise default fallback for isolated environments
ENTERPRISE_API_KEY = os.getenv("ENTERPRISE_API_KEY", "b2b-secret-key-2026")

# Setting auto_error=False allows us to bypass FastAPI's default 403 
# and manually enforce a standard 401 Unauthorized error with logging.
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

# Enterprise Fix: Typed as Optional[str] to prevent Pydantic 422 Validation Errors
def verify_api_key(api_key: Optional[str] = Security(api_key_header_scheme)):
    """
    Zero-Trust Gateway Validation.
    Rejects any request without the exact X-API-Key header match.
    """
    if not api_key or api_key != ENTERPRISE_API_KEY:
        logger.warning("Intrusion attempt blocked: Missing or invalid API Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or Missing Enterprise API Key",
        )
    return api_key