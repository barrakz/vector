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
    "summary": "Bartosz Kapustka to utalentowany polski pomocnik, który swoją karierę rozpoczynał w Cracovii. Mimo trudności w Leicester City, w Legii Warszawa odbudował swoją pozycję, stając się kluczowym rozgrywającym. Cechuje go świetna technika użytkowa, wizja gry i umiejętność gry kombinacyjnej. Obecnie prezentuje wysoką formę, będąc jednym z liderów Ekstraklasy.",
    "metadata": { ... }
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
  "summary": "Jan Kowalski to obiecujący napastnik, który wyróżnia się szybkością i instynktem strzeleckim...",
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
    "summary": "Zaktualizowany opis kariery i formy zawodnika..."
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

## 🧠 Jak działa generowanie profilu (AI & Workflow)

Proces generowania profilu piłkarza jest w pełni zautomatyzowany dzięki n8n i składa się z kilku kluczowych etapów. Poniżej znajdziesz szczegółowy opis każdego z nich.

### 1. Pobieranie danych (Wikipedia)
Workflow najpierw próbuje znaleźć informacje o piłkarzu w **polskiej Wikipedii**.
- Jeśli znajdzie artykuł, pobiera jego treść (extract) oraz zdjęcie (thumbnail).
- Jeśli dane z polskiej Wikipedii są skąpe (mniej niż 50 znaków) lub artykuł nie istnieje, workflow automatycznie przeszukuje **angielską Wikipedię**.
- Dane z obu źródeł są agregowane, aby dostarczyć modelowi AI jak najwięcej kontekstu.
- **Anonimowość:** Zapytania do Wikipedii są wysyłane z nagłówkiem `User-Agent`, ale bez logowania, co zapewnia zgodność z polityką API Wikipedii.

### 2. Generowanie profilu (Gemini API)
Zgromadzone dane tekstowe są przesyłane do modelu **Google Gemini** (obecnie używany model: `gemini-2.0-flash`).

**Prompt (Instrukcja dla AI):**
Model otrzymuje precyzyjną instrukcję (prompt), która definiuje jego rolę i zadanie:
> "Jesteś ekspertem od piłki nożnej, specjalizujesz się w Ekstraklasie polskiej. ZADANIE: Na podstawie poniższych danych z Wikipedii, wygeneruj szczegółowy profil piłkarza."

**Dane wejściowe dla modelu:**
- Nazwa piłkarza
- Surowy tekst z Wikipedii (PL i/lub EN)
- Wykryta pozycja (z prostego parsowania tekstu)

**Logika modelu:**
Model ma za zadanie:
1. Przeanalizować tekst z Wikipedii.
2. Uzupełnić go o **własną wiedzę** (jeśli dane z Wiki są niepełne, a model "zna" zawodnika).
3. Wygenerować ustrukturyzowany obiekt JSON zawierający pole `summary` z opisem (4-5 zdań) uwzględniającym:
   - Skrót kariery
   - Charakterystykę gry
   - Ocenę potencjału/formy

### 3. Zapis do bazy (UPSERT)
Wygenerowany JSON jest przesyłany do Twojego API (`POST /player/create`).
- System używa mechanizmu **UPSERT** (Update or Insert).
- Jeśli piłkarz o takim nazwisku już istnieje, jego dane są **aktualizowane**.
- Jeśli to nowy piłkarz, tworzony jest **nowy rekord**.

---

## ⚙️ Konfiguracja i Modyfikacje

### Jak zmienić prompt dla AI?
Prompt znajduje się bezpośrednio w workflow n8n, w nodzie **"Generate Profile with Gemini"**.
1. Otwórz workflow w n8n.
2. Kliknij dwukrotnie node **"Generate Profile with Gemini"**.
3. W sekcji `Body Parameters` -> `contents` -> `parts` -> `text` znajdziesz treść promptu.
4. Możesz go edytować, np. aby zmienić styl opisu, dodać nowe pola do JSON-a lub zmienić język.

### Czy Gemini korzysta tylko z Wikipedii?
**Nie tylko.** Prompt instruuje model: *"Jeśli masz dane z Wikipedii LUB znasz zawodnika"*.
- **Wikipedia** jest głównym źródłem faktów (kluby, historia).
- **Wiedza własna modelu** jest używana do uzupełnienia charakterystyki, stylu gry i oceny formy, szczególnie gdy Wikipedia zawiera tylko suche fakty.
- Dzięki temu opisy są bardziej "ludzkie" i analityczne, a nie tylko kopią encyklopedii.

### Zmiana modelu AI
Obecnie workflow używa `gemini-2.0-flash`. Aby to zmienić (np. na `gemini-1.5-pro`):
1. W nodzie **"Generate Profile with Gemini"** zmień URL na: `.../models/gemini-1.5-pro:generateContent`.
2. W nodzie **"Parse Gemini Response"** zaktualizuj pole `model` w kodzie JavaScript (dla celów statystycznych w metadanych).

---

## 🛠️ Troubleshooting

### Błąd "The resource you are requesting could not be found"
Oznacza to zazwyczaj, że wybrany model (np. `gemini-pro`) nie jest dostępny w używanej wersji API (`v1beta`). Upewnij się, że używasz modelu dostępnego dla Twojego klucza API (np. `gemini-2.0-flash`).

### Błąd "Forbidden" (Wikipedia)
Wikipedia blokuje requesty bez nagłówka `User-Agent`. Workflow ma to już skonfigurowane ("n8n-player-bot/1.0"), więc nie powinno to sprawiać problemów. Jeśli wystąpi, sprawdź nody "Wikipedia Search".

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
  "summary": "Bartosz Kapustka to dynamiczny pomocnik, wychowanek Tarnovii, który wypłynął na szerokie wody w Cracovii. Jego kariera wyhamowała po transferze do Leicester City, ale w Legii Warszawa odzyskał radość z gry. Cechuje go świetna technika, wizja gry i umiejętność gry kombinacyjnej. Obecnie prezentuje wysoką formę, będąc liderem drugiej linii Wojskowych."
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
