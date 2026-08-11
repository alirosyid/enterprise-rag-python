import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "enterprise_knowledge_base"

def init_qdrant_client():
    """
    Initializes the Qdrant client and securely creates the vector collection
    only if it does not already exist. Prevents 409 Conflict crashes on reboot.
    """
    logger.info(f"Connecting to Qdrant Vector DB at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        # Enterprise Fix: Context-aware collection initialization
        if not client.collection_exists(collection_name=COLLECTION_NAME):
            logger.info(f"Creating new Qdrant collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=384,  # Matching the dimension of all-MiniLM-L6-v2
                    distance=models.Distance.COSINE
                )
            )
        else:
            logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists. Skipping creation.")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
        
    return client

# Singleton instantiation
qdrant_db = init_qdrant_client()