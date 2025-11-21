# Vector Embeddings Demo with FastAPI, PostgreSQL, and pgvector

This is a learning project that demonstrates:
- **Vector embeddings** using **local sentence-transformers** model (no API key needed!)
- **Semantic search** with pgvector in PostgreSQL
- **JSONB** for flexible document metadata
- **FastAPI** for the REST API
- **n8n** for workflow automation with webhook-based article ingestion
- **Application logging** to track all operations

All services run in Docker for easy local development.

---

## Features

✅ **RAG-ready chunking** - Documents split into ~300 word chunks for precise retrieval  
✅ **Multilingual support** - Works with Polish, English, and 50+ languages  
✅ **No API costs** - Uses local `paraphrase-multilingual-MiniLM-L12-v2` model  
✅ **Duplicate detection** - Automatically prevents duplicate URLs  
✅ **Webhook ingestion** - Add articles via n8n workflows  
✅ **Application logging** - Track all operations in `api/app.log`  
✅ **Semantic search** - Find relevant text fragments, not just keywords  

---

## Prerequisites

- macOS with Docker Desktop installed and running
- **No API key needed!** Everything runs locally.

---

## Setup

### 1. Configure environment variables (optional)

The `.env` file is optional since we use local embeddings:

```bash
cp .env.example .env
```

### 2. Build and run the Docker stack

From this directory, run:

```bash
docker compose up --build
```

This will start three services:
- **PostgreSQL** with pgvector extension (port 5432)
- **FastAPI** backend (port 8000)
- **n8n** workflow automation (port 5678)

Wait until you see logs indicating all services are ready (typically 20-30 seconds).

---

## Services

Once running, you can access:

### FastAPI API
- **URL**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative docs**: http://localhost:8000/redoc

### n8n Workflow Automation
- **URL**: http://localhost:5678
- **Login**: 
  - Username: `admin`
  - Password: `admin`

---

## Testing the API

### Example 1: Ingest a document

Add a document about cats and dogs (in Polish):

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Artykuł o kotach i psach",
    "body": "Kot śpi na kanapie, a pies biega po ogrodzie. Koty są leniwymi zwierzętami.",
    "metadata": {"category": "animals", "lang": "pl"}
  }'
```

Response:
```json
{
  "status": "ok",
  "document_id": 1,
  "chunks_inserted": 1
}
```

Add another document:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Przepis na ciasto",
    "body": "Wymieszaj mąkę, cukier i jajka. Piecz w 180 stopniach przez 30 minut.",
    "metadata": {"category": "recipes", "lang": "pl"}
  }'
```

And one more (in English):

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Article about dogs",
    "body": "Dogs are loyal companions. They love to play and run in the park.",
    "metadata": {"category": "animals", "lang": "en"}
  }'
```

### Example 2: Semantic search

Search for documents about cats (in Polish):

```bash
curl "http://localhost:8000/search?q=kot&limit=3"
```

Or about dogs (in English):

```bash
curl "http://localhost:8000/search?q=dog&limit=3"
```

Or about recipes/cooking:

```bash
curl "http://localhost:8000/search?q=gotowanie&limit=3"
```

The API will return documents sorted by semantic similarity (lowest distance = most similar).

### Example 3: List all documents

```bash
curl http://localhost:8000/documents
```

---

## Using n8n Workflows

The project includes ready-to-use n8n workflows for automated article ingestion.

### Import Workflows

1. Open n8n: http://localhost:5678 (login: `admin` / `admin`)
2. Click **three dots** (top right) → **Import from File**
3. Import files from `n8n_workflows/`:
   - `1_ingest_from_url.json` - Fetch and ingest articles from URLs
   - `2_search_documents.json` - Search the vector database

### Using the Webhook Workflow

The **Ingest from URL** workflow accepts POST requests:

**URL**: `http://localhost:5678/webhook/ingest-url`  
**Method**: `POST`  
**Body**:
```json
{
  "url": "https://example.com/article"
}
```

**Example with curl**:
```bash
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://weszlo.com/sylvinho-trener-reprezentacji-albanii-to-on-sprobuje-ograc-urbana/"}'
```

