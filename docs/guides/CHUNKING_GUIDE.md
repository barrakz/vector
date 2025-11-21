# Text Chunking Guide

This document explains how text chunking works in the Vector Embeddings project and why it's essential for effective RAG (Retrieval-Augmented Generation).

## What is Text Chunking?

Text chunking is the process of splitting long documents into smaller, overlapping segments before generating embeddings. Instead of creating one embedding for an entire document, we create multiple embeddings for smaller chunks.

## Why Use Chunking?

### 1. **Better Semantic Precision**
- Long documents cover multiple topics
- Chunking allows each topic to have its own embedding
- Search results are more precise and relevant

### 2. **Improved Context Retrieval**
- When searching, you retrieve specific relevant sections
- Not the entire document (which may contain irrelevant information)
- Better for RAG applications where context matters

### 3. **Embedding Model Limitations**
- Most embedding models have token limits
- Very long texts may lose semantic meaning
- Chunking keeps each piece within optimal size

## How It Works in This Project

### Chunking Parameters

```python
chunk_size = 300    # words per chunk
overlap = 50        # overlapping words between chunks
```

### Example

Given a 500-word document:

```
Chunk 1: words 0-299     (300 words)
Chunk 2: words 250-549   (300 words, 50 overlap with Chunk 1)
Chunk 3: words 500-end   (remaining words)
```

### Why Overlap?

**Overlapping chunks preserve context across boundaries:**

- Without overlap: "...end of sentence" | "Beginning of next..."
- With overlap: "...end of sentence. Beginning of next..." | "Beginning of next sentence..."

This prevents losing meaning when a key concept spans chunk boundaries.

## Implementation Details

### Code Location

The chunking logic is in [`api/app/chunking.py`](../api/app/chunking.py):

```python
def chunk_text(
    text: str, 
    chunk_size: int = 300, 
    overlap: int = 50
) -> List[str]:
    """Split text into overlapping chunks based on word count."""
    # Implementation...
```

### Database Structure

Chunks are stored in a dedicated table:

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    body TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    UNIQUE(document_id, chunk_index)
);
```

**Key points:**
- Each chunk has its own embedding
- `chunk_index` preserves order
- `document_id` links chunks to parent document
- Cascade delete removes chunks when document is deleted

### Ingestion Flow

When you POST to `/ingest`:

1. **Document received** (title, body, metadata)
2. **Check for duplicates** (by URL in metadata)
3. **Chunk the text** using `chunk_text(body, 300, 50)`
4. **Generate embeddings** for each chunk
5. **Store in database**:
   - Parent document in `documents` table
   - Chunks in `chunks` table
6. **Return response** with `document_id` and `chunks_inserted`

### Search Flow

When you GET `/search?q=query`:

1. **Generate query embedding**
2. **Search chunks table** (not documents)
3. **Find most similar chunks** using vector distance
4. **Return results** with chunk content and metadata

## Adjusting Chunking Parameters

You can modify chunking behavior in [`api/app/main.py`](../api/app/main.py):

```python
# Current default
chunks = chunk_text(request.body, chunk_size=300, overlap=50)

# For shorter chunks (more precise, more chunks)
chunks = chunk_text(request.body, chunk_size=200, overlap=40)

# For longer chunks (less chunks, more context per chunk)
chunks = chunk_text(request.body, chunk_size=500, overlap=100)
```

### Recommendations

| Document Type | Chunk Size | Overlap | Reason |
|---------------|------------|---------|--------|
| Short articles | 200-300 | 30-50 | Precise retrieval |
| Long articles | 300-500 | 50-100 | More context |
| Technical docs | 400-600 | 80-120 | Preserve code/examples |
| FAQ/Q&A | 100-200 | 20-40 | Each Q&A separate |

## Testing Chunking

### View Chunks in Database

```bash
docker exec vector_db psql -U app -d app -c "
  SELECT 
    d.id as doc_id,
    d.title,
    COUNT(c.id) as num_chunks,
    MIN(LENGTH(c.body)) as min_chunk_length,
    MAX(LENGTH(c.body)) as max_chunk_length,
    AVG(LENGTH(c.body))::int as avg_chunk_length
  FROM documents d
  LEFT JOIN chunks c ON c.document_id = d.id
  GROUP BY d.id, d.title
  ORDER BY d.id;
"
```

### View Specific Chunks

```bash
docker exec vector_db psql -U app -d app -c "
  SELECT 
    chunk_index,
    LEFT(body, 100) as chunk_preview,
    LENGTH(body) as length
  FROM chunks
  WHERE document_id = 1
  ORDER BY chunk_index;
"
```

## Common Questions

### Q: Why not just embed the whole document?

**A:** Long documents often cover multiple topics. If you search for "cat food", you want the chunk about cat food, not a 5000-word article where cat food is mentioned once.

### Q: What happens to very short documents?

**A:** If a document is shorter than `chunk_size`, it's stored as a single chunk. No splitting occurs.

### Q: Can I disable chunking?

**A:** Yes, set `chunk_size` to a very large number (e.g., 10000). But this defeats the purpose of RAG and may reduce search quality.

### Q: How does chunking affect search results?

**A:** Search returns **chunks**, not documents. Each result is a chunk with its `chunk_index` and parent `document_id`. This gives you the exact relevant section.

## Further Reading

- [SEARCH_ENDPOINT_GUIDE.md](SEARCH_ENDPOINT_GUIDE.md) - How search works with chunks
- [DOKUMENTACJA_TECHNICZNA.md](../technical/DOKUMENTACJA_TECHNICZNA.md) - Technical implementation details
- [RAG Best Practices](https://www.pinecone.io/learn/chunking-strategies/) - External resource on chunking strategies
