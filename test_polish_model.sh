#!/bin/bash
echo "=== Test Wielojęzycznego Modelu - Polski ===
"
echo ""

# Wyczyść bazę (opcjonalnie - usuń stare embeddingi z angielskiego modelu)
echo "Czyszczenie starych danych..."
docker exec vector_db psql -U app -d app -c "TRUNCATE chunks CASCADE;" > /dev/null 2>&1
docker exec vector_db psql -U app -d app -c "TRUNCATE documents CASCADE;" > /dev/null 2>&1

echo ""
echo "1. Dodawanie polskiego artykułu o kotach..."
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Jak dbać o kota - kompletny przewodnik",
    "body": "Kot to wspaniałe zwierzę domowe, które wymaga odpowiedniej opieki. Karmienie kota powinno odbywać się regularnie, najlepiej dwa razy dziennie. Karma dla kota powinna być wysokiej jakości i zawierać dużo białka. Koty są mięsożercami i potrzebują odpowiedniej diety. Woda dla kota powinna być zawsze świeża i dostępna. Szczotkowanie kota jest bardzo ważne, szczególnie dla ras długowłosych. Regularne szczotkowanie pomaga usunąć martwe włosy i zapobiega powstawaniu kołtunów. Pazury kota również wymagają uwagi - kot potrzebujedrapaka. Zdrowie kota wymaga regularnych wizyt u weterynarza. Weterynarz powinien badać kota przynajmniej raz w roku. Szczepienia są kluczowe dla ochrony kota przed chorobami. Koty mogą żyć 15-20 lat przy odpowiedniej opiece.",
    "metadata": {"lang": "pl", "category": "zwierzęta", "url": "https://example.com/kot-pl"}
  }' | python3 -m json.tool

echo ""
echo "2. Dodawanie polskiego artykułu o psach..."
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Psy - wszystko co musisz wiedzieć",
    "body": "Pies to najlepszy przyjaciel człowieka. Psy wymagają codziennych spacerów i aktywności fizycznej. Karmienie psa powinno być dostosowane do jego rasy i wieku. Psy potrzebują wysokobiałkowej karmy i świeżej wody. Szczotkowanie psa zależy od rasy - długowłose psy wymagają codziennego szczotkowania. Pazury psa ścierają się naturalnie podczas spacerów. Weterynarz powinien regularnie badać psa. Szczepienia chronią psa przed niebezpiecznymi chorobami. Psy są bardzo lojalne i kochają swoich właścicieli.",
    "metadata": {"lang": "pl", "category": "zwierzęta", "url": "https://example.com/pies-pl"}
  }' | python3 -m json.tool

echo ""
echo "3. Wyszukiwanie: 'karmienie kota'"
curl -s "http://localhost:8000/search?q=karmienie+kota&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    distance,
    preview: .body[:80]
  })
}'

echo ""
echo "4. Wyszukiwanie: 'szczotkowanie'"
curl -s "http://localhost:8000/search?q=szczotkowanie&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    distance,
    preview: .body[:80]
  })
}'

echo ""
echo "5. Wyszukiwanie: 'weterynarz'"
curl -s "http://localhost:8000/search?q=weterynarz&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    distance,
    preview: .body[:80]
  })
}'

echo ""
echo "6. Wyszukiwanie: 'spacery z psem'"
curl -s "http://localhost:8000/search?q=spacery+z+psem&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    distance,
    preview: .body[:80]
  })
}'

echo ""
echo "7. Porównanie distance scores (niższe = lepsze):"
echo "   - Stary model (EN): ~1.1-1.3 dla polskiego"
echo "   - Nowy model (Multilingual): powinno być ~0.6-0.9"

