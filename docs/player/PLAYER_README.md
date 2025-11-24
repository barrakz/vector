# Player Profile Generator - Dokumentacja

System automatycznego generowania profili piłkarzy Ekstraklasy z wykorzystaniem n8n, Wikipedia API i Gemini AI.

## 🎯 Przegląd

**Player** to niezależny moduł aplikacji Vector, który automatycznie generuje szczegółowe profile piłkarzy na podstawie:
- Danych z Wikipedii (polska i angielska wersja)
- Analizy AI (Gemini) generującej charakterystykę i ocenę formy

**Kluczowe cechy:**
- ✅ Zero dodatkowych rejestracji (tylko Wikipedia + Gemini)
- ✅ Automatyczne wykrywanie duplikatów
- ✅ Łatwa edycja wygenerowanych profili
- ✅ Modularny workflow n8n (łatwa zmiana modelu AI)

---

## 🏗️ Architektura

```
POST /webhook/generate-player
↓
n8n Workflow:
  1. Sprawdzenie czy profil istnieje
  2. Wikipedia PL → ekstrakcja danych
  3. Wikipedia EN (fallback)
  4. Agregacja danych
  5. Gemini AI → generowanie profilu
  6. Zapis do bazy PostgreSQL
↓
Profil piłkarza gotowy!
```

---

## 🚀 Szybki Start

### 1. Uruchom stack Docker

```bash
cd /Users/brakuzy/Code/personal/vector
docker compose up --build
```

Usługi:
- FastAPI: `http://localhost:8000`
- n8n: `http://localhost:5678` (login: admin/admin)
- PostgreSQL: `localhost:5432`

### 2. Zaimportuj workflow n8n

1. Otwórz n8n: `http://localhost:5678`
2. Zaloguj się (admin/admin)
3. Kliknij **trzy kropki** → **Import from File**
4. Wybierz: `n8n_workflows/3_generate_player_profile.json`
5. Workflow zostanie zaimportowany

### 3. Aktywuj workflow

1. Otwórz zaimportowany workflow
2. Kliknij **Active** (przełącznik w prawym górnym rogu)
3. Workflow jest gotowy!

### 4. Wygeneruj pierwszy profil

```bash
curl -X POST http://localhost:5678/webhook/generate-player \
  -H "Content-Type: application/json" \
  -d '{"name": "Bartosz Kapustka"}'
```

**Odpowiedź:**
```json
{
  "status": "created",
  "profile": {
    "name": "Bartosz Kapustka",
    "summary": "...",
    "position": "pomocnik",
    "clubs": ["Legia Warszawa", "Leicester City", ...],
    "characteristics": "...",
    "strengths": "...",
    "weaknesses": "...",
    "estimated_current_form": "..."
  }
}
```

---

## 📡 API Endpoints

### Player API (FastAPI)

#### `POST /player/create`
Utwórz nowy profil piłkarza (używane przez n8n).

**Request:**
```json
{
  "name": "Jan Kowalski",
  "summary": "Polski piłkarz...",
  "position": "pomocnik",
  "clubs": ["Legia Warszawa"],
  "characteristics": "...",
  "strengths": "...",
  "weaknesses": "...",
  "estimated_current_form": "...",
  "metadata": {}
}
```

#### `GET /player/{player_id}`
Pobierz profil po ID.

```bash
curl http://localhost:8000/player/1
```

#### `GET /player/search?name=...`
Wyszukaj piłkarza po nazwisku.

```bash
curl "http://localhost:8000/player/search?name=Kapustka"
```

#### `PUT /player/{player_id}`
Edytuj profil piłkarza.

```bash
curl -X PUT http://localhost:8000/player/1 \
  -H "Content-Type: application/json" \
  -d '{
    "characteristics": "Zaktualizowana charakterystyka...",
    "estimated_current_form": "Bardzo dobra forma"
  }'
```

#### `DELETE /player/{player_id}`
Usuń profil.

```bash
curl -X DELETE http://localhost:8000/player/1
```

#### `GET /player/`
Lista wszystkich piłkarzy (z paginacją).

```bash
curl "http://localhost:8000/player/?limit=10&offset=0"
```

---

## 🔄 Workflow n8n - Szczegóły

### Przepływ danych (16 nodów)

