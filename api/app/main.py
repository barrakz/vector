"""
FastAPI application for vector embeddings demo with pgvector.
Now using LOCAL sentence-transformers model (no OpenAI, no API key needed).
"""
import os
from typing import Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

import logging
from app.db import get_db_connection, init_database
from app.chunking import chunk_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load the local sentence-transformers model once at startup
# Using paraphrase-multilingual-MiniLM-L12-v2 (384-dimensional, 50+ languages including Polish)
logger.info("Loading sentence-transformers model: paraphrase-multilingual-MiniLM-L12-v2...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
logger.info("Model loaded successfully!")


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding using local sentence-transformers model.
    Returns a list of 384 floats.
    """
    embedding = model.encode(text)
    return embedding.tolist()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the FastAPI app.
    Initialize database on startup.
    """
    logger.info("Starting up: initializing database...")
    init_database()
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vector Embeddings Demo (Local Model)",
    description="Demo API using LOCAL sentence-transformers for embeddings (no OpenAI). Semantic search with pgvector and JSONB metadata.",
    version="2.0.0",
    lifespan=lifespan
)


# Request/Response models
class IngestRequest(BaseModel):
    title: str
    body: str
    metadata: Optional[dict[str, Any]] = {}


class IngestResponse(BaseModel):
    status: str
    document_id: int
    chunks_inserted: int


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    title: str
    body: str
    metadata: Optional[dict[str, Any]]
    distance: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Vector embeddings API is running"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a document with RAG-ready chunking: generate embeddings for text chunks and store in PostgreSQL.
    
    - Chunks the document body into ~300 word fragments with 50 word overlap
    - Uses sentence-transformers to generate embedding for each chunk
    - Stores chunks with embeddings in pgvector (384 dimensions)
    - Stores document metadata in documents table
    - Returns document_id and number of chunks created
    """
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if document with this URL already exists
        if request.metadata and 'url' in request.metadata:
            cursor.execute(
                """
                SELECT id FROM documents 
                WHERE metadata->>'url' = %s;
                """,
                (request.metadata['url'],)
            )
            existing = cursor.fetchone()
            if existing:
                # Count existing chunks for this document
                cursor.execute(
                    "SELECT COUNT(*) FROM chunks WHERE document_id = %s;",
                    (existing[0],)
                )
                chunk_count = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                logger.info(f"Document with URL '{request.metadata['url']}' already exists (ID: {existing[0]}). Skipping.")
                return IngestResponse(status="ok", document_id=existing[0], chunks_inserted=chunk_count)
        
        # Insert document record (without body - chunks will contain the text)
        logger.info(f"Ingesting document: '{request.title}' | Metadata: {request.metadata}")
        cursor.execute(
            """
            INSERT INTO documents (title, body, metadata, embedding)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (request.title, "", Jsonb(request.metadata), None)  # Empty body, no embedding for document
        )
        
        document_id = cursor.fetchone()[0]
        
        # Chunk the text
        chunks = chunk_text(request.body, chunk_size=300, overlap=50)
        logger.info(f"Document split into {len(chunks)} chunks")
        
        # Insert each chunk with its embedding
        chunks_inserted = 0
        for idx, chunk in enumerate(chunks):
            # Generate embedding for this chunk
            chunk_embedding = get_embedding(chunk)
            
            # Insert chunk
            cursor.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, title, body, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (document_id, idx, request.title, chunk, Jsonb(request.metadata), chunk_embedding)
            )
            chunks_inserted += 1
        
        cursor.close()
        conn.close()
        
        logger.info(f"Document inserted successfully with ID: {document_id}, chunks: {chunks_inserted}")
        return IngestResponse(status="ok", document_id=document_id, chunks_inserted=chunks_inserted)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@app.get("/search", response_model=SearchResponse)
async def search_documents(q: str, limit: int = 5):
    """
    Semantic search on text chunks: find most relevant chunks using vector similarity.
    
    - Generates embedding for the query text using LOCAL model
    - Searches chunks table (not documents) using L2 distance
    - Returns most similar chunks with document context
    - Perfect for RAG: returns precise, relevant text fragments
    """
    try:
        # Generate embedding for the search query using local model
        logger.info(f"Searching for: '{q}' | Limit: {limit}")
        query_embedding = get_embedding(q)
        
        # Connect to database and perform similarity search on chunks
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for similar chunks using L2 distance
        # The <-> operator calculates L2 distance between vectors
        # Lower distance = more similar
        cursor.execute(
            """
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.chunk_index,
                c.title,
                c.body,
                c.metadata,
                c.embedding <-> %s::vector AS distance
            FROM chunks c
            ORDER BY c.embedding <-> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, limit)
        )
        
        rows = cursor.fetchall()
        
        # Build results
        results = []
        for row in rows:
            results.append(SearchResult(
                chunk_id=row[0],
                document_id=row[1],
                chunk_index=row[2],
                title=row[3],
                body=row[4],
                metadata=row[5],
                distance=row[6]
            ))
        
        cursor.close()
        conn.close()
        
        logger.info(f"Search completed. Found {len(results)} chunk results.")
        return SearchResponse(query=q, results=results)
        
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")


@app.get("/documents")
async def list_documents():
    """
    List all documents in the database (useful for debugging).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, body, metadata
            FROM documents
            ORDER BY id DESC;
        """)
        
        rows = cursor.fetchall()
        
        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "title": row[1],
                "body": row[2],
                "metadata": row[3]
            })
        
        cursor.close()
        conn.close()
        
        return {"documents": documents, "count": len(documents)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")
