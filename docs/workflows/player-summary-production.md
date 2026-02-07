# Player Summary Production Update Workflow

## Overview

This workflow automatically generates and updates player summaries on the production Grill Ekstraklasa API using AI (Gemini) and Wikipedia data.

## Workflow: 5. Grill Production Update Player

**File:** `n8n_workflows/5_grill_production_update.json`

### Purpose

Generates humorous, meme-style player descriptions and updates them directly on the production server via REST API.

### Architecture

```
Webhook → Fetch Production API → Parse Players → Wikipedia Search → 
Process Data → Gemini AI Generation → Parse Response → Update Production → 
Aggregate Results → Respond
```

### Node Details

#### 1. Webhook Trigger
- **Endpoint:** `POST /webhook/grill-production-update`
- **Input:** JSON with `name` or `slug` or empty for all players
- **Examples:**
  ```bash
  # Update single player by name
  curl -X POST http://localhost:5678/webhook/grill-production-update \
    -H "Content-Type: application/json" \
    -d '{"name": "Arkadiusz Reca"}'
  
  # Update single player by slug
  curl -X POST http://localhost:5678/webhook/grill-production-update \
    -H "Content-Type: application/json" \
    -d '{"slug": "arkadiusz-reca"}'
  ```

#### 2. Fetch Players from Production API
- **URL:** `https://grillekstraklasa.pl/api/players/`
- **Method:** GET
- **Query params:** Based on input (name, slug, or all)

#### 3. Parse Players
- **Type:** Code node
- **Mode:** runOnceForAllItems
- **Output:** Array of player objects with id, name, slug, club_name

#### 4. Wikipedia Search (PL)
- **URL:** `https://pl.wikipedia.org/w/api.php`
- **Parameters:**
  - `action=query`
  - `format=json`
  - `prop=extracts|pageimages`
  - `exintro=1` (intro only)
  - `explaintext=1` (plain text)

#### 5. Process Wikipedia Data
- **Type:** Code node
- **Extracts:** Player bio from Wikipedia response
- **Handles:** Missing data (pageId = -1)

#### 6. Generate Summary with Gemini
- **Model:** gemini-2.0-flash
- **API Key:** From `$env.GEMINI_API_KEY`
- **Prompt Style:** Humorous, meme-focused, Ekstraklasa-specific
- **Output:** JSON with `summary` field (4-5 sentences)

#### 7. Parse Gemini Response
- **Type:** Code node
- **Cleans:** Removes markdown code blocks
- **Parses:** JSON response from Gemini
- **Error handling:** Returns error message if parsing fails

#### 8. Update Player on Production
- **Method:** PATCH
- **URL:** `https://grillekstraklasa.pl/api/players/{slug}/`
- **Headers:**
  - `Authorization: Token {GRILL_ADMIN_TOKEN}`
  - `Content-Type: application/json`
- **Body:** `{"summary": "generated text"}`

#### 9. Aggregate Results
- **Type:** Code node
- **Mode:** runOnceForAllItems
- **Output:** Summary with count and player list

#### 10. Respond - Success
- **Type:** Respond to Webhook
- **Format:** JSON with status, count, and players array

## Configuration

### Environment Variables

Required in `vector/.env`:

```bash
# Gemini API Key - for AI text generation
GEMINI_API_KEY=your_gemini_api_key_here

# Grill Ekstraklasa Admin Token - for production API updates
GRILL_ADMIN_TOKEN=your_production_admin_token_here
```

### Docker Compose Setup

The `docker-compose.yml` must include these environment variables for n8n:

```yaml
n8n:
  environment:
    GEMINI_API_KEY: ${GEMINI_API_KEY:-}
    GRILL_ADMIN_TOKEN: ${GRILL_ADMIN_TOKEN:-}
```

### Getting Production Admin Token

SSH to production server and run:

```bash
cd /home/ec2-user/grill-ekstraklasa/backend
source venv/bin/activate
python manage.py shell
```

Then in Python shell:

```python
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
user = User.objects.get(username='adminpazax')
token, created = Token.objects.get_or_create(user=user)
print(token.key)
```

## Usage

### Import Workflow to n8n

1. Open n8n at `http://localhost:5678`
2. Login with credentials: `admin/admin`
3. Go to **Workflows** → **Import from File**
4. Select `n8n_workflows/5_grill_production_update.json`
5. Save and activate the workflow

### Restart n8n After Environment Changes

When you update `.env` file, restart n8n:

```bash
cd /Users/brakuzy/Code/personal/vector
docker compose stop n8n
docker compose up -d n8n
```

Verify environment variable is loaded:

```bash
docker exec vector_n8n printenv GRILL_ADMIN_TOKEN
```

### Test Workflow

Update single player:

```bash
curl -X POST http://localhost:5678/webhook/grill-production-update \
  -H "Content-Type: application/json" \
  -d '{"name": "Arkadiusz Reca"}'
```

### Verify Update

Check production API:

```bash
curl -s "https://grillekstraklasa.pl/api/players/arkadiusz-reca/" | jq '.summary'
```

## Example Response

```json
{
  "status": "success",
  "count": 1,
  "players": [
    {
      "name": "Arkadiusz Reca",
      "slug": "arkadiusz-reca",
      "summary": "Arkadiusz Reca, człowiek-instytucja na lewej obronie... Legii, oczywiście..."
    }
  ]
}
```

## Troubleshooting

### Error: "Invalid token"

1. Verify token in `.env` is correct (no extra spaces/newlines)
2. Restart n8n container: `docker compose stop n8n && docker compose up -d n8n`
3. Check token is loaded: `docker exec vector_n8n printenv GRILL_ADMIN_TOKEN`
4. Test token with curl:
   ```bash
   curl -X PATCH https://grillekstraklasa.pl/api/players/arkadiusz-reca/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"summary": "test"}'
   ```

### Error: "No credentials provided"

- Check Authorization header format in workflow: `={{ 'Token ' + $env.GRILL_ADMIN_TOKEN }}`
- Re-import workflow JSON after fixing

### Wikipedia Returns No Data

- Normal for lesser-known players
- Gemini will generate fictional but humorous profile
- Summary still gets created and updated

## Related Documentation

- [n8n Production Setup](../n8n-production-setup.md)
- [Player Profile Generator (Local)](./player-profile-generation.md)
- [Grill Ekstraklasa API Reference](../api-reference.md)