1. **Webhook Trigger** - Przyjmuje POST z nazwą piłkarza
2. **Check if Player Exists** - Sprawdza duplikaty w bazie
3. **IF Player Exists** - Jeśli istnieje → zwraca profil, jeśli nie → kontynuuj
4. **Wikipedia Search (PL)** - Pobiera dane z polskiej Wikipedii
5. **Process Wikipedia PL** - Ekstraktuje tekst, zdjęcie, pozycję
6. **IF Need EN Wikipedia** - Jeśli PL jest pusta → pobierz EN
7. **Wikipedia Search (EN)** - Fallback do angielskiej Wikipedii
8. **Aggregate Data (with EN)** - Łączy dane PL + EN
9. **Aggregate Data (PL only)** - Tylko dane PL (jeśli wystarczające)
10. **Generate Profile with Gemini** - Wywołanie Gemini API z promptem
11. **Parse Gemini Response** - Parsowanie JSON z odpowiedzi AI
12. **IF Known Player** - Sprawdza czy AI zna zawodnika
13. **Save to Database** - Zapis profilu do PostgreSQL
14. **Respond - Profile Created** - Zwraca wygenerowany profil
15. **Respond - Already Exists** - Zwraca istniejący profil
16. **Respond - Unknown Player** - Brak danych o zawodniku

### Kluczowe nody

#### Wikipedia API Call
```
URL: https://pl.wikipedia.org/w/api.php
Parametry:
  - action=query
  - format=json
  - prop=extracts|pageimages
  - exintro=1
  - explaintext=1
  - titles={player_name}
  - piprop=thumbnail
  - pithumbsize=300
```

#### Gemini API Call
```
URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
Headers:
  - x-goog-api-key: {GEMINI_API_KEY}
Body: {
  "contents": [{
    "parts": [{
      "text": "Prompt z danymi o piłkarzu..."
    }]
  }]
}
```

---

## 🎨 Modyfikacja Workflow

### Zmiana modelu AI (Gemini → OpenAI)

1. Otwórz workflow w n8n
2. Znajdź node **"Generate Profile with Gemini"**
3. Zmień URL na: `https://api.openai.com/v1/chat/completions`
4. Zmień headers:
   ```
   Authorization: Bearer {OPENAI_API_KEY}
   Content-Type: application/json
   ```
5. Zmień body na format OpenAI:
   ```json
   {
     "model": "gpt-4",
     "messages": [{
       "role": "user",
       "content": "Prompt..."
     }]
   }
   ```
6. Zaktualizuj node **"Parse Gemini Response"** aby parsować odpowiedź OpenAI

### Dodanie nowych źródeł danych

**Przykład: Transfermarkt**

1. Dodaj nowy node **HTTP Request** po Wikipedia
2. URL: `https://www.transfermarkt.com/...`
3. Ekstraktuj dane (wartość rynkowa, statystyki)
4. Dodaj do node **Aggregate Data**
5. Zaktualizuj prompt Gemini aby uwzględnić nowe dane

---

## 🗄️ Baza Danych

### Tabela `players`

```sql
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    position VARCHAR(100) NOT NULL,
    clubs TEXT[] NOT NULL,
    characteristics TEXT NOT NULL,
    strengths TEXT NOT NULL,
    weaknesses TEXT NOT NULL,
    estimated_current_form TEXT NOT NULL,
    team VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indeksy:**
- `idx_players_name` - szybkie wyszukiwanie po nazwisku
- `idx_players_team` - filtrowanie po drużynie
- `idx_players_metadata` - zapytania JSONB

**Metadata zawiera:**
```json
{
  "sources": ["wikipedia"],
  "generated_at": "2025-11-24T12:00:00Z",
  "model": "gemini-pro",
  "has_wiki_data": true,
  "image_url": "https://..."
}
```

---

## 🧪 Testowanie

### Test 1: Generowanie profilu

```bash
curl -X POST http://localhost:5678/webhook/generate-player \
  -H "Content-Type: application/json" \
  -d '{"name": "Robert Lewandowski"}'
```

**Oczekiwany rezultat:** Profil z pełnymi danymi (Wikipedia PL + wiedza Gemini)

### Test 2: Duplikat

```bash
# Drugi raz ten sam piłkarz
curl -X POST http://localhost:5678/webhook/generate-player \
  -H "Content-Type: application/json" \
  -d '{"name": "Robert Lewandowski"}'
```

**Oczekiwany rezultat:** `{"status": "exists", "profile": {...}}`

### Test 3: Nieznany piłkarz

```bash
curl -X POST http://localhost:5678/webhook/generate-player \
  -H "Content-Type: application/json" \
  -d '{"name": "Jan Kowalski XYZ123"}'
```

**Oczekiwany rezultat:** `{"status": "unknown", "message": "Nie znaleziono danych..."}`

### Test 4: Edycja profilu

```bash
# Pobierz ID
curl "http://localhost:8000/player/search?name=Lewandowski"

