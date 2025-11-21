#!/bin/bash
# Przykłady użycia /search endpoint

echo "=== 1. Proste wyszukiwanie ==="
curl -s "http://localhost:8000/search?q=kot&limit=2" | python3 -m json.tool | head -20

echo ""
echo "=== 2. Wyszukiwanie z polskimi znakami ==="
curl -s "http://localhost:8000/search?q=karmienie&limit=1" | jq '.results[0].title'

echo ""
echo "=== 3. Tylko tytuły wyników ==="
curl -s "http://localhost:8000/search?q=weterynarz&limit=3" | jq '.results[].title'

echo ""
echo "=== 4. Tylko distance scores ==="
curl -s "http://localhost:8000/search?q=szczotkowanie&limit=3" | jq '.results[] | {title, distance}'

echo ""
echo "=== 5. Chunk indexes ==="
curl -s "http://localhost:8000/search?q=kot&limit=5" | jq '.results[] | {chunk_index, document_id}'