The workflow will:
1. Fetch the HTML from the URL
2. Extract title and paragraphs
3. Send to the vector API
4. **Skip if URL already exists** (duplicate detection)

See `N8N_WORKFLOW_DOCS.md` for detailed n8n documentation.

---

## Application Logging

All operations are logged to `api/app.log`. View logs:

```bash
cat api/app.log
```

Or in real-time:
```bash
tail -f api/app.log
```

Log entries include:
- Document ingestion (title, metadata, URL)
- Duplicate detection (skipped URLs)
- Search queries (query text, result count)
- Errors and warnings

---

## How It Works

### 1. Document Ingestion (`POST /ingest`)

When you send a document:
1. The **FastAPI app** checks if a document with the same URL already exists
2. If it exists, returns the existing document ID (no duplicate)
3. Otherwise, the document **body is split into chunks** (~300 words each, 50 word overlap)
4. Each chunk gets its own **384-dimensional vector embedding** using the local `paraphrase-multilingual-MiniLM-L12-v2` model
5. Chunks are stored in **PostgreSQL** with:
   - `title` (inherited from document)
   - `body` (the chunk text, ~300 words)
   - `metadata` as **JSONB** (flexible JSON storage)
   - `embedding` as **vector(384)** in a pgvector column
   - `document_id` (link to parent document)
   - `chunk_index` (position in document)

**Why chunking?** This enables RAG (Retrieval-Augmented Generation) by returning precise, relevant text fragments instead of entire documents.

### 2. Semantic Search (`GET /search`)

When you search:
1. The query text is converted to a vector using the **local multilingual model** (no API call!)
2. PostgreSQL searches the **chunks table** using the **`<->` operator** (L2 distance) to find chunks with similar embeddings
3. Results are ordered by distance (lower = more similar)
4. The API returns the most relevant **text fragments** (chunks), not entire documents

**This means the search understands meaning**, not just keywords! For example, searching for "karmienie kota" (feeding a cat in Polish) will find specific chunks about cat feeding, even if the exact phrase differs.

**Perfect for RAG:** Each result is a ~300 word fragment that can be directly used as context for LLMs.

### 3. JSONB Metadata

Each document can have flexible metadata stored as JSONB. This allows:
- Fast queries on JSON fields (using GIN index)
- Flexible schema (no need to predefine all fields)
- Example queries you could run in SQL: 
  ```sql
  SELECT * FROM documents WHERE metadata->>'category' = 'animals';
  ```

### 4. pgvector

The `pgvector` extension adds:
- A `vector` data type for storing embeddings
- Distance operators: `<->` (L2), `<=>` (cosine), `<#>` (inner product)
- Specialized indexes (IVFFlat, HNSW) for fast similarity search

---

## Project Structure

```
/Users/brakuzy/Code/personal/vector/
├── docker-compose.yml       # Defines the 3 services (db, api, n8n)
├── .env.example             # Template for environment variables
├── .env                     # Your actual config (git-ignored, optional)
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── DOKUMENTACJA_TECHNICZNA.md  # Technical documentation (Polish)
├── N8N_WORKFLOW_DOCS.md     # n8n workflow documentation (Polish)
├── n8n_workflows/           # Ready-to-import n8n workflows
│   ├── 1_ingest_from_url.json
│   └── 2_search_documents.json
└── api/
    ├── Dockerfile           # Builds the FastAPI container
    ├── requirements.txt     # Python dependencies
    └── app/
        ├── main.py          # FastAPI app with endpoints
        ├── db.py            # Database connection helper
        └── app.log          # Application logs (auto-created)
```

---

## Stopping the Services

Press `Ctrl+C` in the terminal where `docker compose` is running, or run:

```bash
docker compose down
```

To remove all data (database + n8n volumes):

```bash
docker compose down -v
```

---

## Chunking & RAG

This implementation uses **text chunking** to enable RAG (Retrieval-Augmented Generation):

