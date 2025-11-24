# Przewodnik Chunkowania Tekstu

Ten dokument wyjaśnia jak działa chunking tekstu w projekcie Vector Embeddings i dlaczego jest niezbędny dla efektywnego RAG (Retrieval-Augmented Generation).

## Czym Jest Chunking Tekstu?

Chunking tekstu to proces dzielenia długich dokumentów na mniejsze, nakładające się segmenty przed generowaniem embeddingów. Zamiast tworzyć jeden embedding dla całego dokumentu, tworzymy wiele embeddingów dla mniejszych chunków.

## Dlaczego Używać Chunkingu?

### 1. **Lepsza Precyzja Semantyczna**
- Długie dokumenty obejmują wiele tematów
- Chunking pozwala każdemu tematowi mieć własny embedding
- Wyniki wyszukiwania są bardziej precyzyjne i relevantne

### 2. **Ulepszone Wyszukiwanie Kontekstu**
- Podczas wyszukiwania, otrzymujesz konkretne relevantne sekcje
- Nie cały dokument (który może zawierać nieistotne informacje)
- Lepsze dla aplikacji RAG gdzie kontekst ma znaczenie

### 3. **Ograniczenia Modeli Embeddingów**
- Większość modeli embeddingów ma limity tokenów
- Bardzo długie teksty mogą tracić znaczenie semantyczne
- Chunking utrzymuje każdy fragment w optymalnym rozmiarze

## Jak To Działa w Tym Projekcie

### Parametry Chunkowania
```python
chunk_size = 60     # słów na chunk (około 2-3 zdania)
overlap = 15        # nakładających się słów między chunkami
```

### Przykład

Dla dokumentu 500-słownego:

```
Chunk 1: słowa 0-59      (60 słów)
Chunk 2: słowa 45-104    (60 słów, 15 nakładki z Chunk 1)
Chunk 3: słowa 90-149    (60 słów, 15 nakładki z Chunk 2)
...
```

### Dlaczego Nakładka?

**Nakładające się chunki zachowują kontekst na granicach:**

- Bez nakładki: "...koniec zdania" | "Początek następnego..."
- Z nakładką: "...koniec zdania. Początek następnego..." | "Początek następnego zdania..."

To zapobiega utracie znaczenia gdy kluczowa koncepcja rozciąga się na granice chunków.

## Szczegóły Implementacji

### Lokalizacja Kodu

Logika chunkowania znajduje się w [`api/app/chunking.py`](../../api/app/chunking.py):

```python
def chunk_text(
    text: str, 
    chunk_size: int = 60, 
    overlap: int = 15
) -> List[str]:
    """Dzieli tekst na nakładające się chunki na podstawie liczby słów."""
    # Implementacja...
```

### Struktura Bazy Danych

Chunki są przechowywane w dedykowanej tabeli:

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    UNIQUE(document_id, chunk_index)
);
```

**Kluczowe punkty:**
- Każdy chunk ma własny embedding
- `chunk_index` zachowuje kolejność
- `document_id` łączy chunki z dokumentem nadrzędnym
- Kaskadowe usuwanie usuwa chunki gdy dokument jest usunięty

### Przepływ Ingestion

Kiedy wysyłasz POST do `/ingest`:

1. **Dokument otrzymany** (title, body, metadata)
2. **Sprawdzenie duplikatów** (po URL w metadata)
3. **Chunking tekstu** używając `chunk_text(body, 60, 15)`
4. **Generowanie embeddingów** dla każdego chunka
5. **Zapis w bazie danych**:
   - Dokument nadrzędny w tabeli `documents`
   - Chunki w tabeli `chunks`
6. **Zwrócenie odpowiedzi** z `document_id` i `chunks_inserted`

### Przepływ Wyszukiwania

Kiedy wysyłasz GET `/search?q=zapytanie`:

1. **Generowanie embeddingu zapytania**
2. **Przeszukiwanie tabeli chunks** (nie documents)
3. **Znajdowanie najbardziej podobnych chunków** używając odległości wektorowej
4. **Zwrócenie wyników** z zawartością chunka i metadata

## Dostosowywanie Parametrów Chunkowania

Możesz modyfikować zachowanie chunkowania w [`api/app/main.py`](../../api/app/main.py):

```python
# Obecne domyślne
chunks = chunk_text(request.body, chunk_size=60, overlap=15)

# Dla krótszych chunków (bardziej precyzyjne, więcej chunków)
chunks = chunk_text(request.body, chunk_size=40, overlap=10)

# Dla dłuższych chunków (mniej chunków, więcej kontekstu na chunk)
chunks = chunk_text(request.body, chunk_size=100, overlap=25)
```

### Rekomendacje

| Typ Dokumentu | Rozmiar Chunka | Nakładka | Powód |
|---------------|----------------|----------|-------|
| Krótkie odpowiedzi | 60-80 | 15-20 | Precyzyjne wyszukiwanie (2-3 zdania) |
| Standardowe artykuły | 100-200 | 30-50 | Balans kontekstu i precyzji |
| Długie analizy | 300-500 | 50-100 | Głęboki kontekst |
| Dokumentacja techniczna | 200-400 | 50-80 | Zachowanie kodu/przykładów |

## Testowanie Chunkowania

### Zobacz Chunki w Bazie Danych

```bash
docker exec -it vector_db psql -U app -d app -c "
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

### Zobacz Konkretne Chunki

```bash
docker exec -it vector_db psql -U app -d app -c "
  SELECT 
    chunk_index,
    LEFT(body, 100) as chunk_preview,
    LENGTH(body) as length
  FROM chunks
  WHERE document_id = 1
  ORDER BY chunk_index;
"
```

## Częste Pytania

### P: Dlaczego nie po prostu embeddować całego dokumentu?

**O:** Długie dokumenty często obejmują wiele tematów. Jeśli szukasz "karma dla kota", chcesz chunk o karmie dla kota, nie artykuł 5000-słowny gdzie karma dla kota jest wspomniana raz.

### P: Co się dzieje z bardzo krótkimi dokumentami?

**O:** Jeśli dokument jest krótszy niż `chunk_size`, jest przechowywany jako pojedynczy chunk. Nie następuje dzielenie.

### P: Czy mogę wyłączyć chunking?

**O:** Tak, ustaw `chunk_size` na bardzo dużą liczbę (np. 10000). Ale to niweluje cel RAG i może zmniejszyć jakość wyszukiwania.

### P: Jak chunking wpływa na wyniki wyszukiwania?

**O:** Wyszukiwanie zwraca **chunki**, nie dokumenty. Każdy wynik to chunk z jego `chunk_index` i nadrzędnym `document_id`. To daje Ci dokładną relevantną sekcję.

## Dalsze Czytanie

- [SEARCH_ENDPOINT_GUIDE.md](SEARCH_ENDPOINT_GUIDE.md) - Jak działa wyszukiwanie z chunkami
- [DOKUMENTACJA_TECHNICZNA.md](../technical/DOKUMENTACJA_TECHNICZNA.md) - Szczegóły implementacji technicznej
- [RAG Best Practices](https://www.pinecone.io/learn/chunking-strategies/) - Zewnętrzne źródło o strategiach chunkowania
