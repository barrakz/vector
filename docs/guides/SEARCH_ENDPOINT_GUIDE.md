# 🔍 Jak Używać /search Endpoint

## Podstawowe Użycie

Endpoint `/search` jest już dostępny jako **GET request**:

```
GET http://localhost:8000/search?q={zapytanie}&limit={liczba_wyników}
```

### Parametry

- `q` (wymagany) - fraza do wyszukania
- `limit` (opcjonalny, domyślnie: 5) - maksymalna liczba wyników

---

## 📝 Przykłady Użycia

### 1. Z curl (terminal)

```bash
# Proste wyszukiwanie
curl "http://localhost:8000/search?q=karmienie+kota&limit=3"

# Z formatowaniem JSON
curl -s "http://localhost:8000/search?q=weterynarz&limit=2" | python3 -m json.tool

# Z enkodowaniem URL (dla polskich znaków)
curl "http://localhost:8000/search?q=$(echo 'jak karmić kota' | jq -sRr @uri)&limit=5"
```

### 2. Z przeglądarki

Po prostu otwórz w Chrome/Firefox:
```
http://localhost:8000/search?q=kot&limit=3
```

### 3. Z n8n Workflow

#### Krok 1: Dodaj HTTP Request Node

1. Dodaj node **HTTP Request**
2. Ustaw **Method**: `GET`
3. Ustaw **URL**: `http://api:8000/search`

#### Krok 2: Dodaj Query Parameters

W sekcji **Query Parameters**:
- **Name**: `q`, **Value**: `{{$json.query}}` (lub stała wartość jak `kot`)
- **Name**: `limit`, **Value**: `5`

#### Przykładowy Workflow n8n

```json
{
  "nodes": [
    {
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "name": "Set Query",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {
              "name": "query",
              "value": "karmienie kota"
            }
          ]
        }
      }
    },
    {
      "name": "Search Chunks",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://api:8000/search",
        "qs": {
          "q": "={{$json.query}}",
          "limit": "3"
        },
        "options": {}
      }
    }
  ]
}
```

### 4. Z JavaScript/Fetch

```javascript
// Proste wyszukiwanie
fetch('http://localhost:8000/search?q=kot&limit=3')
  .then(response => response.json())
  .then(data => {
    console.log('Query:', data.query);
    console.log('Results:', data.results);
    
    // Przetwórz wyniki
    data.results.forEach(chunk => {
      console.log(`Chunk ${chunk.chunk_index} from doc ${chunk.document_id}`);
      console.log(`Title: ${chunk.title}`);
      console.log(`Distance: ${chunk.distance}`);
      console.log(`Body: ${chunk.body.substring(0, 100)}...`);
    });
  });

// Z async/await
async function searchChunks(query, limit = 5) {
  const params = new URLSearchParams({ q: query, limit });
  const response = await fetch(`http://localhost:8000/search?${params}`);
  const data = await response.json();
  return data.results;
}

// Użycie
const results = await searchChunks('karmienie kota', 3);
```

### 5. Z Python

```python
import requests

# Proste wyszukiwanie
response = requests.get('http://localhost:8000/search', params={
    'q': 'karmienie kota',
    'limit': 3
})

data = response.json()
print(f"Query: {data['query']}")

for chunk in data['results']:
    print(f"\nChunk ID: {chunk['chunk_id']}")
    print(f"Document ID: {chunk['document_id']}")
    print(f"Title: {chunk['title']}")
    print(f"Distance: {chunk['distance']:.2f}")
    print(f"Preview: {chunk['body'][:100]}...")
```

---

## 📤 Format Odpowiedzi

```json
{
  "query": "karmienie kota",
  "results": [
    {
      "chunk_id": 1,
      "document_id": 42,
      "chunk_index": 0,
      "title": "Kompletny przewodnik po kotach",
      "body": "[Fragment tekstu ~300 słów]",
      "metadata": {
        "category": "pets",
        "url": "https://example.com/article"
      },
      "distance": 1.18
    }
  ]
}
```

### Pola w Odpowiedzi

- `query` - zapytanie, które zostało wyszukane
- `results` - lista znalezionych chunków (max `limit`)
  - `chunk_id` - ID chunka w bazie
  - `document_id` - ID dokumentu źródłowego
  - `chunk_index` - numer chunka w dokumencie (0, 1, 2...)
  - `title` - tytuł dokumentu
  - `body` - treść chunka (~300 słów)
  - `metadata` - metadane (kategoria, URL, itp.)
  - `distance` - odległość semantyczna (niższa = lepsze dopasowanie)

---

## 🎯 Przykłady Praktyczne

### Wyszukiwanie z Różnymi Frazami

```bash
# Wyszukaj informacje o karmieniu
curl -s "http://localhost:8000/search?q=karmienie&limit=2" | jq '.results[].title'

# Wyszukaj informacje o weterynarzach
curl -s "http://localhost:8000/search?q=weterynarz&limit=2" | jq '.results[].chunk_index'

# Wyszukaj informacje o szczotkowaniu
curl -s "http://localhost:8000/search?q=szczotkowanie&limit=2" | jq '.results[].distance'
```

### Integracja z RAG (LLM)

```python
import requests
import openai  # lub inna biblioteka LLM

def rag_query(user_question):
    # 1. Wyszukaj relevantne chunki
    search_response = requests.get('http://localhost:8000/search', params={
        'q': user_question,
        'limit': 3
    })
    chunks = search_response.json()['results']
    
    # 2. Przygotuj kontekst dla LLM
    context = "\n\n".join([
        f"Fragment {i+1} (z '{chunk['title']}'):\n{chunk['body']}"
        for i, chunk in enumerate(chunks)
    ])
    
    # 3. Zapytaj LLM z kontekstem
    prompt = f"""Odpowiedz na pytanie używając poniższego kontekstu:

Kontekst:
{context}

Pytanie: {user_question}

Odpowiedź:"""
    
    # Wyślij do LLM (OpenAI, Claude, itp.)
    # response = openai.chat.completions.create(...)
    
    return response

# Użycie
answer = rag_query("Jak często karmić kota?")
```

---

## 🔗 Dostęp z Zewnątrz (Opcjonalnie)

Jeśli chcesz wywoływać endpoint z zewnątrz (nie localhost):

### 1. Przez Tunel (ngrok)

```bash
# Zainstaluj ngrok
brew install ngrok  # macOS

# Utwórz tunel
ngrok http 8000

# Użyj URL z ngrok
curl "https://abc123.ngrok.io/search?q=kot&limit=3"
```

### 2. Przez Publiczny Serwer

Wdróż aplikację na:
- **Railway** / **Render** / **Fly.io** (darmowe tier)
- **AWS** / **GCP** / **Azure**
- **VPS** (DigitalOcean, Linode, itp.)

---

## 📚 Dokumentacja API

Interaktywna dokumentacja dostępna pod:

```
http://localhost:8000/docs
```

Tam możesz:
- Przetestować endpoint bezpośrednio w przeglądarce
- Zobaczyć dokładny format request/response
- Skopiować przykłady curl

---

## ✅ Podsumowanie

**Endpoint działa już teraz!** Możesz go używać:

✅ Z curl (terminal)
✅ Z przeglądarki (Chrome/Firefox)
✅ Z n8n workflow (HTTP Request node)
✅ Z JavaScript/Python/dowolnego języka
✅ Z zewnętrznych aplikacji (przez ngrok/tunel)

**Nie musisz nic dodawać - wszystko już działa!** 🎉
