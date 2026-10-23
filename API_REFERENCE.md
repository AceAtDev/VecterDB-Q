# 🔌 VectorDB-Q API Reference

Complete REST API documentation for VectorDB-Q - Semantic Search Engine.

> **✨ Architecture Note**: The internal backend has been refactored to follow Single Responsibility Principle with separate services for libraries, chunks, and search. The API remains unchanged - all endpoints work exactly as documented below. See [ARCHITECTURE.md](ARCHITECTURE.md) for internal design details.

## 🌐 Base URLs

```
Frontend UI:    http://localhost:8000/
API Base:       http://localhost:8000/api/v1
Interactive:    http://localhost:8000/docs (Swagger UI)
Alternative:    http://localhost:8000/redoc (ReDoc)
Health Check:   http://localhost:8000/health
```

---

## 📋 Quick Navigation

- [System Endpoints](#system-endpoints)
- [Library Endpoints](#library-endpoints)
- [Chunk Endpoints](#chunk-endpoints)
- [Search Endpoint](#search-endpoint)
- [Distance Metrics](#distance-metrics)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Examples](#examples)

---

## 🔧 System Endpoints

### Health Check
```http
GET /health
```

**Description**: Check if the API is running and healthy.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T12:34:56.789Z"
}
```

**Use Case**: Container health checks, monitoring systems.

---

### Root Endpoint
```http
GET /
```

**Description**: Serves the frontend admin dashboard.

**Response** (200 OK): HTML page with responsive UI.

**Features**:
- Library management
- Document upload with embedding generation
- Real-time semantic search
- Sample data loader
- Stats dashboard

---

### API Documentation
```http
GET /docs          # Swagger UI (Interactive)
GET /redoc         # ReDoc (Clean documentation)
GET /openapi.json  # OpenAPI 3.0 specification
```

**Description**: Interactive API documentation with try-it-now functionality.

---

## 📚 Library Endpoints

Libraries are collections that hold related documents/chunks. Each library uses a specific index type (Flat or IVF).

### Create Library
```http
POST /api/v1/libraries
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "My Research Papers",
  "description": "Collection of AI/ML papers",
  "index_type": "flat"
}
```

**Fields**:
- `name` (required): Library name (string)
- `description` (optional): Description (string)
- `index_type` (required): `"flat"` or `"ivf"`
  - **Flat**: Exact search, 100% recall, O(n) time, best for <10K docs
  - **IVF**: Fast approximate, scans ~10% of vectors by default; recall depends on how clustered the data is (1.00 recall@10 on clustered, 0.20 on uniform random in the README benchmark), best for larger collections

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Research Papers",
  "description": "Collection of AI/ML papers",
  "index_type": "flat",
  "created_at": "2025-10-19T12:34:56.789Z",
  "updated_at": "2025-10-19T12:34:56.789Z",
  "documents": [],
  "total_chunks": 0
}
```

**Frontend**: Available in **Libraries** page via "Create New Library" form.

---

### List All Libraries
```http
GET /api/v1/libraries
```

**Description**: Retrieve all libraries with their metadata and statistics.

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "name": "Research Papers",
    "description": "AI/ML papers",
    "index_type": "flat",
    "created_at": "2025-10-19T...",
    "updated_at": "2025-10-19T...",
    "documents": [
      {
        "id": "uuid",
        "name": "Document 1",
        "chunks": [...]
      }
    ],
    "total_chunks": 150
  }
]
```

**Frontend**: Powers the **Libraries** page list and **Search** page dropdown.

---

### Get Library by ID
```http
GET /api/v1/libraries/{library_id}
```

**Parameters**:
- `library_id` (path, required): UUID of the library

**Response** (200 OK): Single library object with full details.

**Response** (404 Not Found):
```json
{
  "detail": "Library not found"
}
```

---

### Update Library
```http
PUT /api/v1/libraries/{library_id}
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "Updated Library Name",
  "description": "Updated description"
}
```

**Note**: `index_type` can be changed (`"flat"` or `"ivf"`). The library's index is recreated and refilled from its stored chunks. `"hnsw"` is not supported and returns 422.

**Response** (200 OK): Updated library object.

---

### Delete Library
```http
DELETE /api/v1/libraries/{library_id}
```

**Description**: Permanently delete a library and all its chunks.

**Response** (204 No Content): Success, no body returned.

**Response** (404 Not Found): Library doesn't exist.

**Warning**: This action cannot be undone. All chunks will be deleted.

---

## 📄 Chunk Endpoints

Chunks are individual pieces of content (text + embedding + metadata) stored in libraries.

### Create Chunk
```http
POST /api/v1/libraries/{library_id}/chunks
Content-Type: application/json
```

**Request Body**:
```json
{
  "text": "Introduction to machine learning and artificial intelligence.",
  "embedding": [0.123, -0.456, 0.789, ...],
  "metadata": {
    "source": "AI_Textbook.pdf",
    "page": 12,
    "chapter": "Introduction",
    "tags": ["machine-learning", "ai", "intro"],
    "custom": {
      "author": "John Doe",
      "year": 2024
    }
  }
}
```

**Fields**:
- `text` (required): The actual text content (string)
- `embedding` (required): Vector representation (array of floats, must match model dimensions)
  - Must have the same dimension as the chunks already in the library. A mismatch returns 400 and nothing is stored.
  - **Cohere embed-english-light-v3.0**: 384 dimensions
  - **All chunks in a library must use the same embedding model**
- `metadata` (optional): Custom metadata (object)
  - Suggested fields: `source`, `page`, `chapter`, `section`, `tags`, `custom`

**Response** (201 Created):
```json
{
  "chunk_id": "abc123...",
  "library_id": "uuid",
  "text": "Introduction to machine learning...",
  "embedding": [0.123, ...],
  "metadata": {...},
  "created_at": "2025-10-19T12:34:56.789Z",
  "updated_at": "2025-10-19T12:34:56.789Z"
}
```

**Frontend**: 
- **Documents** page: Manual form with Cohere API integration
- **Libraries** page: Sample data loader (generates 9 chunks automatically)

**Important**: 
- Embeddings are generated via **Cohere API** in the frontend
- Backend stores and indexes the vectors
- Same embedding model must be used for all chunks in a library

---

### List All Chunks in Library
```http
GET /api/v1/libraries/{library_id}/chunks
```

**Description**: Retrieve all chunks in a library with their metadata.

**Response** (200 OK):
```json
[
  {
    "id": "chunk-uuid",
    "text": "Chunk text content",
    "embedding": [0.1, 0.2, ...],
    "metadata": {...},
    "created_at": "2025-10-19T...",
    "updated_at": "2025-10-19T..."
  }
]
```

---

### Get Chunk by ID
```http
GET /api/v1/libraries/{library_id}/chunks/{chunk_id}
```

**Parameters**:
- `library_id` (path, required): Library UUID
- `chunk_id` (path, required): Chunk UUID

**Response** (200 OK): Single chunk object.

**Response** (404 Not Found): Chunk or library doesn't exist.

---

### Update Chunk
```http
PUT /api/v1/libraries/{library_id}/chunks/{chunk_id}
Content-Type: application/json
```

**Request Body**:
```json
{
  "text": "Updated text content",
  "embedding": [0.234, -0.567, ...],
  "metadata": {
    "source": "Updated source",
    "edited": true
  }
}
```

**Note**: If you update the text, you **must** regenerate the embedding via Cohere API.

**Response** (200 OK): Updated chunk object.

---

### Delete Chunk
```http
DELETE /api/v1/libraries/{library_id}/chunks/{chunk_id}
```

**Description**: Remove a chunk from the library and index.

**Response** (204 No Content): Success.

**Response** (404 Not Found): Chunk or library doesn't exist.

---

## 🔍 Search Endpoint

The **core feature** of VectorDB-Q: semantic similarity search using vector embeddings.

### k-NN Vector Search
```http
POST /api/v1/libraries/{library_id}/search
Content-Type: application/json
```

**Request Body**:
```json
{
  "embedding": [0.234, -0.567, 0.891, ...],
  "k": 10,
  "metric": "cosine",
  "filters": {
    "source": "AI_Textbook.pdf",
    "tags": ["machine-learning"]
  }
}
```

**Parameters**:
- `embedding` (required): Query vector (384 dimensions for Cohere embed-english-light-v3.0)
  - **Must use same model** as indexed chunks
  - Generate with `input_type: "search_query"` in Cohere API
- `k` (optional, default=5): Number of results to return (1-100)
- `metric` (optional, default="euclidean"): Distance calculation method
  - `"euclidean"`: L2 distance (exact magnitude comparison)
  - `"cosine"`: Angular similarity (semantic meaning)
- `filters` (optional): Metadata-based filtering
  - Filters are applied **before** the top `k` is chosen, so up to `k` matching chunks are returned
  - Any metadata field can be used as filter

---

**Response** (200 OK):
```json
[
  {
    "chunk": {
      "id": "uuid",
      "text": "Machine learning is a subset of artificial intelligence...",
      "embedding": [0.123, -0.456, ...],
      "metadata": {
        "source": "AI_Textbook.pdf",
        "page": 12,
        "chapter": "Introduction",
        "tags": ["machine-learning", "ai"]
      },
      "created_at": "2025-10-19T12:34:56.789Z",
      "updated_at": "2025-10-19T12:34:56.789Z"
    },
    "score": 0.95,
    "distance": 0.05
  }
]
```

**Response Fields**:
- `chunk`: Full chunk object with metadata
- `score`: Similarity score (0-1, higher = better match)
  - **Cosine**: Converted to 0-1 range (1.0 = identical)
  - **Euclidean**: Normalized with `1 / (1 + distance)`
- `distance`: Raw distance value
  - **Cosine**: 0.0 (identical) to 2.0 (opposite)
  - **Euclidean**: 0.0 (identical) to ∞ (very different)

---

### Embed Text

**POST** `/api/v1/embed`

Turns text into vectors with the server's embedding provider, so clients do not need an API key. The provider is Cohere `embed-english-light-v3.0` when `COHERE_API_KEY` is set, otherwise the local `all-MiniLM-L6-v2` (set `EMBEDDING_PROVIDER` to `cohere` or `local` to force one). Both return 384 dimensions.

```json
{"texts": ["how did she escape?"], "input_type": "search_query"}
```

`texts`: 1 to 96 strings. `input_type`: `search_document` (default) or `search_query`; only Cohere uses it.

**Response 200:** `{"embeddings": [[...384 floats...]], "provider": "local", "model": "sentence-transformers/all-MiniLM-L6-v2", "dimension": 384}`

**Response 503:** no provider is available (for example `local` without `sentence-transformers` installed).

### Frontend Integration

**Search Page** workflow:
1. User types query: *"What is machine learning?"*
2. Frontend calls **Cohere API** to embed query → `[0.234, -0.567, ...]`
3. Frontend sends POST to `/api/v1/libraries/{id}/search`
4. Backend runs vector similarity search (Flat or IVF index)
5. Frontend displays results with metadata

**Performance**:
- **Flat Index**: Exact search, O(n), ~206 ms for 100K random vectors (measured)
- **IVF Index**: Approximate search, scans ~10% of vectors by default, ~30 ms for 100K random vectors (measured). Speed and recall depend on the data; see the README benchmark section.

**Filtering Example**:
```javascript
// Search with metadata filter
const results = await fetch('/api/v1/libraries/uuid/search', {
  method: 'POST',
  body: JSON.stringify({
    embedding: queryVector,
    k: 10,
    metric: "cosine",
    filters: {
      source: "AI_Textbook.pdf",
      chapter: "Introduction"
    }
  })
});
```

---

## 📊 Distance Metrics

### Euclidean Distance (L2 Norm)
**Formula**: 

$$
d(p, q) = \sqrt{\sum_{i=1}^{n} (q_i - p_i)^2}
$$

**Characteristics**:
- Measures **absolute distance** in vector space
- Sensitive to magnitude differences
- Good for: comparing vectors with meaningful scale (e.g., normalized embeddings)

**Score Calculation**: 
$$
\text{score} = \frac{1}{1 + \text{distance}}
$$

**Use Cases**:
- Image embeddings (pixel distance)
- Normalized text embeddings
- When magnitude matters

**Example**:
- `p = [1, 2, 3]`, `q = [4, 5, 6]`
- Distance = `√((4-1)² + (5-2)² + (6-3)²)` = `√27` = `5.196`
- Score = `1 / (1 + 5.196)` = `0.161`

---

### Cosine Similarity
**Formula**:

$$
\text{similarity} = \frac{p \cdot q}{||p|| \times ||q||}
$$

$$
\text{distance} = 1 - \text{similarity}
$$

**Characteristics**:
- Measures **angular similarity** (direction, not magnitude)
- Range: -1 (opposite) to +1 (identical)
- Magnitude-independent (good for variable-length texts)

**Score Calculation**: 
$$
\text{score} = 1 - \text{distance}
$$

**Use Cases**:
- **Text embeddings** (most common for semantic search)
- Document similarity
- When direction matters more than magnitude

**Example**:
- `p = [1, 2, 3]`, `q = [2, 4, 6]` (same direction, different magnitude)
- Similarity = `(1×2 + 2×4 + 3×6) / (√14 × √56)` = `1.0`
- Distance = `1 - 1.0` = `0.0` (perfect match!)
- Score = `1 - 0.0` = `1.0`

---

### Which Metric to Use?

| Metric | Best For | Pros | Cons |
|--------|----------|------|------|
| **Cosine** | Text/semantic search | Magnitude-independent, semantic meaning | Ignores length differences |
| **Euclidean** | Image/audio embeddings | Considers magnitude, intuitive | Sensitive to scale |

**Recommendation**: Use **cosine** for text embeddings (Cohere, OpenAI, etc.)

---

## 🔧 cURL Examples

### 1. Create Library
```bash
curl -X POST http://localhost:8000/api/v1/libraries \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Research Library",
    "description": "Collection of AI research papers and articles",
    "index_type": "ivf",
    "dimension": 384,
    "distance_metric": "cosine"
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AI Research Library",
  "index_type": "ivf",
  "chunk_count": 0
}
```

---

### 2. Add Chunk with Embedding
```bash
# Note: Generate embedding via Cohere API first (see frontend or Python examples)
curl -X POST http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
    "embedding": [0.234, -0.567, 0.891, ..., 0.123],
    "metadata": {
      "source": "AI_Basics.pdf",
      "page": 12,
      "chapter": "Introduction",
      "author": "John Doe",
      "tags": ["machine-learning", "ai", "fundamentals"]
    }
  }'
