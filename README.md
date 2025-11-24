# Vector Embeddings Demo z FastAPI, PostgreSQL i pgvector

To jest projekt edukacyjny, który demonstruje:
- **Embeddingi wektorowe** używając **lokalnego modelu sentence-transformers** (bez klucza API!)
- **Wyszukiwanie semantyczne** z pgvector w PostgreSQL
- **JSONB** dla elastycznych metadanych dokumentów
- **FastAPI** dla REST API
- **n8n** dla automatyzacji workflow z ingestion artykułów przez webhook
- **Logowanie aplikacji** do śledzenia wszystkich operacji

Wszystkie usługi działają w Docker dla łatwego lokalnego developmentu.

---

## Funkcjonalności

✅ **Chunking gotowy dla RAG** - Dokumenty dzielone na fragmenty ~60 słów dla precyzyjnego wyszukiwania  
✅ **Wsparcie wielojęzyczne** - Działa z polskim, angielskim i 50+ językami  
✅ **Bez kosztów API** - Używa lokalnego modelu `paraphrase-multilingual-MiniLM-L12-v2`  
✅ **Wykrywanie duplikatów** - Automatycznie zapobiega duplikacji URL  
✅ **Ingestion przez webhook** - Dodawaj artykuły przez workflow n8n  
✅ **Logowanie aplikacji** - Śledź wszystkie operacje w `api/app.log`  
✅ **Wyszukiwanie semantyczne** - Znajdź relevantne fragmenty tekstu, nie tylko słowa kluczowe  

---

## Wymagania

- macOS z zainstalowanym i uruchomionym Docker Desktop
- **Bez klucza API!** Wszystko działa lokalnie.

---

## Instalacja

### 1. Skonfiguruj zmienne środowiskowe (opcjonalne)

Plik `.env` jest opcjonalny, ponieważ używamy lokalnych embeddingów:

```bash
cp .env.example .env
```

### 2. Zbuduj i uruchom stack Docker

Z tego katalogu uruchom:

```bash
docker compose up --build
```

To uruchomi trzy usługi:
- **PostgreSQL** z rozszerzeniem pgvector (port 5432)
- **FastAPI** backend (port 8000)
- **n8n** automatyzacja workflow (port 5678)

Poczekaj aż zobaczysz logi wskazujące, że wszystkie usługi są gotowe (zazwyczaj 20-30 sekund).

---

## Usługi

Po uruchomieniu możesz uzyskać dostęp do:

### FastAPI API
- **URL**: http://localhost:8000
- **Interaktywna dokumentacja**: http://localhost:8000/docs (Swagger UI)
- **Alternatywna dokumentacja**: http://localhost:8000/redoc

### n8n Automatyzacja Workflow
- **URL**: http://localhost:5678
- **Login**: 
  - Nazwa użytkownika: `admin`
  - Hasło: `admin`

---

## Testowanie API

### Przykład 1: Dodaj dokument

Dodaj dokument o kotach i psach (po polsku):

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Artykuł o kotach i psach",
    "body": "Kot śpi na kanapie, a pies biega po ogrodzie. Koty są leniwymi zwierzętami.",
    "metadata": {"category": "animals", "lang": "pl"}
  }'
```

Odpowiedź:
```json
{
  "status": "ok",
  "document_id": 1,
  "chunks_inserted": 1
}
```

Dodaj kolejny dokument:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Przepis na ciasto",
    "body": "Wymieszaj mąkę, cukier i jajka. Piecz w 180 stopniach przez 30 minut.",
    "metadata": {"category": "recipes", "lang": "pl"}
  }'
```

I jeszcze jeden (po angielsku):

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Article about dogs",
    "body": "Dogs are loyal companions. They love to play and run in the park.",
    "metadata": {"category": "animals", "lang": "en"}
  }'
