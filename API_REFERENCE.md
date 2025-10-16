# API Quick Reference

## Base URL
```
http://localhost:8000
```

---

## System Endpoints

### Health Check
```http
GET /health
```
**Response**: `{ "status": "healthy", "service": "vectordb-q" }`

### Root
```http
GET /
```
**Response**: API information

### Documentation
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI Schema: `GET /openapi.json`

---

## Library Endpoints

### Create Library
```http
POST /api/v1/libraries
Content-Type: application/json

{
  "name": "My Library",
  "description": "Optional description",
  "metadata": {
    "category": "research",
    "language": "en",
    "tags": ["ai", "ml"]
  },
  "index_type": "flat"  // or "ivf"
}
```

### List All Libraries
```http
GET /api/v1/libraries
```

### Get Library by ID
```http
GET /api/v1/libraries/{library_id}
```

### Update Library
```http
PUT /api/v1/libraries/{library_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Library
```http
DELETE /api/v1/libraries/{library_id}
```

---

## Chunk Endpoints

### Create Chunk
```http
POST /api/v1/libraries/{library_id}/chunks
Content-Type: application/json

{
  "text": "Your text content here",
  "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
  "metadata": {
    "source": "Document name",
    "page": 1,
    "section": "Introduction",
    "tags": ["tag1", "tag2"]
  }
}
```

### List All Chunks in Library
```http
GET /api/v1/libraries/{library_id}/chunks
```

### Get Chunk by ID
```http
GET /api/v1/libraries/{library_id}/chunks/{chunk_id}
```

### Update Chunk
```http
PUT /api/v1/libraries/{library_id}/chunks/{chunk_id}
Content-Type: application/json

{
  "text": "Updated text",
  "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]
}
```

### Delete Chunk
```http
DELETE /api/v1/libraries/{library_id}/chunks/{chunk_id}
```

---

## Search Endpoint

### k-NN Vector Search
```http
POST /api/v1/libraries/{library_id}/search
Content-Type: application/json

{
  "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
  "k": 10,
  "metric": "euclidean",  // or "cosine"
  "filters": {            // Optional
    "source": "Document name",
    "tags": ["tag1"]
  }
}
```

**Response**:
```json
[
  {
    "chunk": {
      "id": "uuid",
      "text": "Chunk text",
      "embedding": [0.1, 0.2, 0.3],
      "metadata": {...},
      "created_at": "2025-10-16T...",
      "updated_at": "2025-10-16T..."
    },
    "score": 0.95,      // Similarity score (higher = better)
    "distance": 0.123   // Distance value (lower = better)
  }
]
```

---

## Distance Metrics

### Euclidean Distance
- Traditional L2 norm
- Formula: `√(Σ(qi - pi)²)`
- Good for: absolute distances
- Score calculation: `1 / (1 + distance)`

### Cosine Similarity
- Angle-based similarity
- Formula: `(q · p) / (||q|| ||p||)`
- Good for: direction similarity (magnitude-independent)
- Score calculation: `1 - distance`

---

## cURL Examples

### Create Library
```bash
curl -X POST http://localhost:8000/api/v1/libraries \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Library",
    "description": "A test library",
    "index_type": "flat"
  }'
```

### Add Chunk
```bash
curl -X POST http://localhost:8000/api/v1/libraries/{library_id}/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sample text",
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "metadata": {
      "source": "test",
      "tags": ["sample"]
    }
  }'
```

### Search with Euclidean
```bash
curl -X POST http://localhost:8000/api/v1/libraries/{library_id}/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "k": 5,
    "metric": "euclidean"
  }'
```

### Search with Cosine
```bash
curl -X POST http://localhost:8000/api/v1/libraries/{library_id}/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "k": 5,
    "metric": "cosine"
  }'
```

---

## Status Codes

- `200 OK` - Successful GET/PUT
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Metadata Filtering

Filters support:
- **Exact match**: `{"source": "Document.pdf"}`
- **Substring match** (case-insensitive): `{"source": "Doc"}`
- **List membership**: `{"category": ["research", "education"]}`
- **Nested fields**: `{"custom.field": "value"}`

Example:
```json
{
  "embedding": [0.1, 0.2, 0.3],
  "k": 10,
  "filters": {
    "source": "Research Paper",
    "page": 5,
    "tags": ["AI", "ML"]
  }
}
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Create library
response = requests.post(
    f"{BASE_URL}/api/v1/libraries",
    json={
        "name": "My Library",
        "index_type": "flat"
    }
)
library_id = response.json()["id"]

# Add chunk
response = requests.post(
    f"{BASE_URL}/api/v1/libraries/{library_id}/chunks",
    json={
        "text": "Sample text",
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
        "metadata": {"source": "test"}
    }
)

# Search
response = requests.post(
    f"{BASE_URL}/api/v1/libraries/{library_id}/search",
    json={
        "embedding": [0.11, 0.19, 0.31, 0.39, 0.51],
        "k": 5,
        "metric": "cosine"
    }
)
results = response.json()
```

---

**Last Updated**: October 16, 2025
