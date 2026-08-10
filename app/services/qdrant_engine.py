import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "enterprise_knowledge_base"

# Enterprise Check: Detect if running inside an automated testing environment
IS_TESTING = os.getenv("TESTING_ENV", "false").lower() == "true"

def init_qdrant_client() -> QdrantClient:
    """
    Initializes connection to the Qdrant Vector Database.
    Automatically degrades to an ephemeral in-memory database during CI/CD testing.
    """
    try:
        if IS_TESTING:
            logger.info("Testing environment detected. Booting Qdrant in memory mode.")
            # :memory: runs purely in RAM, requires no server, perfect for Pytest
            client = QdrantClient(":memory:")
        else:
            logger.info(f"Connecting to live Qdrant server at {QDRANT_HOST}:{QDRANT_PORT}")
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Check if collection exists to avoid recreation errors
        collections = client.get_collections().collections
        exists = any(col.name == COLLECTION_NAME for col in collections)
        
        if not exists:
            logger.info(f"Initializing new Qdrant collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        else:
            logger.info(f"Connected to existing Qdrant collection: {COLLECTION_NAME}")
            
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant Vector DB: {str(e)}")
        raise

# Initialize connection at startup
qdrant_db = init_qdrant_client()