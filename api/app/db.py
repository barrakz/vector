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
    Initialize the database: create pgvector extension, create tables, and create indexes.
    This runs once when the FastAPI app starts.
    
    NOTE: This version uses vector(384) for sentence-transformers/all-MiniLM-L6-v2
    Creates both 'documents' table (for metadata) and 'chunks' table (for RAG retrieval)
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
        
        # Create chunks table for RAG-ready chunking
        print("Creating chunks table if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                metadata JSONB,
                embedding vector(384),
                UNIQUE(document_id, chunk_index)
            );
        """)
        
        # NOTE: IVFFlat index disabled for small datasets (< 100 documents/chunks)
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
        # cursor.execute("""
        #     CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        #     ON chunks
        #     USING ivfflat (embedding vector_l2_ops)
        #     WITH (lists = 100);
        # """)
        
        # Create GIN index on JSONB metadata for fast JSON queries
        print("Creating JSONB indexes if not exist...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS documents_metadata_idx
            ON documents
            USING gin (metadata);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS chunks_metadata_idx
            ON chunks
            USING gin (metadata);
        """)
        
        # Create index on chunks.document_id for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS chunks_document_id_idx
            ON chunks(document_id);
        """)
        
        # Create players table for Player Profile Generator
        print("Creating players table if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                summary TEXT NOT NULL,
                position VARCHAR(100) NOT NULL,
                clubs TEXT[] NOT NULL DEFAULT '{}',
                characteristics TEXT NOT NULL,
                strengths TEXT NOT NULL,
                weaknesses TEXT NOT NULL,
                estimated_current_form TEXT NOT NULL,
                team VARCHAR(255),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            );
        """)
        
        # Create indexes for players table
        print("Creating players indexes if not exist...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_players_team ON players(team);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_players_metadata ON players USING gin(metadata);
        """)
        
        # Create trigger for auto-updating updated_at
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_players_updated_at ON players;
        """)
        cursor.execute("""
            CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        print("Database initialization complete! Using vector(384) for sentence-transformers.")
        print("Tables created: documents, chunks, players")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
