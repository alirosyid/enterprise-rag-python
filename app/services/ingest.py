import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client.http.models import PointStruct
from app.services.qdrant_engine import qdrant_db, COLLECTION_NAME
import uuid

logger = logging.getLogger(__name__)

# Initialize local embedding model (runs on CPU/RAM, no API cost)
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

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

    # 2. Generate Embeddings
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = embeddings_model.embed_documents(chunks)

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