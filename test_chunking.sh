#!/bin/bash
# Test script for chunking functionality

echo "=== Test 1: Ingest a long document with chunking ==="
echo ""

# Create a long text (500+ words)
LONG_TEXT="Kot to zwierzę domowe należące do rodziny kotowatych. Koty są jednymi z najpopularniejszych zwierząt domowych na świecie. Historia kotów sięga starożytnego Egiptu, gdzie były one czczone jako święte zwierzęta. Koty charakteryzują się niezależnym charakterem i silnym instynktem łowieckim. Są zwierzętami terytorialnymi, które potrzebują własnej przestrzeni. W domu kot powinien mieć dostęp do bezpiecznych miejsc, gdzie może się schronić. Koty są mięsożercami i wymagają diety bogatej w białko zwierzęce. Prawidłowe żywienie kota jest kluczowe dla jego zdrowia. Karmienie kota wymaga regularności i odpowiedniego doboru karmy. Najlepsze jedzenie dla kota to karma wysokobiałkowa, która zawiera wszystkie niezbędne składniki odżywcze. Warto również pamiętać o regularnym dostępie do świeżej wody. Koty powinny być karmione 2-3 razy dziennie, w stałych porach. Unikaj karmienia kota resztkami ze stołu, ponieważ wiele produktów przeznaczonych dla ludzi jest toksycznych dla kotów. Świeża woda powinna być zawsze dostępna. Niektóre koty preferują wodę bieżącą, dlatego warto rozważyć zakup fontanny dla kota. Pamiętaj, że mleko krowie nie jest odpowiednie dla dorosłych kotów, ponieważ większość z nich nie toleruje laktozy. Regularność w karmieniu pomaga utrzymać zdrową wagę kota i zapobiega problemom żołądkowym. Jeśli zauważysz, że kot odmawia jedzenia przez więcej niż 24 godziny, skonsultuj się z weterynarzem. Opieka nad kotem obejmuje również regularne szczotkowanie sierści. Szczotkowanie pomaga usunąć martwe włosy i zapobiega powstawaniu kołtunów. Koty długowłose wymagają codziennego szczotkowania, podczas gdy koty krótkowłose można szczotkować 2-3 razy w tygodniu. Regularne szczotkowanie zmniejsza również ilość sierści połykanej przez kota podczas toalety. Koty są bardzo czyste i spędzają dużo czasu na pielęgnacji swojej sierści. Ważnym elementem opieki nad kotem jest również dbanie o jego pazury. Koty potrzebują drapaka, aby mogły naturalnie ścierać pazury. Regularne przycinanie pazurów może być konieczne, szczególnie u kotów mieszkających w domu. Zdrowie kota wymaga regularnych wizyt u weterynarza. Coroczne badania kontrolne pozwalają na wczesne wykrycie ewentualnych problemów zdrowotnych. Szczepienia są kluczowe dla ochrony kota przed chorobami zakaźnymi. Koty powinny być szczepione przeciwko wściekliźnie, kociej panleukopenii i kociej grypie. Regularne odrobaczanie i ochrona przed pchłami są również ważne dla zdrowia kota. Koty mogą żyć od 12 do 20 lat, a niektóre nawet dłużej przy odpowiedniej opiece. Starsze koty wymagają specjalnej uwagi i mogą potrzebować zmian w diecie. Zachowanie kota może wiele powiedzieć o jego samopoczuciu. Koty komunikują się za pomocą mruczenia, miauczenia i języka ciała. Mruczenie zazwyczaj oznacza zadowolenie, ale może również sygnalizować ból lub stres. Koty machające ogonem są zazwyczaj zdenerwowane lub podekscytowane. Zrozumienie języka ciała kota pomaga w budowaniu silnej więzi z pupilem."

curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Kompletny przewodnik po kotach\",
    \"body\": \"$LONG_TEXT\",
    \"metadata\": {\"category\": \"pets\", \"animal\": \"cat\", \"url\": \"https://example.com/cat-guide\"}
  }" | python3 -m json.tool

echo ""
echo "=== Test 2: Check chunks in database ==="
docker exec vector_db psql -U app -d app -c "
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

echo ""
echo "=== Test 3: View first 3 chunks ==="
docker exec vector_db psql -U app -d app -c "
SELECT 
    chunk_index,
    LEFT(body, 100) as chunk_preview,
    LENGTH(body) as length
FROM chunks
WHERE document_id = (SELECT MAX(id) FROM documents)
ORDER BY chunk_index
LIMIT 3;
"

echo ""
echo "=== Test 4: Search for 'karmienie kota' ==="
curl -s "http://localhost:8000/search?q=karmienie+kota&limit=3" | python3 -m json.tool

echo ""
echo "=== Test 5: Search for 'szczotkowanie sierści' ==="
curl -s "http://localhost:8000/search?q=szczotkowanie+sierści&limit=2" | python3 -m json.tool
