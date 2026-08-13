import os
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_llama_response(prompt: str) -> dict:
    """
    Calls the Groq API (Llama-3) with enterprise-grade retry mechanisms.
    If the API rate limits or fails, it will exponentially back off and retry up to 3 times.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a precise enterprise AI assistant. Rely strictly on provided context."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }

    logger.info("Transmitting request to Groq Llama-3 cluster...")
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        
        return {
            "answer": content,
            "tokens": tokens_used
        }