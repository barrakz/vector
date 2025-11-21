#!/bin/bash
echo "=== Test Wielojęzyczności - Polski vs Angielski ==="
echo ""

# Test 1: Dodaj dokument po polsku
echo "1. Dodawanie dokumentu PO POLSKU..."
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Psy - Przewodnik",
    "body": "Pies to wierny przyjaciel człowieka. Psy potrzebują regularnych spacerów i odpowiedniej diety. Karmienie psa powinno odbywać się dwa razy dziennie. Psy lubią bawić się piłką i innymi zabawkami. Regularne wizyty u weterynarza są kluczowe dla zdrowia psa.",
    "metadata": {"lang": "pl", "category": "pets", "url": "https://example.com/psy-pl"}
  }' | python3 -m json.tool

echo ""
echo "2. Dodawanie dokumentu PO ANGIELSKU..."
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dogs - Complete Guide",
    "body": "A dog is a loyal companion. Dogs need regular walks and proper diet. Feeding your dog should happen twice daily. Dogs love playing with balls and other toys. Regular veterinary visits are crucial for dog health.",
    "metadata": {"lang": "en", "category": "pets", "url": "https://example.com/dogs-en"}
  }' | python3 -m json.tool

echo ""
echo "3. Wyszukiwanie PO POLSKU: 'karmienie psa'"
curl -s "http://localhost:8000/search?q=karmienie+psa&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    lang: .metadata.lang,
    distance,
    preview: .body[:100]
  })
}'

echo ""
echo "4. Wyszukiwanie PO ANGIELSKU: 'feeding dog'"
curl -s "http://localhost:8000/search?q=feeding+dog&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    lang: .metadata.lang,
    distance,
    preview: .body[:100]
  })
}'

echo ""
echo "5. Wyszukiwanie MIESZANE: 'veterinary' (angielskie słowo)"
curl -s "http://localhost:8000/search?q=veterinary&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    lang: .metadata.lang,
    distance
  })
}'

echo ""
echo "6. Wyszukiwanie MIESZANE: 'weterynarz' (polskie słowo)"
curl -s "http://localhost:8000/search?q=weterynarz&limit=2" | jq '{
  query,
  results: .results | map({
    title,
    lang: .metadata.lang,
    distance
  })
}'