```

**Response**:
```json
{
  "chunk_id": "abc123...",
  "library_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-19T12:34:56.789Z"
}
```

---

### 3. Semantic Search (Cosine)
```bash
curl -X POST http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.123, -0.456, 0.789, ..., 0.234],
    "k": 10,
    "metric": "cosine",
    "filters": {
      "tags": ["machine-learning"]
    }
  }'
```

**Response**:
```json
[
  {
    "chunk": {
      "id": "abc123...",
      "text": "Machine learning is a subset...",
      "metadata": {...}
    },
    "score": 0.95,
    "distance": 0.05
  }
]
```

---

### 4. Search with Euclidean Distance
```bash
curl -X POST http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000/search \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.1, 0.2, 0.3, ..., 0.384],
    "k": 5,
    "metric": "euclidean"
  }'
```

---

### 5. List All Libraries
```bash
curl -X GET http://localhost:8000/api/v1/libraries
```

---

### 6. Get Library Details
```bash
curl -X GET http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000
```

---

### 7. Delete Chunk
```bash
curl -X DELETE http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000/chunks/abc123...
```

---

### 8. Delete Library
```bash
curl -X DELETE http://localhost:8000/api/v1/libraries/550e8400-e29b-41d4-a716-446655440000
```

---

## 🔐 Authentication

**Current Version**: No authentication required (development mode)

**Production Recommendation**:
- API Key authentication (header: `X-API-Key`)
- JWT tokens for user-based access  
- Rate limiting per API key

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| **200 OK** | Success | GET, PUT requests |
| **201 Created** | Resource created | POST requests (library, chunk) |
| **204 No Content** | Success, no body | DELETE requests |
| **400 Bad Request** | Validation error | Invalid request body, missing fields |
| **404 Not Found** | Resource doesn't exist | Invalid library_id or chunk_id |
| **422 Unprocessable Entity** | Semantic error | Dimension mismatch, invalid index type |
| **500 Internal Server Error** | Server error | Unexpected backend error |

### Error Response Format

```json
{
  "detail": "Error message describing the problem"
}
```

**Examples**:

**404 Not Found**:
```json
{
  "detail": "Library not found"
}
```

**422 Dimension Mismatch**:
```json
{
  "detail": "Embedding dimension (512) does not match library dimension (384)"
}
```

---

## 🚦 Rate Limits

**Current Version**: No rate limits (development mode)

**Production Recommendation**:
- **100 requests/minute** per IP (general endpoints)
- **10 searches/minute** per IP (search endpoint)
- **1000 chunks/hour** per library (ingestion limit)

---

## 🎯 Metadata Filtering

Filters are applied **after** vector search to refine results.

### Supported Filter Types

**1. Exact Match**:
```json
{"source": "AI_Textbook.pdf"}
```

**2. Substring Match** (case-insensitive):
```json
{"source": "textbook"}
```

**3. List Membership**:
```json
{"category": ["research", "education"]}
```

**4. Nested Fields**:
```json
{"custom.author": "John Doe"}
```

**5. Multiple Filters** (AND logic):
```json
{
  "embedding": [...],
  "k": 10,
  "filters": {
    "source": "Research",
    "tags": ["machine-learning"],
    "page": 12
  }
}
```

---

## 💻 Python Client Example

```python
import os
import requests
import cohere

