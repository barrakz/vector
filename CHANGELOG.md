# Changelog - feature/rag-chunking

## Nowe Funkcjonalności

### 🎯 RAG-Ready Text Chunking
- Dokumenty są automatycznie dzielone na fragmenty ~300 słów
- Overlap 50 słów między chunkami zachowuje kontekst
- Każdy chunk ma własny embedding dla precyzyjnego wyszukiwania
- Zwracane są konkretne fragmenty zamiast całych dokumentów

### 🌍 Wsparcie Wielojęzyczne
- Zmiana modelu na `paraphrase-multilingual-MiniLM-L12-v2`
- Obsługa 50+ języków (w tym polski)
- Ten sam wymiar 384 (kompatybilność z bazą danych)
- Lepsze wyniki dla języka polskiego

### 🔍 Ulepszone Wyszukiwanie
- Endpoint `/search` zwraca chunki zamiast pełnych dokumentów
- Każdy wynik zawiera: `chunk_id`, `document_id`, `chunk_index`
- Idealne dla RAG - fragmenty gotowe do użycia przez LLM

### 🔗 n8n Webhook dla Search
- Nowy workflow: `2_search_documents.json`
- GET endpoint: `http://localhost:5678/webhook/search?q=...&limit=...`
- Proxy do API search z możliwością dodania logiki

## Zmiany w API

### POST /ingest
**Przed:**
```json
{
  "status": "ok",
  "id": 1
}
```

**Po:**
```json
{
  "status": "ok",
  "document_id": 1,
  "chunks_inserted": 3
}
```

### GET /search
**Przed:**
```json
{
  "results": [{
    "id": 1,
    "title": "...",
    "body": "[CAŁY ARTYKUŁ 5000 SŁÓW]",
    "distance": 0.85
  }]
}
```

**Po:**
```json
{
  "results": [{
    "chunk_id": 15,
    "document_id": 42,
    "chunk_index": 4,
    "title": "...",
    "body": "[FRAGMENT ~300 SŁÓW]",
    "distance": 2.54
  }]
}
```

## Nowe Pliki

- `api/app/chunking.py` - Algorytm chunkowania tekstu
- `api/migrations/001_add_chunks_table.sql` - Migracja SQL
- `test_chunking.sh` - Testy funkcjonalności chunkowania
- `test_multilingual.sh` - Testy wielojęzyczności
- `test_polish_model.sh` - Testy modelu polskiego
- `SEARCH_ENDPOINT_GUIDE.md` - Przewodnik użycia endpoint search
- `N8N_WORKFLOW_DOCS.md` - Dokumentacja workflow n8n

## Zmiany w Bazie Danych

### Nowa Tabela: chunks
```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    metadata JSONB,
    embedding vector(384),
    UNIQUE(document_id, chunk_index)
);
```

### Indeksy
- `chunks_document_id_idx` - szybkie wyszukiwanie po document_id
- `chunks_metadata_idx` - GIN index dla JSONB
- Vector index wyłączony dla małych datasetów

## Migracja Danych

**Uwaga:** Stare dokumenty w tabeli `documents` nie są automatycznie chunkowane.

**Opcje:**
1. Re-ingest dokumentów przez API (zalecane)
2. Ręczna migracja SQL
3. Dual mode - stare bez chunków, nowe z chunkami

## Testy

Wszystkie testy przeszły pomyślnie:
- ✅ Chunking działa (300 słów, 50 overlap)
- ✅ Ingestion z chunkowaniem
- ✅ Search zwraca chunki
- ✅ Wykrywanie duplikatów działa
- ✅ Polski język działa poprawnie
- ✅ n8n webhook działa

## Commits

```
9462fd4 docs: update README with chunking and multilingual features
e247b25 feat: switch to multilingual model for Polish language support
a8e8658 feat: add n8n search webhook workflow
9e532c1 feat: implement RAG-ready text chunking
```

## Następne Kroki

Branch `feature/rag-chunking` jest gotowy do:
1. Testowania produkcyjnego
2. Merge do `main` (po zatwierdzeniu)
3. Deploy na produkcję

## Rollback

Jeśli potrzeba wrócić do starej wersji:
```bash
git checkout main
docker compose down
docker compose up --build
```
