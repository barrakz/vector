# Dokumentacja Techniczna - Vector Embeddings Demo

**Projekt demonstracyjny:** Semantyczne wyszukiwanie dokumentów z wykorzystaniem lokalnych embeddingów i pgvector.

---

## 📋 Spis treści

1. [Przegląd architektury](#przegląd-architektury)
2. [Stack technologiczny](#stack-technologiczny)
3. [Struktura projektu](#struktura-projektu)
4. [Jak to działa](#jak-to-działa)
5. [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
6. [API Endpoints](#api-endpoints)
7. [Testowanie](#testowanie)
8. [Baza danych](#baza-danych)
9. [Embeddingi](#embeddingi)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Przegląd architektury

Projekt składa się z trzech głównych serwisów uruchamianych w Docker:

```
┌─────────────────┐
│   FastAPI API   │ ← Port 8000
│  (Python 3.11)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   PostgreSQL    │ ← Port 5432
│  + pgvector     │
│   (pg16)        │
└─────────────────┘

┌─────────────────┐
│      n8n        │ ← Port 5678
│  (workflow)     │
└─────────────────┘
```

### Główne komponenty:

1. **FastAPI Backend** - REST API do ingestion i wyszukiwania
2. **PostgreSQL z pgvector** - baza danych z rozszerzeniem do wektorów
3. **n8n** - platforma do automatyzacji workflow (opcjonalnie)

---

## 🛠️ Stack technologiczny

### Backend (FastAPI)

| Narzędzie | Wersja | Cel |
|-----------|--------|-----|
| Python | 3.11 | Język programowania |
| FastAPI | 0.104.1 | Framework REST API |
| Uvicorn | 0.24.0 | ASGI server |
| sentence-transformers | ≥2.2.0 | Lokalne embeddingi |
| torch | ≥2.0.0 | PyTorch (wymagane przez sentence-transformers) |
| psycopg | 3.1.13 | Driver PostgreSQL |
| python-dotenv | 1.0.0 | Zarządzanie zmiennymi środowiskowymi |

### Baza danych

| Narzędzie | Wersja | Cel |
|-----------|--------|-----|
| PostgreSQL | 16 | Relacyjna baza danych |
| pgvector | 0.8.1 | Rozszerzenie do operacji na wektorach |

### Workflow automation

| Narzędzie | Wersja | Cel |
|-----------|--------|-----|
| n8n | latest | Automatyzacja workflow |

---

## 📁 Struktura projektu

```
/Users/brakuzy/Code/personal/vector/
│
├── docker-compose.yml          # Definicja 3 serwisów (db, api, n8n)
├── .env.example               # Szablon zmiennych środowiskowych
├── .env                       # Twoje zmienne (git-ignored)
├── .gitignore                 # Ignorowane pliki
├── README.md                  # Dokumentacja dla użytkownika
├── DOKUMENTACJA_TECHNICZNA.md # Ta dokumentacja
│
└── api/                       # Kod aplikacji FastAPI
    ├── Dockerfile             # Obraz Docker dla API
    ├── requirements.txt       # Zależności Python
    └── app/
        ├── main.py           # Główna aplikacja FastAPI + endpoints
        └── db.py             # Zarządzanie połączeniem i schematem DB
```

---

## ⚙️ Jak to działa

### 1. Przepływ ingestion dokumentu

```
User → POST /ingest
  ↓
  {title, body, metadata}
  ↓
FastAPI otrzymuje dane
  ↓
sentence-transformers.encode(body)
  ↓
Embedding [384 floats]
  ↓
INSERT INTO documents
  (title, body, metadata::jsonb, embedding::vector(384))
  ↓
PostgreSQL + pgvector
  ↓
Response: {status: "ok", id: 1}
```

### 2. Przepływ semantycznego wyszukiwania

```
User → GET /search?q=kot&limit=3
  ↓
FastAPI otrzymuje query
  ↓
sentence-transformers.encode(q)
  ↓
Query embedding [384 floats]
  ↓
SELECT * FROM documents
ORDER BY embedding <-> query_vector::vector
LIMIT 3
  ↓
PostgreSQL + pgvector (używa IVFFlat index)
  ↓
Top 3 najbardziej podobne dokumenty
  ↓
Response: {query, results: [{id, title, body, metadata, distance}]}
```

### 3. Kluczowe mechanizmy

#### Lokalne embeddingi
- Model: `all-MiniLM-L6-v2` (sentence-transformers)
- Wymiar: **384** (zamiast 1536 jak OpenAI)
- Rozmiar: ~90 MB
- Szybkość: ~100-1000 dokumentów/sekundę (CPU)
- **Brak kosztów, brak API key, brak limitów**

#### pgvector
- Operator `<->` = L2 distance (Euclidean) - **mniejsza wartość = lepsze dopasowanie**
- Operator `<=>` = cosine similarity (opcjonalnie)
- Operator `<#>` = inner product (opcjonalnie)
- Index: **IVFFlat WYŁĄCZONY dla małych datasetów**
  - IVFFlat wymaga ~100+ dokumentów do poprawnego działania
  - Dla < 100 dokumentów: brute-force search (bardziej dokładny)
  - Dla produkcji z dużą ilością danych: włącz IVFFlat lub HNSW

#### JSONB
- Elastyczne przechowywanie metadanych
- GIN index dla szybkich zapytań
- Przykłady:
  ```sql
  WHERE metadata->>'category' = 'pets'
  WHERE metadata->>'animal' = 'cat'
  WHERE metadata @> '{"lang": "pl"}'
  ```

---

## 🚀 Instalacja i uruchomienie

### Wymagania
- Docker Desktop (dla macOS/Windows) lub Docker Engine (Linux)
- ~2 GB wolnego miejsca (obrazy Docker + modele ML)

### Krok 1: Konfiguracja
```bash
cd /Users/brakuzy/Code/personal/vector
cp .env.example .env
# Edytuj .env jeśli potrzeba (ale OPENAI_API_KEY nie jest już wymagany!)
```

### Krok 2: Build i start
```bash
# Zbuduj obrazy
docker compose build

# Uruchom wszystkie serwisy
docker compose up -d

# Sprawdź status
docker compose ps
```

### Krok 3: Sprawdź dostępność

| Serwis | URL | Opis |
|--------|-----|------|
| FastAPI | http://localhost:8000 | REST API |
| FastAPI Docs | http://localhost:8000/docs | Interaktywna dokumentacja Swagger |
| FastAPI ReDoc | http://localhost:8000/redoc | Alternatywna dokumentacja |
| PostgreSQL | localhost:5432 | Baza danych (user: app, pass: app, db: app) |
| n8n | http://localhost:5678 | Workflow automation (login: admin/admin) |

### Krok 4: Pierwsze testy
```bash
# Health check
curl http://localhost:8000/

# Dodaj dokument
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "body": "To jest testowy dokument.",
    "metadata": {"category": "test"}
  }'

# Wyszukaj
curl "http://localhost:8000/search?q=dokument&limit=3"
```

---

## 📡 API Endpoints

### `GET /`
**Health check**

**Response:**
```json
{
  "status": "ok",
  "message": "Vector embeddings API is running"
}
```

---

### `POST /ingest`
**Dodaj dokument do bazy z automatycznym wygenerowaniem embeddingu**

**Request Body:**
```json
{
  "title": "Tytuł dokumentu",
  "body": "Treść dokumentu do embedowania",
  "metadata": {
    "category": "example",
    "lang": "pl",
    "custom_field": "wartość"
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "id": 1
}
```

**Przykłady:**

```bash
# Przykład 1: Artykuł techniczny
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Wprowadzenie do Docker",
    "body": "Docker to platforma do konteneryzacji aplikacji.",
    "metadata": {"category": "tech", "difficulty": "beginner"}
  }'

# Przykład 2: FAQ
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Jak zresetowac haslo",
    "body": "Kliknij Nie pamietam hasla na stronie logowania.",
    "metadata": {"category": "faq", "lang": "pl"}
  }'
```

---

### `GET /search`
**Semantyczne wyszukiwanie dokumentów**

**Query Parameters:**
- `q` (required) - zapytanie tekstowe
- `limit` (optional, default: 5) - maksymalna liczba wyników

**Response:**
```json
{
  "query": "jak zresetować hasło",
  "results": [
    {
      "id": 2,
      "title": "Jak zresetowac haslo",
      "body": "Kliknij Nie pamietam hasla na stronie logowania.",
      "metadata": {
        "category": "faq",
        "lang": "pl"
      },
      "distance": 0.8234
    }
  ]
}
```

**Interpretacja `distance`:**
- Niższa wartość = większe podobieństwo
- Typowy zakres: 0.5 - 1.5
- < 1.0 = bardzo podobne
- 1.0 - 1.3 = podobne
- > 1.3 = mniej podobne

**Przykłady:**

```bash
# Wyszukiwanie po polsku
curl "http://localhost:8000/search?q=docker+kontener&limit=5"

# Wyszukiwanie z enkodowanym URL
curl "http://localhost:8000/search?q=$(echo 'jak zresetować hasło' | jq -sRr @uri)&limit=3"

# Z json formatting
curl -s "http://localhost:8000/search?q=docker&limit=3" | python3 -m json.tool
```

---

### `GET /documents`
**Listuj wszystkie dokumenty (debug)**

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "title": "Tytuł",
      "body": "Treść",
      "metadata": {"category": "test"}
    }
  ],
  "count": 1
}
```

---

## 🧪 Testowanie

### Test 1: Podstawowy flow

```bash
# 1. Dodaj dokumenty
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" \
  -d '{"title":"Python Tutorial","body":"Python is a high-level programming language","metadata":{"lang":"en"}}'

curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" \
  -d '{"title":"JavaScript Guide","body":"JavaScript is a scripting language for web","metadata":{"lang":"en"}}'

# 2. Wyszukaj
curl -s "http://localhost:8000/search?q=programming&limit=2" | python3 -m json.tool

# Oczekiwany wynik: Python Tutorial powinien być na pierwszym miejscu
```

### Test 2: Semantyczne podobieństwo

```bash
# Dokumenty po polsku
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" \
  -d '{"title":"Kot nie je","body":"Kot odmawia jedzenia i jest apatyczny","metadata":{"category":"pets"}}'

curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" \
  -d '{"title":"Pies szczeka","body":"Pies głośno szczeka na przechodniów","metadata":{"category":"pets"}}'

# Wyszukaj: "problem z kotem"
curl -s "http://localhost:8000/search?q=problem+z+kotem&limit=2" | python3 -m json.tool

# Oczekiwany wynik: "Kot nie je" powinien mieć niższy distance
```

### Test 3: Metadata filtering (w przyszłości)

Obecnie API nie filtruje po metadata, ale możesz to dodać:

```python
# W main.py, endpoint /search
cursor.execute(
    """
    SELECT id, title, body, metadata, embedding <-> %s::vector AS distance
    FROM documents
    WHERE metadata->>'category' = %s
    ORDER BY embedding <-> %s::vector
    LIMIT %s;
    """,
    (query_embedding, category, query_embedding, limit)
)
```

### Test 4: Performance

```bash
# Załaduj 100 dokumentów
for i in {1..100}; do
  curl -X POST http://localhost:8000/ingest \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Doc $i\",\"body\":\"This is document number $i about various topics\",\"metadata\":{\"id\":$i}}"
done

# Zmierz czas wyszukiwania
time curl -s "http://localhost:8000/search?q=document&limit=10" > /dev/null

# Typowy czas: < 100ms dla 100 dokumentów
```

### Test 5: Interaktywna dokumentacja

1. Otwórz http://localhost:8000/docs
2. Rozwiń endpoint `POST /ingest`
3. Kliknij "Try it out"
4. Wypełnij przykładowe dane
5. Kliknij "Execute"
6. Zobacz response

---

## 🗄️ Baza danych

### Schema

```sql
-- Włącz rozszerzenie pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela dokumentów
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    metadata JSONB,
    embedding vector(384)  -- 384 wymiary dla all-MiniLM-L6-v2
);

-- Index dla wyszukiwania wektorowego (IVFFlat)
-- UWAGA: WYŁĄCZONY dla małych datasetów (< 100 dokumentów)
-- IVFFlat wymaga znacznej ilości danych aby działać poprawnie
-- Dla małych datasetów brute-force search jest bardziej dokładny
--
-- CREATE INDEX documents_embedding_idx
-- ON documents
-- USING ivfflat (embedding vector_l2_ops)
-- WITH (lists = 100);

-- Index dla JSONB
CREATE INDEX documents_metadata_idx
ON documents
USING gin (metadata);
```

### Połączenie z bazą

```bash
# Z terminala
docker exec -it vector_db psql -U app -d app

# Przykładowe zapytania
\d documents                          # Struktura tabeli
SELECT COUNT(*) FROM documents;       # Liczba dokumentów
SELECT id, title FROM documents;      # Lista dokumentów

# Sprawdź wymiar embeddingu
SELECT id, title, array_length(embedding::real[], 1) as dim 
FROM documents 
LIMIT 5;

# Top 5 dokumentów podobnych do wektora
SELECT id, title, 
       embedding <-> '[0.1, 0.2, ...]'::vector as distance
FROM documents
ORDER BY distance
LIMIT 5;

# Zapytania JSONB
SELECT * FROM documents WHERE metadata->>'category' = 'pets';
SELECT * FROM documents WHERE metadata @> '{"lang": "pl"}';
```

### Backup i restore

```bash
# Backup
docker exec vector_db pg_dump -U app app > backup.sql

# Restore
docker exec -i vector_db psql -U app app < backup.sql
```

---

## 🧠 Embeddingi

### Model: all-MiniLM-L6-v2

**Charakterystyka:**
- **Autor:** sentence-transformers (Hugging Face)
- **Wymiar:** 384
- **Rozmiar:** ~90 MB
- **Architektura:** BERT-based (6 layers)
- **Training:** MS MARCO passage ranking dataset
- **Licencja:** Apache 2.0

**Performance:**
- Szybkość: ~1000-3000 dokumentów/sek (CPU)
- Jakość: dobra dla general-purpose semantic search
- Języki: **głównie angielski** - ograniczone wsparcie dla innych języków

**⚠️ UWAGA: Język polski**
- Model `all-MiniLM-L6-v2` jest trenowany głównie na angielskim
- Nie rozumie polskiej morfologii ("kot" vs "koty" to różne tokeny)
- Dla języka polskiego: użyj modelu wielojęzycznego (patrz alternatywy poniżej)
- **Testuj zawsze na angielskim** dla najlepszych wyników

**Alternatywne modele (wymienić w `main.py`):**

```python
# Lepszy dla języków europejskich (w tym polski)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
# Wymiar: 384, ~470 MB

# Wyższa jakość (wolniejszy)
model = SentenceTransformer("all-mpnet-base-v2")
# Wymiar: 768, ~438 MB

# Polski model (jeśli potrzeba)
model = SentenceTransformer("sdadas/mmlw-retrieval-roberta-base")
# Wymiar: 768
```

**UWAGA:** Po zmianie modelu z innym wymiarem:
1. Zaktualizuj `vector(384)` w `db.py` na właściwy wymiar
2. Przebuduj kontener: `docker compose down && docker compose build && docker compose up -d`

### Proces generowania embeddingu

```python
from sentence_transformers import SentenceTransformer

# Load model (raz przy starcie)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embedding
text = "To jest przykładowy tekst"
embedding = model.encode(text)
# embedding = numpy array [384 floats]

# Convert to list for PostgreSQL
embedding_list = embedding.tolist()
# [0.123, -0.456, 0.789, ...]
```

### Metryki podobieństwa

| Metryka | Operator pgvector | Kiedy używać |
|---------|-------------------|--------------|
| L2 distance (Euclidean) | `<->` | Domyślnie (używane w projekcie) |
| Cosine similarity | `<=>` | Gdy długość wektora ma znaczenie |
| Inner product | `<#>` | Dla znormalizowanych wektorów |

**Zmiana na cosine similarity:**

W `main.py`, zmień:
```python
embedding <-> %s::vector  # L2
# na:
embedding <=> %s::vector  # cosine
```

I w `db.py`, zmień:
```sql
USING ivfflat (embedding vector_l2_ops)
# na:
USING ivfflat (embedding vector_cosine_ops)
```

---

## 🔧 Troubleshooting

### Problem: API nie startuje

**Logi:**
```bash
docker compose logs api
```

**Częste przyczyny:**
1. Port 8000 zajęty → zmień w `docker-compose.yml`
2. Błąd instalacji torch → sprawdź architekturę (ARM vs x86)
3. Brak pamięci → Docker Desktop ma za mało RAM (zwiększ do 4GB+)

### Problem: Model się nie ładuje

**Objawy:**
```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**Rozwiązanie:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Problem: Baza danych nie odpowiada

**Diagnoza:**
```bash
docker compose logs db
docker exec -it vector_db pg_isready -U app
```

**Restart:**
```bash
docker compose restart db
```

### Problem: Puste wyniki wyszukiwania

**Przyczyny:**
1. Brak dokumentów → sprawdź `curl http://localhost:8000/documents`
2. Restart API przebudował tabelę (DROP TABLE) → dodaj dokumenty ponownie
3. Query nie pasuje do żadnego dokumentu → sprawdź `distance` w wynikach
4. **IVFFlat index z małą ilością danych** ← **NAJCZĘSTSZA PRZYCZYNA**

**Rozwiązanie problemu IVFFlat:**

IVFFlat wymaga ~100+ dokumentów do poprawnego działania. Dla małych datasetów:

```bash
# Usuń indeks (włącza brute-force search)
docker exec vector_db psql -U app -d app -c "DROP INDEX IF EXISTS documents_embedding_idx;"

# Testuj ponownie
curl "http://localhost:8000/search?q=test&limit=5"
```

**Dezaktywacja DROP TABLE (zachowanie danych):**

W `db.py`, już zaimplementowane - używa `CREATE TABLE IF NOT EXISTS`

### Problem: Wolne wyszukiwanie

**Diagnoza:**
```sql
EXPLAIN ANALYZE 
SELECT id, title, embedding <-> '[...]'::vector as distance
FROM documents
ORDER BY distance
LIMIT 5;
```

**Optymalizacje:**
1. Zwiększ `lists` w indeksie (dla > 1000 dokumentów):
   ```sql
   CREATE INDEX ... WITH (lists = 500);  -- zamiast 100
   ```
2. Użyj HNSW zamiast IVFFlat (PostgreSQL 16+):
   ```sql
   CREATE INDEX ... USING hnsw (embedding vector_l2_ops);
   ```

### Problem: Błąd "cannot adapt type 'dict'"

**Przyczyna:** Brak konwersji dict → Jsonb

**Rozwiązanie:**
```python
from psycopg.types.json import Jsonb

# W insert:
cursor.execute("...", (title, body, Jsonb(metadata), embedding))
```

### Problem: Błąd "operator does not exist: vector <-> double precision[]"

**Przyczyna:** Brak rzutowania na typ vector

**Rozwiązanie:**
```python
# Dodaj ::vector
cursor.execute("""
    SELECT ... embedding <-> %s::vector ...
""", (query_embedding, ...))
```

---

## 📊 Monitoring i logi

### Logi w czasie rzeczywistym

```bash
# Wszystkie serwisy
docker compose logs -f

# Tylko API
docker compose logs -f api

# Tylko baza danych
docker compose logs -f db

# Ostatnie 50 linii
docker compose logs --tail=50 api
```

### Status serwisów

```bash
# Lista kontenerów
docker compose ps

# Użycie zasobów
docker stats

# Szczegóły kontenera
docker inspect vector_api
```

### Metryki FastAPI

Dodaj endpoint `/metrics` w `main.py`:

```python
@app.get("/metrics")
async def metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT pg_database_size('app')")
    db_size = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return {
        "documents_count": doc_count,
        "database_size_bytes": db_size,
        "model": "all-MiniLM-L6-v2",
        "embedding_dimension": 384
    }
```

---

## 🔐 Bezpieczeństwo

### Produkcyjne ustawienia

**NIE UŻYWAJ w produkcji:**
- Hasło `app/app` do bazy danych
- Basic auth `admin/admin` w n8n
- Brak HTTPS
- Brak rate limiting

**Zalecenia:**
1. Użyj silnych haseł (secrets w Docker)
2. Dodaj HTTPS (nginx reverse proxy)
3. Włącz rate limiting w FastAPI
4. Dodaj autentykację (JWT, OAuth2)
5. Waliduj input (pydantic już to robi)

---

## 📚 Dalszy rozwój

### Pomysły na rozszerzenia

1. **Filtering w search**
   ```python
   @app.get("/search")
   async def search(q: str, category: str = None, limit: int = 5):
       # WHERE metadata->>'category' = category
   ```

2. **Batch ingestion**
   ```python
   @app.post("/ingest/batch")
   async def ingest_batch(documents: list[IngestRequest]):
       # INSERT INTO ... VALUES (%s, %s, ...), (%s, %s, ...), ...
   ```

3. **Hybrid search (keyword + semantic)**
   ```sql
   SELECT *, 
          embedding <-> %s::vector as semantic_score,
          ts_rank(to_tsvector(body), plainto_tsquery(%s)) as keyword_score
   FROM documents
   ORDER BY semantic_score * 0.7 + keyword_score * 0.3
   ```

4. **Re-ranking z cross-encoder**
   ```python
   from sentence_transformers import CrossEncoder
   reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
   ```

5. **Clustering dokumentów**
   ```python
   from sklearn.cluster import KMeans
   # Cluster embeddings into topics
   ```

6. **Webhook dla n8n**
   ```python
   @app.post("/webhook/n8n")
   async def n8n_webhook(data: dict):
       # Auto-ingest from n8n workflow
   ```

---

## 📖 Źródła i dokumentacja

- **FastAPI:** https://fastapi.tiangolo.com/
- **sentence-transformers:** https://www.sbert.net/
- **pgvector:** https://github.com/pgvector/pgvector
- **PostgreSQL:** https://www.postgresql.org/docs/
- **n8n:** https://docs.n8n.io/

---

## 📝 Changelog

### v2.1.0 (2025-11-20)
- ✅ **Wyłączenie IVFFlat index dla małych datasetów**
- ✅ IVFFlat wymaga ~100+ dokumentów - dla mniejszych datasetów brute-force jest dokładniejszy
- ✅ Dodanie informacji o wsparciu językowym (angielski głównie)
- ✅ Zachowanie danych przy restarcie (IF NOT EXISTS)
- ✅ Dokumentacja troubleshootingu pustych wyników

### v2.0.0 (2025-11-20)
- ✅ Zamiana OpenAI na lokalne embeddingi (sentence-transformers)
- ✅ Model: all-MiniLM-L6-v2 (384 wymiary)
- ✅ Brak kosztów, brak API key
- ✅ Poprawki JSONB handling
- ✅ Poprawki vector casting w SQL

### v1.0.0 (2025-11-20)
- ✅ Projekt początkowy z OpenAI embeddings
- ✅ PostgreSQL + pgvector
- ✅ FastAPI REST API
- ✅ n8n integration ready

---

**Autor projektu:** Projekt edukacyjny - vector embeddings demo  
**Data ostatniej aktualizacji:** 20 listopada 2025
