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

✅ **No API costs** - Uses local `all-MiniLM-L6-v2` model  
✅ **Duplicate detection** - Automatically prevents duplicate URLs  
✅ **Webhook ingestion** - Add articles via n8n workflows  
✅ **Application logging** - Track all operations in `api/app.log`  
✅ **Semantic search** - Find documents by meaning, not just keywords  

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
  "id": 1
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
3. Otherwise, generates a **384-dimensional vector embedding** using the local `all-MiniLM-L6-v2` model
4. The document is stored in **PostgreSQL** with:
   - `title`, `body` as text
   - `metadata` as **JSONB** (flexible JSON storage)
   - `embedding` as **vector(384)** in a pgvector column

### 2. Semantic Search (`GET /search`)

When you search:
1. The query text is converted to a vector using the **local model** (no API call!)
2. PostgreSQL uses the **`<->` operator** (L2 distance) to find documents with similar embeddings
3. Results are ordered by distance (lower = more similar)
4. The API returns the most relevant documents

**This means the search understands meaning**, not just keywords! For example, searching for "kot" (cat in Polish) will find documents about cats even if the exact word differs.

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

## Next Steps

Now that you have a working setup, you can:

1. **Experiment with different texts**: Try ingesting documents in different languages, technical documents, or creative writing
2. **Test semantic search**: Notice how it finds similar meaning, not just matching words
3. **Explore JSONB queries**: Add more complex metadata and query it directly in PostgreSQL
4. **Learn n8n**: Create workflows that automatically ingest documents from external sources
5. **Try different embedding models**: Replace `all-MiniLM-L6-v2` with multilingual models for better Polish support
6. **Experiment with distance metrics**: Try cosine similarity (`<=>`) instead of L2 distance (`<->`)

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

- **README.md** (this file) - Quick start guide
- **DOKUMENTACJA_TECHNICZNA.md** - Detailed technical documentation (Polish)
- **N8N_WORKFLOW_DOCS.md** - n8n workflow guide (Polish)

---

Happy learning! 🚀
