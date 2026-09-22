import os
import json
import logging
import redis
import numpy as np
from numpy.linalg import norm
from app.services.ingest import get_embeddings_model

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=False)

CACHE_PREFIX = "rag_cache:"
DEFAULT_THRESHOLD = 0.95
DEFAULT_TTL = 86400  # 24 hours in seconds

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    denom = norm(vec1) * norm(vec2)
    if denom == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / denom)

def get_cached_response(query: str, threshold: float = DEFAULT_THRESHOLD) -> dict | None:
    """
    Scans cached query vectors in Redis and calculates similarity.
    Returns cached response dict on cache hit; None on cache miss.
    """
    try:
        model = get_embeddings_model()
        query_vector = np.array(model.embed_query(query), dtype=np.float32)

        keys = redis_client.keys(f"{CACHE_PREFIX}*")
        for key in keys:
            cached_data_raw = redis_client.get(key)
            if not cached_data_raw:
                continue

            cached_payload = json.loads(cached_data_raw.decode("utf-8"))
            cached_vector = np.array(cached_payload["vector"], dtype=np.float32)

            similarity = compute_cosine_similarity(query_vector, cached_vector)
            if similarity >= threshold:
                logger.info(f"Semantic Cache HIT (Similarity: {similarity:.4f}) for query: '{query}'")
                return {
                    "answer": cached_payload["answer"],
                    "tokens": 0,  # 0 tokens burned on cache hit
                    "cached": True,
                    "similarity": round(similarity, 4)
                }

        logger.info(f"Semantic Cache MISS for query: '{query}'")
        return None

    except Exception as e:
        logger.error(f"Semantic Cache lookup error: {str(e)}")
        return None

def set_cached_response(query: str, answer: str, ttl: int = DEFAULT_TTL):
    """
    Stores the query vector and answer in Redis with an expiration TTL.
    """
    try:
        model = get_embeddings_model()
        query_vector = model.embed_query(query)

        cache_key = f"{CACHE_PREFIX}{hash(query)}"
        payload = {
            "query": query,
            "vector": query_vector,
            "answer": answer
        }

        redis_client.setex(cache_key, ttl, json.dumps(payload))
        logger.info(f"Successfully cached semantic response for key: {cache_key}")
    except Exception as e:
        logger.error(f"Failed to save semantic cache: {str(e)}")