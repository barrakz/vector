-- Migration: Add chunks table for RAG-ready chunking
-- This migration creates the chunks table for storing text fragments with embeddings
-- Run this migration after the initial documents table is created

-- Create chunks table
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

-- Create indexes for chunks
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);
CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON chunks USING gin(metadata);

-- Note: Vector index disabled for small datasets (< 100 chunks)
-- For production with large datasets, uncomment:
-- CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
-- ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
