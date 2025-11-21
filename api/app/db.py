"""
Database connection helper for PostgreSQL with pgvector.
"""
import os
import psycopg
from psycopg import sql


def get_db_connection():
    """
    Create and return a database connection using environment variables.
    """
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "app")
    db_user = os.getenv("DB_USER", "app")
    db_password = os.getenv("DB_PASSWORD", "app")
    
    connection_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"
    
    conn = psycopg.connect(connection_string, autocommit=True)
    return conn


def init_database():
    """
    Initialize the database: create pgvector extension, create table, and create indexes.
    This runs once when the FastAPI app starts.
    
    NOTE: This version uses vector(384) for sentence-transformers/all-MiniLM-L6-v2
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Enable pgvector extension
        print("Creating pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create documents table with vector(384) for sentence-transformers
        # Using IF NOT EXISTS to preserve data on restart
        print("Creating documents table if not exists (vector(384))...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                metadata JSONB,
                embedding vector(384)
            );
        """)
        
        # NOTE: IVFFlat index disabled for small datasets (< 100 documents)
        # IVFFlat requires significant data to work properly (~100+ documents)
        # For small datasets, brute-force search is more reliable
        # Uncomment below to enable IVFFlat for production with large datasets:
        #
        # print("Creating vector index if not exists...")
        # cursor.execute("""
        #     CREATE INDEX IF NOT EXISTS documents_embedding_idx
        #     ON documents
        #     USING ivfflat (embedding vector_l2_ops)
        #     WITH (lists = 100);
        # """)
        
        # Create GIN index on JSONB metadata for fast JSON queries
        print("Creating JSONB index if not exists...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS documents_metadata_idx
            ON documents
            USING gin (metadata);
        """)
        
        print("Database initialization complete! Using vector(384) for sentence-transformers.")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
