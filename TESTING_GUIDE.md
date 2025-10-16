# 🧪 Testing Guide - How to Test the API

## 🐳 Step 1: Start the Docker Container

```bash
# In WSL or PowerShell
docker-compose up

# Or run in background
docker-compose up -d

# Check if it's running
docker ps
```

You should see output like:
```
CONTAINER ID   IMAGE          STATUS         PORTS
abc123def456   vectordb-q     Up 2 minutes   0.0.0.0:8000->8000/tcp
```

---

## 🧪 Step 2: Choose Your Testing Method

### Method 1: 🌐 Swagger UI (Easiest - Interactive)

1. **Open your browser**
2. **Navigate to**: `http://localhost:8000/docs`
3. **You'll see an interactive API documentation**
4. **Click "Try it out"** on any endpoint
5. **Fill in the parameters**
6. **Click "Execute"**
7. **See the response**

**Example - Create a Library:**
1. Go to `http://localhost:8000/docs`
2. Find `POST /api/v1/libraries`
3. Click "Try it out"
4. Paste this JSON:
```json
{
  "name": "Test Library",
  "description": "My first library",
  "index_type": "flat"
}
```
5. Click "Execute"
6. Copy the `id` from the response

---

### Method 2: 🖥️ PowerShell with curl (Windows)

```powershell
# 1. Health Check
curl http://localhost:8000/health

# 2. Create Library
$response = curl -Method POST -Uri "http://localhost:8000/api/v1/libraries" `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Test Library","index_type":"flat"}' | ConvertFrom-Json

$libraryId = $response.id
Write-Host "Library ID: $libraryId"

# 3. Add a Chunk
$chunkBody = @{
  text = "This is a test chunk about machine learning"
  embedding = @(0.1, 0.2, 0.3, 0.4, 0.5)
  metadata = @{
    source = "test"
    page = 1
    tags = @("test", "ml")
  }
} | ConvertTo-Json -Depth 10

curl -Method POST -Uri "http://localhost:8000/api/v1/libraries/$libraryId/chunks" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $chunkBody

# 4. Search
$searchBody = @{
  embedding = @(0.11, 0.19, 0.31, 0.39, 0.51)
  k = 5
  metric = "cosine"
} | ConvertTo-Json -Depth 10

curl -Method POST -Uri "http://localhost:8000/api/v1/libraries/$libraryId/search" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $searchBody

# 5. List all libraries
curl http://localhost:8000/api/v1/libraries

# 6. Delete library
curl -Method DELETE -Uri "http://localhost:8000/api/v1/libraries/$libraryId"
```

---

### Method 3: 🐧 WSL/Linux bash with curl

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Create Library
library_response=$(curl -X POST http://localhost:8000/api/v1/libraries \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Library",
    "description": "Testing the API",
    "index_type": "flat"
  }')

# Extract library ID (requires jq)
library_id=$(echo $library_response | jq -r '.id')
echo "Library ID: $library_id"

# 3. Add a Chunk
curl -X POST "http://localhost:8000/api/v1/libraries/$library_id/chunks" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Deep learning is a subset of machine learning",
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "metadata": {
      "source": "AI Textbook",
      "page": 42,
      "tags": ["deep-learning", "ml"]
    }
  }'

# 4. List chunks
curl "http://localhost:8000/api/v1/libraries/$library_id/chunks"

# 5. Search with Euclidean distance
curl -X POST "http://localhost:8000/api/v1/libraries/$library_id/search" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.11, 0.19, 0.31, 0.39, 0.51],
    "k": 5,
    "metric": "euclidean"
  }'

# 6. Search with Cosine similarity
curl -X POST "http://localhost:8000/api/v1/libraries/$library_id/search" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.11, 0.19, 0.31, 0.39, 0.51],
    "k": 5,
    "metric": "cosine"
  }'

# 7. Delete library
curl -X DELETE "http://localhost:8000/api/v1/libraries/$library_id"
```

---

### Method 4: 🐍 Python Script (Recommended)