BASE_URL = "http://localhost:8000/api/v1"
COHERE_KEY = os.environ["COHERE_API_KEY"]  # supply your own Cohere API key

# Initialize Cohere
co = cohere.Client(COHERE_KEY)

# 1. Create library
response = requests.post(
    f"{BASE_URL}/libraries",
    json={
        "name": "AI Research",
        "description": "AI papers collection",
        "index_type": "ivf",
        "dimension": 384,
        "distance_metric": "cosine"
    }
)
library_id = response.json()["id"]
print(f"Created library: {library_id}")

# 2. Add chunk with Cohere embedding
text = "Machine learning is a subset of artificial intelligence."
embedding_response = co.embed(
    texts=[text],
    model="embed-english-light-v3.0",
    input_type="search_document"
)
embedding = embedding_response.embeddings[0]

response = requests.post(
    f"{BASE_URL}/libraries/{library_id}/chunks",
    json={
        "text": text,
        "embedding": embedding,
        "metadata": {
            "source": "AI_Basics.pdf",
            "page": 12,
            "chapter": "Introduction"
        }
    }
)
chunk_id = response.json()["chunk_id"]
print(f"Added chunk: {chunk_id}")

# 3. Semantic search
query = "What is deep learning?"
query_response = co.embed(
    texts=[query],
    model="embed-english-light-v3.0",
    input_type="search_query"
)
query_embedding = query_response.embeddings[0]

