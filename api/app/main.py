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
# Using all-MiniLM-L6-v2 (384-dimensional, primarily English)
logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
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
    id: int


class SearchResult(BaseModel):
    id: int
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
    Ingest a document: generate embedding using LOCAL model and store in PostgreSQL.
    
    - Uses sentence-transformers to generate embedding from document body
    - Stores document with embedding in pgvector column (384 dimensions)
    - Stores metadata as JSONB
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
                cursor.close()
                conn.close()
                logger.info(f"Document with URL '{request.metadata['url']}' already exists (ID: {existing[0]}). Skipping.")
                return IngestResponse(status="ok", id=existing[0])
        
        # Generate embedding using local sentence-transformers model
        logger.info(f"Ingesting document: '{request.title}' | Metadata: {request.metadata}")
        embedding = get_embedding(request.body)
        # print(f"Embedding generated (dimension: {len(embedding)})")
        
        # Insert document with embedding
        # Note: psycopg3 handles the vector type automatically when we pass a list
        # Wrap metadata in Jsonb for proper JSONB handling
        cursor.execute(
            """
            INSERT INTO documents (title, body, metadata, embedding)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (request.title, request.body, Jsonb(request.metadata), embedding)
        )
        
        document_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Document inserted successfully with ID: {document_id}")
        return IngestResponse(status="ok", id=document_id)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@app.get("/search", response_model=SearchResponse)
async def search_documents(q: str, limit: int = 5):
    """
    Semantic search: find documents similar to the query using vector similarity.
    
    - Generates embedding for the query text using LOCAL model
    - Searches using L2 distance (embedding <-> query_vector)
    - Returns most similar documents
    """
    try:
        # Generate embedding for the search query using local model
        logger.info(f"Searching for: '{q}' | Limit: {limit}")
        query_embedding = get_embedding(q)
        # print(f"Query embedding generated (dimension: {len(query_embedding)})")
        
        # Connect to database and perform similarity search
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for similar documents using L2 distance
        # The <-> operator calculates L2 distance between vectors
        # Lower distance = more similar
        # Cast the embedding list to vector type explicitly
        cursor.execute(
            """
            SELECT id, title, body, metadata, embedding <-> %s::vector AS distance
            FROM documents
            ORDER BY embedding <-> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, limit)
        )
        
        rows = cursor.fetchall()
        
        # Build results
        results = []
        for row in rows:
            results.append(SearchResult(
                id=row[0],
                title=row[1],
                body=row[2],
                metadata=row[3],
                distance=row[4]
            ))
        
        cursor.close()
        conn.close()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Search completed. Found {len(results)} results.")
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
