"""
Text chunking utilities for RAG-ready document processing.
"""
from typing import List


def chunk_text(
    text: str, 
    chunk_size: int = 300, 
    overlap: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks based on word count.
    
    This is a simple word-based chunking algorithm that splits text into
    fixed-size chunks with overlap to preserve context between chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk (default: 300)
        overlap: Number of overlapping words between chunks (default: 50)
    
    Returns:
        List of text chunks
    
    Example:
        >>> text = "word " * 500
        >>> chunks = chunk_text(text, chunk_size=300, overlap=50)
        >>> len(chunks)  # Should be 3 chunks
        3
        
        >>> # First chunk: words 0-299
        >>> # Second chunk: words 250-549 (50 word overlap)
        >>> # Third chunk: words 450-499 (remaining words)
    """
    # Handle empty or whitespace-only text
    if not text or not text.strip():
        return []
    
    # Split by whitespace to get words
    words = text.split()
    
    # If text is shorter than chunk_size, return as single chunk
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        # Get chunk_size words starting from start
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        
        # Move start forward by (chunk_size - overlap)
        # This creates overlap between consecutive chunks
        start += (chunk_size - overlap)
        
        # Stop if we've processed all words
        if end >= len(words):
            break
    
    return chunks
