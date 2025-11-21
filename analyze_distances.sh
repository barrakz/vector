#!/bin/bash
echo "=== Analiza Distance Scores ===" 
echo ""

echo "Test 1: Bardzo podobne zapytanie (exact match)"
curl -s "http://localhost:8000/search?q=karmienie+kota&limit=1" | jq '.results[0] | {title, distance, match: "EXACT"}'

echo ""
echo "Test 2: Podobne zapytanie (synonym)"
curl -s "http://localhost:8000/search?q=żywienie+kota&limit=1" | jq '.results[0] | {title, distance, match: "SYNONYM"}'

echo ""
echo "Test 3: Powiązane zapytanie"
curl -s "http://localhost:8000/search?q=opieka+nad+kotem&limit=1" | jq '.results[0] | {title, distance, match: "RELATED"}'

echo ""
echo "Test 4: Niepowiązane zapytanie"
curl -s "http://localhost:8000/search?q=piłka+nożna&limit=1" | jq '.results[0] | {title, distance, match: "UNRELATED"}'

echo ""
echo "Sprawdzenie embeddingów w bazie:"
docker exec vector_db psql -U app -d app -c "
SELECT 
    id,
    title,
    LEFT(body, 50) as preview,
    array_length(embedding::real[], 1) as embedding_dim
FROM chunks
LIMIT 3;
"