- **Chunk size**: 300 words (configurable in `api/app/chunking.py`)
- **Overlap**: 50 words (preserves context between chunks)
- **Benefits**: Returns precise, relevant fragments instead of entire documents

### Why Chunking?

**Without chunking:**
- Search returns entire 5000-word article
- Relevant info buried in middle
- Too much text for LLM context

**With chunking:**
- Search returns specific 300-word fragment
- Precise semantic matching
- Perfect size for LLM context
- Multiple relevant chunks from same document possible

### Changing Chunk Size

Edit `api/app/chunking.py`:
```python
def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    # Adjust chunk_size and overlap as needed
```

---

## Multilingual Support

The project uses `paraphrase-multilingual-MiniLM-L12-v2` which supports 50+ languages including:
- Polish (Polski)
- English
- German, French, Spanish, Italian
- And many more

### Changing the Model

To use a different model, edit `api/app/main.py`:

```python
# Current: Multilingual (50+ languages, 384 dimensions)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Alternative: English-only (faster, smaller)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Alternative: Best quality multilingual (768 dimensions - requires DB schema change!)
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
```

**Note:** If changing to a model with different dimensions (e.g., 768), you must also update `vector(384)` to `vector(768)` in `api/app/db.py` and rebuild the database.

---

## Next Steps

Now that you have a working setup, you can:

1. **Test RAG workflow**: Ingest long articles, search for specific topics, use results with LLMs
2. **Experiment with different texts**: Try ingesting documents in different languages
3. **Test semantic search**: Notice how it finds similar meaning, not just matching words
4. **Explore JSONB queries**: Add more complex metadata and query it directly in PostgreSQL
5. **Learn n8n**: Create workflows that automatically ingest documents from external sources
6. **Adjust chunk size**: Experiment with different chunk sizes for your use case
7. **Try different models**: Test English-only vs multilingual models

---

## Useful Commands

### View logs
```bash
docker compose logs -f api    # FastAPI logs
docker compose logs -f db     # PostgreSQL logs
docker compose logs -f n8n    # n8n logs
```

### View application logs
```bash
cat api/app.log               # All logs
tail -f api/app.log           # Follow logs in real-time
```

### Connect to PostgreSQL directly
```bash
docker exec -it vector_db psql -U app -d app
```

Then you can run SQL queries:
```sql
-- View documents table
SELECT * FROM documents;

-- Check for duplicates
SELECT metadata->>'url' as url, COUNT(*) 
FROM documents 
WHERE metadata->>'url' IS NOT NULL 
GROUP BY metadata->>'url' 
HAVING COUNT(*) > 1;

-- Search using SQL directly
SELECT id, title, embedding <-> '[0.1, 0.2, ...]'::vector AS distance
FROM documents
ORDER BY distance
LIMIT 5;
```

### Rebuild after code changes
```bash
docker compose up --build
```

---

## Troubleshooting

**Problem**: Model loading takes a long time on first start

**Solution**: This is normal - the model (~90MB) is downloaded on first run. Subsequent starts are much faster.

**Problem**: Database connection errors

**Solution**: Wait a bit longer for PostgreSQL to initialize, or restart: `docker compose restart api`

**Problem**: n8n not loading

**Solution**: Give it a minute - n8n takes a bit longer to start up on first run

**Problem**: Duplicate documents in database

**Solution**: The API now automatically prevents duplicates based on URL. Existing duplicates can be removed via SQL.

---

## Documentation

📚 **[Documentation Index](docs/README.md)** - All documentation organized by category

### Quick Links

- **[Technical Documentation](docs/technical/DOKUMENTACJA_TECHNICZNA.md)** - Comprehensive technical guide (Polish)
- **[n8n Workflows](docs/workflows/N8N_WORKFLOW_DOCS.md)** - Workflow automation guide (Polish)
- **[Chunking Guide](docs/guides/CHUNKING_GUIDE.md)** - How text chunking works
- **[Search Guide](docs/guides/SEARCH_ENDPOINT_GUIDE.md)** - Search endpoint documentation
- **[Changelog](CHANGELOG.md)** - Version history

---

Happy learning! 🚀
