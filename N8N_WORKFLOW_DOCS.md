# n8n Workflows - Dokumentacja

## Dostępne Workflow

### 1. Ingest Article from URL (Webhook POST)

**Plik:** `1_ingest_from_url.json`

**Endpoint:** `POST http://localhost:5678/webhook/ingest-url`

**Opis:** Pobiera artykuł z URL, ekstraktuje tytuł i treść, a następnie wysyła do API `/ingest` gdzie jest chunkowany i zapisywany.

**Użycie:**
```bash
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**Przepływ:**
1. Webhook otrzymuje URL
2. Pobiera HTML ze strony
3. Ekstraktuje tytuł (h1) i treść (p)
4. Formatuje dane
5. Wysyła do API `/ingest`
6. Zwraca odpowiedź z `document_id` i `chunks_inserted`

---

### 2. Search Documents (Webhook GET)

**Plik:** `2_search_documents.json`

**Endpoint:** `GET http://localhost:5678/webhook/search?q={zapytanie}&limit={liczba}`

**Opis:** Webhook GET, który przekazuje zapytanie do API `/search` i zwraca wyniki wyszukiwania chunków.

**Użycie:**
```bash
# Proste wyszukiwanie
curl "http://localhost:5678/webhook/search?q=kot&limit=3"

# Z polskimi znakami
curl "http://localhost:5678/webhook/search?q=karmienie+kota&limit=5"

# Z przeglądarki
http://localhost:5678/webhook/search?q=weterynarz&limit=2
```

**Parametry:**
- `q` - zapytanie (wymagane, domyślnie: "default search")
- `limit` - liczba wyników (opcjonalne, domyślnie: 5)

**Przepływ:**
1. Webhook GET otrzymuje parametry `q` i `limit`
2. Przekazuje je do API `GET /search`
3. Zwraca wyniki chunków w formacie JSON

**Odpowiedź:**
```json
{
  "query": "kot",
  "results": [
    {
      "chunk_id": 1,
      "document_id": 42,
      "chunk_index": 0,
      "title": "Kompletny przewodnik po kotach",
      "body": "[Fragment ~300 słów]",
      "metadata": {"category": "pets"},
      "distance": 1.26
    }
  ]
}
```

---

## Import do n8n

### Krok 1: Otwórz n8n
```
http://localhost:5678
```

### Krok 2: Import Workflow

1. Kliknij **"+"** (nowy workflow)
2. Kliknij **menu (⋮)** → **Import from File**
3. Wybierz plik:
   - `n8n_workflows/1_ingest_from_url.json` lub
   - `n8n_workflows/2_search_documents.json`
4. Kliknij **Import**

### Krok 3: Aktywuj Workflow

1. Po zaimportowaniu kliknij przełącznik **"Inactive"** → **"Active"**
2. Workflow jest teraz aktywny i nasłuchuje na webhookach

---

## Testowanie Workflows

### Test 1: Ingest Article

```bash
# Dodaj artykuł z URL
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://weszlo.com/ekstraklasa-finansowa-polskie-kluby-wydaja-ponad-stan-oto-raport/"}'

# Odpowiedź:
# {
#   "status": "ok",
#   "document_id": 43,
#   "chunks_inserted": 5
# }
```

### Test 2: Search Documents

```bash
# Wyszukaj chunki
curl "http://localhost:5678/webhook/search?q=piłka+nożna&limit=3"

# Odpowiedź:
# {
#   "query": "piłka nożna",
#   "results": [...]
# }
```

---

## Różnice między Endpointami

### Bezpośrednie API vs n8n Webhook

| Aspekt | Bezpośrednie API | n8n Webhook |
|--------|------------------|-------------|
| **URL** | `http://localhost:8000/search` | `http://localhost:5678/webhook/search` |
| **Wymaga n8n** | Nie | Tak (workflow musi być aktywny) |
| **Dodatkowa logika** | Nie | Można dodać (transformacje, logi, itp.) |
| **Użycie** | Bezpośrednie wywołanie API | Proxy przez n8n |

### Kiedy Używać Którego?

**Bezpośrednie API (`localhost:8000`):**
- ✅ Szybsze (bez pośrednika)
- ✅ Prostsze
- ✅ Nie wymaga n8n
- ❌ Brak dodatkowej logiki

**n8n Webhook (`localhost:5678`):**
- ✅ Można dodać logikę (transformacje, walidacje)
- ✅ Można logować zapytania
- ✅ Można łączyć z innymi workflow
- ❌ Wymaga aktywnego n8n
- ❌ Wolniejsze (dodatkowy hop)

---

## Przykłady Użycia

### Pełny Przepływ RAG

```bash
# 1. Dodaj artykuł
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article-about-cats"}'

# 2. Wyszukaj relevantne chunki
curl "http://localhost:5678/webhook/search?q=jak+karmić+kota&limit=3"

# 3. Użyj wyników w LLM (np. ChatGPT, Claude)
# Przekaż zwrócone chunki jako kontekst
```

### Integracja z Zewnętrzną Aplikacją

```javascript
// Frontend aplikacji
async function searchKnowledgeBase(query) {
  const response = await fetch(
    `http://localhost:5678/webhook/search?q=${encodeURIComponent(query)}&limit=5`
  );
  const data = await response.json();
  return data.results;
}

// Użycie
const results = await searchKnowledgeBase('karmienie kota');
console.log(results);
```

---

## Rozszerzanie Workflows

### Dodanie Logowania do Search Workflow

Możesz dodać node **Set** lub **Code** między webhook a API call, aby:
- Logować zapytania do pliku/bazy
- Walidować parametry
- Transformować zapytanie
- Dodać cache

### Dodanie Filtrowania Wyników

Możesz dodać node **Filter** lub **Code** po API call, aby:
- Filtrować wyniki po distance
- Grupować po document_id
- Formatować odpowiedź

---

## Troubleshooting

### Webhook nie działa

1. Sprawdź czy workflow jest **Active**
2. Sprawdź URL webhooka w n8n (kliknij na node Webhook)
3. Sprawdź czy n8n działa: `docker compose ps`

### API nie odpowiada

1. Sprawdź czy API działa: `curl http://localhost:8000/`
2. Sprawdź logi: `docker compose logs api`
3. Sprawdź czy używasz prawidłowego URL w n8n (`http://api:8000` nie `localhost:8000`)

### Brak wyników

1. Sprawdź czy są chunki w bazie:
   ```bash
   docker exec vector_db psql -U app -d app -c "SELECT COUNT(*) FROM chunks;"
   ```
2. Sprawdź czy zapytanie jest poprawne
3. Zwiększ `limit` parametr
