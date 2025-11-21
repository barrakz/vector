# n8n + FastAPI - Dokumentacja Workflowów

**Projekt:** Vector Embeddings Demo  
**Wersja:** 2.0.0  
**Data:** 20 listopada 2025

---

## 📋 Spis treści

1. [Cel dokumentu](#cel-dokumentu)
2. [Architektura i URL-e](#architektura-i-url-e)
3. [Workflow 1: Dodawanie dokumentów](#workflow-1-dodawanie-dokumentów)
4. [Workflow 2: Wyszukiwanie dokumentów](#workflow-2-wyszukiwanie-dokumentów)
5. [Jak uruchomić i przetestować](#jak-uruchomić-i-przetestować)
6. [Najczęstsze problemy](#najczęstsze-problemy)
7. [Pomysły na przyszłość](#pomysły-na-przyszłość)

---

## 🎯 Cel dokumentu

n8n w tym projekcie służy do:
- **Dodawania dokumentów** do bazy (ingestion) - wygodne wrzucanie artykułów z automatycznym generowaniem embeddingów
- **Testowania wyszukiwania** - semantyczne zapytania do bazy przez interfejs graficzny
- **Prototypowania** - szybkie klikanie zamiast pisania curl/Postman

Zamiast w terminalu robić:
```bash
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"title":"...","body":"...","metadata":{}}'
```

...klikasz w n8n kilka pól, naciskasz Execute i masz wynik. Proste.

---

## 🏗️ Architektura i URL-e

Projekt ma trzy serwisy w `docker-compose.yml`:

| Serwis | Kontener | Co robi | Jak się do niego dostać |
|--------|----------|---------|-------------------------|
| **api** | `vector_api` | FastAPI + embeddingi | Host: `http://localhost:8000`<br>Z n8n: `http://vector_api:8000` |
| **db** | `vector_db` | PostgreSQL + pgvector | `localhost:5432` |
| **n8n** | `vector_n8n` | Workflow automation | `http://localhost:5678` (admin/admin) |

### ⚠️ Najważniejsza rzecz: URL w n8n

**Z hosta (terminal, przeglądarka):**
```
http://localhost:8000
```

**Z n8n (workflow):**
```
http://vector_api:8000
```

**Dlaczego?**  
n8n działa w kontenerze Docker. `localhost` w kontenerze to **sam kontener**, nie host. Kontenery w docker-compose rozmawiają ze sobą po **nazwach serwisów** (`vector_api`, `vector_db`, etc.). Dlatego w n8n zawsze używamy `http://vector_api:8000`, nigdy `localhost`.

---

## 📥 Workflow 1: Dodawanie dokumentów

**Flow:** Manual Trigger → Edit Fields → HTTP Request (POST /ingest)

### Krok 1: Manual Trigger

W n8n kliknij **"+"** → wybierz **"Manual"** lub **"On clicking 'Test workflow'"**.

### Krok 2: Edit Fields

Kliknij **"+"** → **"Data transformation"** → **"Edit Fields"**. Dodaj trzy pola:

| Field Name | Type | Przykład wartości |
|------------|------|-------------------|
| `title` | **String** | `Jak zresetować hasło` |
| `body` | **String** | `Kliknij 'Nie pamiętam hasła' na stronie logowania.` |
| `metadata` | **Object** ⚠️ | `{"category": "faq", "lang": "pl"}` |

**⚠️ WAŻNE:** `metadata` musi być typu **Object**, nie String!

### Krok 3: HTTP Request

Kliknij **"+"** → **"HTTP Request"**. Ustaw:

| Parametr | Wartość |
|----------|---------|
| **Method** | `POST` |
| **URL** | `http://vector_api:8000/ingest` |
| **Send Body** | ✅ ON |
| **Body Content Type** | `JSON` |

W sekcji **Body** przełącz na **Expression** i wklej:

```javascript
={{ {
  "title": $json.title,
  "body": $json.body,
  "metadata": $json.metadata
} }}
```

**Nie rób tego:**
- ❌ `"metadata": "{{ $json.metadata }}"` (cudzysłów = string)
- ❌ `"metadata": {{ $json.metadata }}` (brak `=` na początku)

**Poprawnie:**
- ✅ `"metadata": $json.metadata` (bez cudzysłowu, to jest obiekt)

### Przykład

**Body wysłane do API:**
```json
{
  "title": "Testowy artykuł",
  "body": "To jest treść artykułu dodanego z n8n.",
  "metadata": {
    "category": "test",
    "lang": "pl"
  }
}
```

**Odpowiedź z API:**
```json
{
  "status": "ok",
  "id": 27
}
```

Gotowe! Dokument jest w bazie z automatycznie wygenerowanym embeddingiem.

---

## 🔍 Workflow 2: Wyszukiwanie dokumentów

**Flow:** Manual Trigger → Edit Fields → HTTP Request (GET /search)

### Krok 1: Manual Trigger

Tak samo jak w Workflow 1.

### Krok 2: Edit Fields

Dodaj dwa pola:

| Field Name | Type | Przykład wartości |
|------------|------|-------------------|
| `q` | **String** | `jak zresetować hasło` |
| `limit` | **Number** | `5` |

### Krok 3: HTTP Request

| Parametr | Wartość |
|----------|---------|
| **Method** | `GET` |
| **URL** | `http://vector_api:8000/search` |
| **Send Query Parameters** | ✅ ON |

W sekcji **Query Parameters** dodaj:

| Name | Value (Expression) |
|------|--------------------|
| `q` | `={{ $json.q }}` |
| `limit` | `={{ $json.limit || 5 }}` |

*(`|| 5` to fallback - jeśli limit nie jest ustawiony, użyje 5)*

### Przykład odpowiedzi

```json
{
  "query": "jak zresetować hasło",
  "results": [
    {
      "id": 9,
      "title": "Password reset",
      "body": "To reset your account password...",
      "metadata": {"category": "account"},
      "distance": 0.82
    },
    {
      "id": 16,
      "title": "Jak zresetować hasło",
      "body": "Kliknij 'Nie pamiętam hasła'...",
      "metadata": {"category": "faq", "lang": "pl"},
      "distance": 0.85
    }
  ]
}
```

**Co oznacza `distance`:**
- `< 1.0` = bardzo podobne
- `1.0 - 1.3` = podobne
- `> 1.3` = słabo dopasowane

Niższa wartość = lepsze dopasowanie.

---

## 🧪 Jak uruchomić i przetestować

### Checklist:

1. **Uruchom stack:**
   ```bash
   docker compose up -d
   docker compose ps  # sprawdź czy wszystko działa
   ```

2. **Wejdź w n8n:**
   - Otwórz: http://localhost:5678
   - Login: `admin` / Hasło: `admin`

3. **Test Workflow 1 (Ingestion):**
   - Stwórz nowy workflow: Manual Trigger → Edit Fields → HTTP Request
   - Ustaw `title`, `body`, `metadata` (Object!)
   - URL: `http://vector_api:8000/ingest`
   - Kliknij **Execute Workflow**
   - Sprawdź output: `{"status": "ok", "id": ...}`

4. **Test Workflow 2 (Search):**
   - Stwórz workflow: Manual Trigger → Edit Fields → HTTP Request
   - Ustaw `q` (np. "hasło"), `limit` (np. 5)
   - URL: `http://vector_api:8000/search`
   - Kliknij **Execute Workflow**
   - Sprawdź output: lista dokumentów z `distance`

5. **Sprawdź z hosta (opcjonalnie):**
   ```bash
   # Lista dokumentów
   curl http://localhost:8000/documents

   # Wyszukaj
   curl "http://localhost:8000/search?q=haslo&limit=3"
   ```

6. **Logi (jeśli coś nie działa):**
   ```bash
   docker compose logs -f api
   ```

---

## 🐛 Najczęstsze problemy

### Problem 1: Błąd połączenia z API w n8n

```
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Przyczyna:** Użyty `http://localhost:8000` zamiast `http://vector_api:8000`.

**Fix:** Zmień URL w HTTP Request node na `http://vector_api:8000`.

---

### Problem 2: "Input should be a valid dictionary" dla metadata

```json
{
  "detail": [{
    "msg": "Input should be a valid dictionary",
    "loc": ["body", "metadata"]
  }]
}
```

**Przyczyna:** W Edit Fields `metadata` jest typu **String**, nie **Object**.

**Fix:**
1. W Edit Fields kliknij pole `metadata`
2. Zmień **Type** na **Object**
3. W HTTP Request body używaj `$json.metadata` **bez cudzysłowu**:
   ```javascript
   ={{ {
     "title": $json.title,
     "body": $json.body,
     "metadata": $json.metadata    // ✅ bez ""
   } }}
   ```

---

### Problem 3: 422 Unprocessable Entity

```json
{
  "detail": [{
    "type": "missing",
    "loc": ["body", "title"],
    "msg": "Field required"
  }]
}
```

**Przyczyna:** Brakuje `title` lub `body`, albo mają zły typ.

**Fix:** Sprawdź czy:
- `title` i `body` są ustawione w Edit Fields
- Oba są typu **String**
- Expression w HTTP Request zawiera oba pola

---

## 🚀 Pomysły na przyszłość

Jeśli chcesz rozbudować projekt, możesz dodać:

- **Webhook w n8n** - przyjmuj artykuły z zewnątrz (CMS, helpdesk) i automatycznie dodawaj do bazy przez `/ingest`
- **Automatyczna ingestion** - Schedule Trigger + RSS/API → pobieraj artykuły co godzinę i wrzucaj do bazy
- **AI FAQ endpoint** - Webhook w n8n → `/search` → zwróć JSON z odpowiedzią (integracja z chatbotem)
- **Batch ingestion** - endpoint `/ingest/batch` do dodawania wielu dokumentów jednym requestem
- **Filtrowanie po metadata** - dodaj parametr `?category=faq` do `/search`

Backend (FastAPI) ma osobną dokumentację techniczną - patrz `DOKUMENTACJA_TECHNICZNA.md`.

---

**Autor:** Vector Embeddings Demo Project  
**Licencja:** Projekt edukacyjny - użyj do nauki 🚀