response = requests.post(
    f"{BASE_URL}/libraries/{library_id}/search",
    json={
        "embedding": query_embedding,
        "k": 5,
        "metric": "cosine"
    }
)
results = response.json()

print(f"\nSearch results for: '{query}'")
for result in results:
    print(f"  - {result['chunk']['text'][:50]}...")
    print(f"    Score: {result['score']:.3f}")
```

---

## 🌐 JavaScript/Frontend Example

```javascript
const COHERE_API_KEY = "YOUR_COHERE_API_KEY"; // supply your own Cohere API key (never commit real keys)
const API_BASE = "http://localhost:8000/api/v1";

// Generate embedding via Cohere
async function getEmbedding(text, inputType = "search_document") {
    const response = await fetch("https://api.cohere.ai/v1/embed", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${COHERE_API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            texts: [text],
            model: "embed-english-light-v3.0",
            input_type: inputType
        })
    });
    const data = await response.json();
    return data.embeddings[0];
}

// Create library
async function createLibrary() {
    const response = await fetch(`${API_BASE}/libraries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: "Tech Articles",
            description: "Collection of tech articles",
            index_type: "ivf",
            dimension: 384,
            distance_metric: "cosine"
        })
    });
    return await response.json();
}

// Add chunk
async function addChunk(libraryId, text, metadata) {
    const embedding = await getEmbedding(text, "search_document");
    
    const response = await fetch(`${API_BASE}/libraries/${libraryId}/chunks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, embedding, metadata })
    });
    return await response.json();
}

// Search
async function search(libraryId, query) {
    const embedding = await getEmbedding(query, "search_query");
    
    const response = await fetch(`${API_BASE}/libraries/${libraryId}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            embedding,
            k: 5,
            metric: "cosine"
        })
    });
    return await response.json();
}

// Example usage
(async () => {
    const library = await createLibrary();
    console.log("Created library:", library.id);
    
    await addChunk(
        library.id,
        "React is a JavaScript library for building UIs.",
        { source: "React_Docs.md", category: "frontend" }
    );
    
    const results = await search(library.id, "How to build UI components?");
    console.log("Search results:", results);
})();
```

---

**Last Updated**: October 19, 2025