# Edytuj
curl -X PUT http://localhost:8000/player/1 \
  -H "Content-Type: application/json" \
  -d '{"estimated_current_form": "Znakomita forma w Barcelonie"}'
```

### Weryfikacja w bazie

```bash
docker exec -it vector_db psql -U app -d app

# Lista piłkarzy
SELECT id, name, position, team FROM players;

# Szczegóły profilu
SELECT * FROM players WHERE name LIKE '%Lewandowski%';

# Metadata
SELECT metadata FROM players WHERE id = 1;
```

---

## 🔧 Troubleshooting

### Problem: Workflow nie działa

**Rozwiązanie:**
1. Sprawdź czy workflow jest **Active** (zielony przełącznik)
2. Sprawdź logi n8n: `docker compose logs -f n8n`
3. Sprawdź czy GEMINI_API_KEY jest ustawiony:
   ```bash
   docker exec vector_n8n env | grep GEMINI
   ```

### Problem: Gemini zwraca błąd 403

**Rozwiązanie:**
- Sprawdź czy klucz API jest poprawny
- Sprawdź limity API w Google Cloud Console
- Upewnij się że Gemini API jest włączone w projekcie

### Problem: Wikipedia nie zwraca danych

**Rozwiązanie:**
- Sprawdź pisownię nazwiska (wielkość liter ma znaczenie)
- Spróbuj wersji angielskiej (EN)
- Sprawdź czy strona Wikipedia istnieje ręcznie

### Problem: Profil jest niepełny

**Rozwiązanie:**
- Sprawdź logi workflow w n8n (kliknij na node → View Executions)
- Zobacz co zwróciła Wikipedia (node "Process Wikipedia PL")
- Zobacz co wygenerował Gemini (node "Parse Gemini Response")
- Dostosuj prompt Gemini jeśli potrzeba

---

## 📊 Przykładowe Profile

### Bartosz Kapustka

```json
{
  "name": "Bartosz Kapustka",
  "summary": "Polski piłkarz, pomocnik. Wychowanek Legii Warszawa, reprezentant Polski.",
  "position": "pomocnik",
  "clubs": ["Legia Warszawa", "Leicester City", "OH Leuven", "Legia Warszawa"],
  "characteristics": "Szybki, techniczny pomocnik ofensywny. Dobry drybling i podania.",
  "strengths": "Szybkość, technika, kreowanie gry",
  "weaknesses": "Fizyczność, skuteczność w wykańczaniu akcji",
  "estimated_current_form": "Bardzo dobra, kluczowy zawodnik Legii"
}
```

---

## 🚀 Następne Kroki

### Rozszerzenia

1. **Automatyczne odświeżanie** - Cron w n8n do aktualizacji profili
2. **Więcej źródeł** - Transfermarkt, Sofascore, oficjalne strony klubów
3. **Statystyki** - Integracja z API statystyk meczowych
4. **Porównywanie** - Endpoint do porównywania dwóch piłkarzy
5. **UI** - Prosty frontend do przeglądania profili

### Optymalizacje

- Cache dla Wikipedia API (zmniejszenie liczby requestów)
- Batch processing (generowanie wielu profili naraz)
- Webhook notifications (powiadomienia o nowych profilach)

---

## 📚 Dokumentacja Techniczna

- **[Implementation Plan](../../.gemini/antigravity/brain/5b24ead0-6860-4a9e-949d-7eab9aa0001a/implementation_plan.md)** - Szczegółowy plan implementacji
- **[API Code](../../api/app/player.py)** - Kod źródłowy endpointów
- **[Database Migration](../../api/migrations/002_add_players_table.sql)** - Migracja SQL
- **[n8n Workflow](../../n8n_workflows/3_generate_player_profile.json)** - Workflow JSON

---

## 💡 Tips & Tricks

### Optymalizacja promptu Gemini

Obecny prompt można dostosować w node "Generate Profile with Gemini":
- Dodaj więcej kontekstu (np. "specjalizujesz się w Ekstraklasie")
- Zmień format odpowiedzi (np. dodaj pole "market_value")
- Dostosuj długość opisów (np. "2-3 zdania" → "1 zdanie")

### Batch import piłkarzy

Utwórz plik `players.txt`:
```
Bartosz Kapustka
Robert Lewandowski
Wojciech Szczęsny
```

Uruchom:
```bash
while read player; do
  curl -X POST http://localhost:5678/webhook/generate-player \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$player\"}"
  sleep 2  # Rate limiting
done < players.txt
```

---

Miłego używania! 🚀⚽