```

### Przykład 2: Wyszukiwanie semantyczne

Wyszukaj dokumenty o kotach (po polsku):

```bash
curl "http://localhost:8000/search?q=kot&limit=3"
```

Lub o psach (po angielsku):

```bash
curl "http://localhost:8000/search?q=dog&limit=3"
```

Lub o przepisach/gotowaniu:

```bash
curl "http://localhost:8000/search?q=gotowanie&limit=3"
```

API zwróci dokumenty posortowane według podobieństwa semantycznego (najniższa odległość = najbardziej podobne).

### Przykład 3: Lista wszystkich dokumentów

```bash
curl http://localhost:8000/documents
```

---

## Używanie Workflow n8n

Projekt zawiera gotowe do użycia workflow n8n dla automatycznej ingestion artykułów.

### Import Workflow

1. Otwórz n8n: http://localhost:5678 (login: `admin` / `admin`)
2. Kliknij **trzy kropki** (prawy górny róg) → **Import from File**
3. Zaimportuj pliki z `n8n_workflows/`:
   - `1_ingest_from_url.json` - Pobierz i dodaj artykuły z URL
   - `2_search_documents.json` - Przeszukuj bazę wektorową

### Używanie Workflow Webhook

Workflow **Ingest from URL** akceptuje requesty POST:

**URL**: `http://localhost:5678/webhook/ingest-url`  
**Metoda**: `POST`  
**Body**:
```json
{
  "url": "https://example.com/article"
}
```

**Przykład z curl**:
```bash
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://weszlo.com/sylvinho-trener-reprezentacji-albanii-to-on-sprobuje-ograc-urbana/"}'
```

Workflow:
1. Pobierze HTML z URL
2. Wyciągnie tytuł i paragrafy
3. Wyśle do vector API
4. **Pominie jeśli URL już istnieje** (wykrywanie duplikatów)

Zobacz `docs/workflows/N8N_WORKFLOW_DOCS.md` dla szczegółowej dokumentacji n8n.

---

## Logowanie Aplikacji

Wszystkie operacje są logowane do `api/app.log`. Zobacz logi:

```bash
cat api/app.log
```

Lub w czasie rzeczywistym:
```bash
tail -f api/app.log
```

Wpisy logów zawierają:
- Ingestion dokumentów (tytuł, metadata, URL)
- Wykrywanie duplikatów (pominięte URL)
- Zapytania wyszukiwania (tekst zapytania, liczba wyników)
- Błędy i ostrzeżenia

---

## Jak To Działa

### 1. Ingestion Dokumentów (`POST /ingest`)

Kiedy wysyłasz dokument:
1. **Aplikacja FastAPI** sprawdza czy dokument z tym samym URL już istnieje
2. Jeśli istnieje, zwraca istniejący document ID (bez duplikatu)
3. W przeciwnym razie, **body dokumentu jest dzielone na chunki** (~60 słów każdy, 15 słów nakładki)
4. Każdy chunk otrzymuje swój własny **384-wymiarowy embedding wektorowy** używając lokalnego modelu `paraphrase-multilingual-MiniLM-L12-v2`
5. Chunki są przechowywane w **PostgreSQL** z:
   - `title` (dziedziczone z dokumentu)
   - `body` (tekst chunka, ~60 słów)
   - `metadata` jako **JSONB** (elastyczne przechowywanie JSON)
   - `embedding` jako **vector(384)** w kolumnie pgvector
   - `document_id` (link do dokumentu nadrzędnego)
   - `chunk_index` (pozycja w dokumencie)

**Dlaczego chunking?** To umożliwia RAG (Retrieval-Augmented Generation) poprzez zwracanie precyzyjnych, relevantnych fragmentów tekstu zamiast całych dokumentów.

### 2. Wyszukiwanie Semantyczne (`GET /search`)

Kiedy wyszukujesz:
1. Tekst zapytania jest konwertowany na wektor używając **lokalnego modelu wielojęzycznego** (bez wywołania API!)
2. PostgreSQL przeszukuje **tabelę chunks** używając **operatora `<->`** (odległość L2) aby znaleźć chunki z podobnymi embeddingami
3. Wyniki są sortowane według odległości (niższa = bardziej podobne)
4. API zwraca najbardziej relevantne **fragmenty tekstu** (chunki), nie całe dokumenty

**To oznacza, że wyszukiwanie rozumie znaczenie**, nie tylko słowa kluczowe! Na przykład, wyszukiwanie "karmienie kota" znajdzie konkretne chunki o karmieniu kotów, nawet jeśli dokładna fraza się różni.

