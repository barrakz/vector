# Vector Embeddings Demo with FastAPI, PostgreSQL, and pgvector

This is a learning project that demonstrates:
- **Vector embeddings** using OpenAI's `text-embedding-3-small` model
- **Semantic search** with pgvector in PostgreSQL
- **JSONB** for flexible document metadata
- **FastAPI** for the REST API
- **n8n** for workflow automation (ready to use, but empty for now)

All services run in Docker for easy local development.

---

## Prerequisites

- macOS with Docker Desktop installed and running
- OpenAI API key (get one at https://platform.openai.com/api-keys)

---

## Setup

### 1. Configure environment variables

Copy the example env file and add your OpenAI API key:

```bash
cp .env.example .env
```

Then edit `.env` and replace `YOUR_OPENAI_API_KEY_HERE` with your actual OpenAI API key:

```bash
# Example:
OPENAI_API_KEY=sk-proj-abc123...
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

## How It Works

### 1. Document Ingestion (`POST /ingest`)

When you send a document:
1. The **FastAPI app** receives the title, body, and metadata
2. It calls the **OpenAI API** to generate a vector embedding (1536 dimensions) from the document body
3. The document is stored in **PostgreSQL** with:
   - `title`, `body` as text
   - `metadata` as **JSONB** (flexible JSON storage)
   - `embedding` as **vector(1536)** in a pgvector column

### 2. Semantic Search (`GET /search`)

When you search:
1. The query text is sent to **OpenAI API** to generate its embedding
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
├── .env                     # Your actual config (git-ignored, you create this)
├── README.md                # This file
└── api/
    ├── Dockerfile           # Builds the FastAPI container
    ├── requirements.txt     # Python dependencies
    └── app/
        ├── main.py          # FastAPI app with endpoints
        └── db.py            # Database connection helper
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
4. **Learn n8n**: Create workflows that could:
   - Automatically ingest documents from external sources
   - Trigger actions based on document similarity
   - Connect to other APIs
5. **Try different embedding models**: OpenAI offers other models (`text-embedding-3-large` for higher quality)
6. **Experiment with distance metrics**: Try cosine similarity (`<=>`) instead of L2 distance (`<->`)

---

## Useful Commands

### View logs
```bash
docker compose logs -f api    # FastAPI logs
docker compose logs -f db     # PostgreSQL logs
docker compose logs -f n8n    # n8n logs
```

### Connect to PostgreSQL directly
```bash
docker exec -it vector_db psql -U app -d app
```

Then you can run SQL queries:
```sql
-- View documents table
SELECT * FROM documents;

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

**Problem**: API returns 500 error about OpenAI key

**Solution**: Make sure you've set `OPENAI_API_KEY` in `.env` file

**Problem**: Database connection errors

**Solution**: Wait a bit longer for PostgreSQL to initialize, or restart: `docker compose restart api`

**Problem**: n8n not loading

**Solution**: Give it a minute - n8n takes a bit longer to start up on first run

---

Happy learning! 🚀
