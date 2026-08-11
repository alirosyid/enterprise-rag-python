import logging
# Enterprise Fix: Updated import path to match LangChain's new modular architecture
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http.models import PointStruct
from app.services.qdrant_engine import qdrant_db, COLLECTION_NAME
import uuid

logger = logging.getLogger(__name__)

# Enterprise Fix: Lazy Loading (Singleton) for ML Models
# Do NOT initialize ML models at the module level. It crashes CI/CD pipelines
# due to Out-Of-Memory (OOM) errors and blocks FastAPI startup.
_embeddings_model = None

def get_embeddings_model():
    """
    Singleton pattern to ensure the ML model is only loaded into memory 
    the first time an ingestion request is actually made.
    """
    global _embeddings_model
    if _embeddings_model is None:
        logger.info("Initializing HuggingFace Embedding Model into memory...")
        # Local import to prevent downloading weights during module initialization
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings_model

def ingest_document(text_content: str, metadata: dict = None) -> int:
    """
    Processes raw text, chunks it, generates embeddings, and stores them in Qdrant.
    Returns the number of chunks successfully ingested.
    """
    if not text_content.strip():
        raise ValueError("Document content cannot be empty.")

    logger.info("Starting document ingestion process...")

    # 1. Chunking the document
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_text(text_content)
    
    if not chunks:
        return 0

    # 2. Lazy load model and generate Embeddings
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    model = get_embeddings_model()
    embeddings = model.embed_documents(chunks)

    # 3. Prepare payload for Qdrant
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())
        payload = metadata.copy() if metadata else {}
        payload["text"] = chunk
        payload["chunk_index"] = i
        
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
        )

    # 4. Upsert to Vector Database
    qdrant_db.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    logger.info(f"Successfully ingested {len(points)} vectors into {COLLECTION_NAME}.")
    return len(points)