**Idealne dla RAG:** Każdy wynik to fragment ~60 słów, który może być bezpośrednio użyty jako kontekst dla LLM.

### 3. Metadata JSONB

Każdy dokument może mieć elastyczne metadata przechowywane jako JSONB. To pozwala na:
- Szybkie zapytania na polach JSON (używając indeksu GIN)
- Elastyczny schemat (nie trzeba predefiniować wszystkich pól)
- Przykładowe zapytania SQL: 
  ```sql
  SELECT * FROM documents WHERE metadata->>'category' = 'animals';
  ```

### 4. pgvector

Rozszerzenie `pgvector` dodaje:
- Typ danych `vector` do przechowywania embeddingów
- Operatory odległości: `<->` (L2), `<=>` (cosine), `<#>` (iloczyn skalarny)
- Specjalizowane indeksy (IVFFlat, HNSW) dla szybkiego wyszukiwania podobieństwa

---

## Struktura Projektu

```
/Users/brakuzy/Code/personal/vector/
├── docker-compose.yml       # Definiuje 3 usługi (db, api, n8n)
├── .env.example             # Szablon zmiennych środowiskowych
├── .env                     # Twoja aktualna konfiguracja (git-ignored, opcjonalne)
├── .gitignore               # Reguły git ignore
├── README.md                # Ten plik
├── CHANGELOG.md             # Historia zmian
├── docs/                    # Dokumentacja projektu
│   ├── README.md            # Indeks dokumentacji
│   ├── technical/           # Dokumentacja techniczna
│   ├── workflows/           # Dokumentacja n8n
│   └── guides/              # Przewodniki użytkownika
├── n8n_workflows/           # Gotowe do importu workflow n8n
│   ├── 1_ingest_from_url.json
│   └── 2_search_documents.json
└── api/
    ├── Dockerfile           # Buduje kontener FastAPI
    ├── requirements.txt     # Zależności Python
    └── app/
        ├── main.py          # Aplikacja FastAPI z endpointami
        ├── db.py            # Helper połączenia z bazą danych
        ├── chunking.py      # Algorytm chunkowania tekstu
        └── app.log          # Logi aplikacji (auto-tworzone)
```

---

## Zatrzymywanie Usług

Naciśnij `Ctrl+C` w terminalu gdzie działa `docker compose`, lub uruchom:

```bash
docker compose down
```

Aby usunąć wszystkie dane (baza danych + wolumeny n8n):

```bash
docker compose down -v
```

---

## Chunking & RAG

Ta implementacja używa **chunkowania tekstu** aby umożliwić RAG (Retrieval-Augmented Generation):

- **Rozmiar chunka**: 60 słów (konfigurowalne w `api/app/chunking.py`)
- **Nakładka**: 15 słów (zachowuje kontekst między chunkami)
- **Korzyści**: Zwraca precyzyjne, relevantne fragmenty (2-3 zdania) zamiast całych dokumentów

### Dlaczego Chunking?

**Bez chunkowania:**
- Wyszukiwanie zwraca cały artykuł 5000 słów
- Relevantna informacja zakopana w środku
- Za dużo tekstu dla kontekstu LLM

**Z chunkowaniem:**
- Wyszukiwanie zwraca konkretny fragment 60 słów
- Precyzyjne dopasowanie semantyczne
- Idealny rozmiar dla kontekstu LLM
- Możliwe wiele relevantnych chunków z tego samego dokumentu

### Zmiana Rozmiaru Chunka

Edytuj `api/app/chunking.py`:
```python
def chunk_text(text: str, chunk_size: int = 60, overlap: int = 15):
    # Dostosuj chunk_size i overlap według potrzeb
```

---

## Wsparcie Wielojęzyczne

Projekt używa `paraphrase-multilingual-MiniLM-L12-v2` który wspiera 50+ języków w tym:
- Polski
- Angielski
- Niemiecki, Francuski, Hiszpański, Włoski
- I wiele więcej

### Zmiana Modelu

Aby użyć innego modelu, edytuj `api/app/main.py`:

```python
# Obecny: Wielojęzyczny (50+ języków, 384 wymiary)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Alternatywa: Tylko angielski (szybszy, mniejszy)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Alternatywa: Najlepsza jakość wielojęzyczna (768 wymiarów - wymaga zmiany schematu DB!)
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
```