**Create a file `test_api.py`:**

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing VectorDB-Q API\n")
    
    # 1. Health Check
    print("1. Health Check...")
    r = requests.get(f"{BASE_URL}/health")
    print(f"   ✅ Status: {r.json()}\n")
    
    # 2. Create Library
    print("2. Creating library...")
    r = requests.post(f"{BASE_URL}/api/v1/libraries", json={
        "name": "Test Library",
        "description": "Testing the API",
        "index_type": "flat"
    })
    library = r.json()
    library_id = library["id"]
    print(f"   ✅ Created library: {library_id}\n")
    
    # 3. Add Chunks
    print("3. Adding chunks...")
    chunks = [
        {
            "text": "Deep learning uses neural networks",
            "embedding": [0.8, 0.6, 0.3, 0.1, 0.2],
            "metadata": {"source": "AI Book", "page": 1, "tags": ["dl"]}
        },
        {
            "text": "Natural language processing handles text",
            "embedding": [0.2, 0.9, 0.7, 0.3, 0.1],
            "metadata": {"source": "NLP Guide", "page": 2, "tags": ["nlp"]}
        },
        {
            "text": "Computer vision analyzes images",
            "embedding": [0.1, 0.3, 0.2, 0.8, 0.9],
            "metadata": {"source": "CV Handbook", "page": 3, "tags": ["cv"]}
        }
    ]
    
    for i, chunk_data in enumerate(chunks, 1):
        r = requests.post(
            f"{BASE_URL}/api/v1/libraries/{library_id}/chunks",
            json=chunk_data
        )
        print(f"   ✅ Added chunk {i}")
    print()
    
    # 4. List Chunks
    print("4. Listing all chunks...")
    r = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}/chunks")
    chunks_list = r.json()
    print(f"   ✅ Found {len(chunks_list)} chunks\n")
    
    # 5. Search with Euclidean
    print("5. Searching with Euclidean distance...")
    r = requests.post(f"{BASE_URL}/api/v1/libraries/{library_id}/search", json={
        "embedding": [0.82, 0.58, 0.32, 0.12, 0.22],  # Similar to first chunk
        "k": 3,
        "metric": "euclidean"
    })
    results = r.json()
    print(f"   ✅ Found {len(results)} results")
    for i, res in enumerate(results, 1):
        print(f"      {i}. Score: {res['score']:.4f} - {res['chunk']['text'][:50]}...")
    print()
    
    # 6. Search with Cosine
    print("6. Searching with Cosine similarity...")
    r = requests.post(f"{BASE_URL}/api/v1/libraries/{library_id}/search", json={
        "embedding": [0.25, 0.85, 0.68, 0.28, 0.15],  # Similar to second chunk
        "k": 3,
        "metric": "cosine"
    })
    results = r.json()
    print(f"   ✅ Found {len(results)} results")
    for i, res in enumerate(results, 1):
        print(f"      {i}. Score: {res['score']:.4f} - {res['chunk']['text'][:50]}...")
    print()
    
    # 7. Search with Filters
    print("7. Searching with metadata filter...")
    r = requests.post(f"{BASE_URL}/api/v1/libraries/{library_id}/search", json={
        "embedding": [0.5, 0.5, 0.5, 0.5, 0.5],
        "k": 5,
        "metric": "euclidean",
        "filters": {"source": "AI Book"}
    })
    results = r.json()
    print(f"   ✅ Found {len(results)} results matching 'AI Book'\n")
    
    # 8. Update Library
    print("8. Updating library...")
    r = requests.put(f"{BASE_URL}/api/v1/libraries/{library_id}", json={
        "description": "Updated description!"
    })
    print(f"   ✅ Library updated\n")
    
    # 9. Delete Library
    print("9. Deleting library...")
    r = requests.delete(f"{BASE_URL}/api/v1/libraries/{library_id}")
    print(f"   ✅ Library deleted (Status: {r.status_code})\n")
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_api()
```

**Run it:**
```bash
python test_api.py
```

---

### Method 5: 📮 Postman (GUI Tool)

1. **Download Postman**: https://www.postman.com/downloads/
2. **Import OpenAPI spec**: 
   - Go to `http://localhost:8000/openapi.json`
   - Copy the JSON
   - In Postman: Import → Raw Text → Paste → Import
3. **Use the generated collection** to test all endpoints

---

## 🎯 Quick Test Workflow

### Minimal Test (30 seconds):

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Check docs are working
# Open: http://localhost:8000/docs

# 3. Create and test library
curl -X POST http://localhost:8000/api/v1/libraries \
  -H "Content-Type: application/json" \
  -d '{"name":"Quick Test","index_type":"flat"}'
```

### Full Test (2 minutes):

Run the comprehensive demo:
```bash
python demo_mvp.py
```

This tests all 14 scenarios automatically!

---

## 📊 What to Look For

### ✅ Success Indicators:

1. **Health endpoint returns**: `{"status":"healthy"}`
2. **Create returns 201**: With a UUID `id` field
3. **GET returns 200**: With data
4. **Search returns results**: With `score` and `distance`
5. **Delete returns 204**: No content

### ❌ If Something Goes Wrong:

```bash
# Check container logs
docker-compose logs -f

# Check if container is running
docker ps

# Restart container
docker-compose restart

# Rebuild if needed
docker-compose down
docker-compose up --build
```

---

## 🔍 Debugging Tips

### Check Container Status:
```bash
docker ps
docker logs vectordb-q-api
```

### Test from Inside Container:
```bash
docker exec -it vectordb-q-api bash
curl http://localhost:8000/health
```

### Check Port Mapping:
```bash
# Should show 0.0.0.0:8000->8000/tcp
docker port vectordb-q-api
```

---

## 📝 Example Full Test Session

```bash
# Start
docker-compose up -d

# Wait a moment for startup
sleep 3

# Test
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"vectordb-q"}

# Open browser
start http://localhost:8000/docs  # Windows
open http://localhost:8000/docs   # Mac
xdg-open http://localhost:8000/docs  # Linux

# Run full demo
python demo_mvp.py

# Stop
docker-compose down
```

---

## 🎉 Ready to Test!

**Easiest method**: Open `http://localhost:8000/docs` in your browser and use the interactive UI!

**Most comprehensive**: Run `python demo_mvp.py`

**Quick verification**: `curl http://localhost:8000/health`

---

**Last Updated**: October 16, 2025
