import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import logging

logger = logging.getLogger(__name__)

# Enterprise default fallback for isolated environments
ENTERPRISE_API_KEY = os.getenv("ENTERPRISE_API_KEY", "b2b-secret-key-2026")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key_header: str = Security(api_key_header)):
    """
    Zero-Trust Gateway Validation.
    Rejects any request without the exact X-API-Key header match.
    """
    if api_key_header != ENTERPRISE_API_KEY:
        logger.warning("Intrusion attempt blocked: Invalid API Key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid Enterprise API Key",
        )
    return api_key_header