**Uwaga:** Jeśli zmieniasz na model z innymi wymiarami (np. 768), musisz również zaktualizować `vector(384)` na `vector(768)` w `api/app/db.py` i przebudować bazę danych.

---

## Następne Kroki

Teraz gdy masz działającą konfigurację, możesz:

1. **Przetestować workflow RAG**: Dodaj długie artykuły, wyszukuj konkretne tematy, używaj wyników z LLM
2. **Eksperymentować z różnymi tekstami**: Spróbuj dodać dokumenty w różnych językach
3. **Testować wyszukiwanie semantyczne**: Zauważ jak znajduje podobne znaczenie, nie tylko pasujące słowa
4. **Eksplorować zapytania JSONB**: Dodaj bardziej złożone metadata i zapytuj je bezpośrednio w PostgreSQL
5. **Uczyć się n8n**: Twórz workflow, które automatycznie dodają dokumenty z zewnętrznych źródeł
6. **Dostosować rozmiar chunka**: Eksperymentuj z różnymi rozmiarami chunków dla swojego przypadku użycia
7. **Wypróbować różne modele**: Testuj modele tylko angielskie vs wielojęzyczne

---

## Przydatne Komendy

### Zobacz logi
```bash
docker compose logs -f api    # Logi FastAPI
docker compose logs -f db     # Logi PostgreSQL
docker compose logs -f n8n    # Logi n8n
```

### Zobacz logi aplikacji
```bash
cat api/app.log               # Wszystkie logi
tail -f api/app.log           # Śledź logi w czasie rzeczywistym
```

### Połącz się bezpośrednio z PostgreSQL
```bash
docker exec -it vector_db psql -U app -d app
```

Następnie możesz uruchomić zapytania SQL:
```sql
-- Zobacz tabelę documents
SELECT * FROM documents;

-- Sprawdź duplikaty
SELECT metadata->>'url' as url, COUNT(*) 
FROM documents 
WHERE metadata->>'url' IS NOT NULL 
GROUP BY metadata->>'url' 
HAVING COUNT(*) > 1;

-- Wyszukaj używając SQL bezpośrednio
SELECT id, title, embedding <-> '[0.1, 0.2, ...]'::vector AS distance
FROM chunks
ORDER BY distance
LIMIT 5;
```

### Przebuduj po zmianach w kodzie
```bash
docker compose up --build
```

---

## Rozwiązywanie Problemów

**Problem**: Ładowanie modelu trwa długo przy pierwszym starcie

**Rozwiązanie**: To normalne - model (~90MB) jest pobierany przy pierwszym uruchomieniu. Kolejne starty są znacznie szybsze.

**Problem**: Błędy połączenia z bazą danych

**Rozwiązanie**: Poczekaj trochę dłużej na inicjalizację PostgreSQL, lub zrestartuj: `docker compose restart api`

**Problem**: n8n się nie ładuje

**Rozwiązanie**: Daj mu minutę - n8n trwa trochę dłużej przy pierwszym uruchomieniu

**Problem**: Duplikaty dokumentów w bazie danych

**Rozwiązanie**: API teraz automatycznie zapobiega duplikatom na podstawie URL. Istniejące duplikaty można usunąć przez SQL.

---

## Dokumentacja

📚 **[Indeks Dokumentacji](docs/README.md)** - Cała dokumentacja uporządkowana według kategorii

### Szybkie Linki

- **[Dokumentacja Techniczna](docs/technical/DOKUMENTACJA_TECHNICZNA.md)** - Kompleksowy przewodnik techniczny
- **[Workflow n8n](docs/workflows/N8N_WORKFLOW_DOCS.md)** - Przewodnik automatyzacji workflow
- **[Przewodnik Chunkowania](docs/guides/CHUNKING_GUIDE.md)** - Jak działa chunking tekstu
- **[Przewodnik Wyszukiwania](docs/guides/SEARCH_ENDPOINT_GUIDE.md)** - Dokumentacja endpointu search
- **[Changelog](CHANGELOG.md)** - Historia wersji

---

Miłej nauki! 🚀
