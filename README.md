# VectorDB-Q: Semantic Search Engine

A semantic search engine with Flat and IVF vector indexes written from scratch, a REST API, and a web interface. Built with Python, FastAPI, and vanilla JavaScript. It is a learning project and a working prototype, not a production database: see [Known Limitations](#-known-limitations).

## ✨ What Makes This Special?

🎯 **Semantic Search** - Find documents by meaning, not just keywords  
🚀 **Fast** - on 20K real sentence embeddings, IVF search takes 7.2 ms vs 56.9 ms for exact search (~8x), at 0.94 recall@10 (measured, see [Performance](#-performance-at-scale))  
🎨 **Beautiful UI** - Responsive admin dashboard with real-time search  
🐳 **Docker Ready** - One-command deployment  
⚡ **Smart Indexing** - Choose between exact (Flat) or fast approximate (IVF) search  
🧠 **AI-Powered** - Cohere embeddings for understanding context

---

## 🎥 Video Walkthroughs

### 🚀 Quick Setup Guide
Watch a complete setup walkthrough from clone to running application:

[![Project Setup](https://img.shields.io/badge/▶️_Watch-Project_Setup-blue?style=for-the-badge&logo=loom)](https://www.loom.com/share/9b112343b0104392b47bd8c1c85b1826?sid=1fca3353-af7a-4d6c-85ff-0ee63d5310f5)

**Covers**: Git clone → Docker setup → First search in under 2 minutes

### 🧠 Technical Dive (please read the note below about architecture)
Architecture, design decisions, and problem-solving walkthrough:

[![Technical Walkthrough](https://img.shields.io/badge/▶️_Watch-Technical_Deep_Dive-red?style=for-the-badge&logo=loom)](https://www.loom.com/share/0094d5bb49234ab0935eb84752424844)

**Covers**: Architecture patterns → Indexing algorithms → Design choices

> **Architecture Note**: The internal backend has been refactored to follow Single Responsibility Principle with separate services for libraries, chunks, and search. The API remains unchanged.


---

## 🚀 Quick Start (3 Steps)

### 1. Clone & Configure
```powershell
git clone github.com/AceAtDev/VecterDB-Q.git
cd VecterDB-Q
cp .env.example .env
# Edit .env and add your Cohere API key
```

### 2. Deploy with Docker
```powershell
docker-compose up -d
```

### 3. Open & Explore
- **Web UI**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

**🎬 First time?** Try the built-in sample data loader in the Libraries page!

---

---

## 🎯 What is VectorDB-Q?

VectorDB-Q is a **semantic search engine** that understands meaning, not just keywords. 

### Traditional Search vs VectorDB-Q

| Traditional Keyword Search | VectorDB-Q Semantic Search |
|---------------------------|---------------------------|
| "machine learning" only finds those exact words | Finds "AI", "neural networks", "deep learning" |
| Slow with large datasets (5+ seconds) | ~4 ms at 10K vectors, ~30 ms at 100K (IVF) |
| SQL LIKE queries scan everything | Smart indexing searches clusters |
| Misses context and synonyms | Understands meaning and context |

### Perfect For:
- � **Document Search** - Find relevant documents by meaning
- 🎯 **Recommendation Systems** - "Similar to this" functionality  
- 🔍 **Research Tools** - Semantic search across papers/articles
- 💬 **Customer Support** - Find similar support tickets
- 🎓 **Knowledge Bases** - Intelligent content discovery

---

## ✨ Features

**Frontend**: Responsive dashboard, real-time search, library management, sample data loader  
**Backend**: FastAPI with async support, Flat (exact) and IVF (fast) indexing, cosine/euclidean metrics  
**AI**: Cohere embeddings (384D), semantic understanding, context-aware search

---

## 🏗️ Architecture

**Clean Domain-Driven Design** with proper service separation following SOLID principles:

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  • Vanilla JavaScript SPA                                    │
│  • Responsive design (mobile/tablet/desktop)                 │
│  • Real-time search interface                                │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼──────────────────────────────────────┐
│                    API Routes Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Libraries   │  │   Chunks     │  │   Search     │        │
│  │   Routes     │  │   Routes     │  │   Routes     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Library     │  │   Chunk      │  │   Search     │        │ 
│  │  Service     │  │   Service    │  │   Service    │        │ 
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ 
│  │  Library     │  │   Chunk      │  │   Index      │        │
│  │  Repository  │  │   Repository │  │   Repository │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         Index Management Layer                          │ │
│  │  ┌──────────────┐    ┌──────────────┐                   │ │
│  │  │ Flat Index   │    │  IVF Index   │                   │ │
│  │  │ (Exact)      │    │ (Fast Approx)│                   │ │
│  │  │ O(n) time    │    │ ~10% scanned │                   │ │
│  │  └──────────────┘    └──────────────┘                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                     Data Layer                               │
│  ┌─────────────────┐        ┌──────────────────────┐         │
│  │ Vector Storage  │        │   Cohere API         │         │
│  │ • In-Memory     │        │   (External)         │         │
│  │ • Pickle Persist│        │   Text → 384D Vector │         │
│  │ • NumPy Arrays  │        └──────────────────────┘         │
│  └─────────────────┘                                         │
└──────────────────────────────────────────────────────────────┘
```

**Why This Design?**
- **Single Responsibility**: Each service handles one domain (libraries, chunks, or search)
- **Separation of Concerns**: Clear boundaries between routes, services, and repositories
- **Testability**: Services can be tested independently with mocked dependencies
- **Maintainability**: Easy to find and update specific functionality
- **SOLID Principles**: Follows industry best practices for enterprise applications

> 📚 **See [ARCHITECTURE.md](ARCHITECTURE.md)** for detailed service design and dependency injection patterns

---

## 📚 Documentation

### 📖 API Documentation

- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete REST API documentation with cURL, Python, and JavaScript examples
- **Interactive Docs** - http://localhost:8000/docs (Auto-generated Swagger UI)



## 🎬 Quick Demo (Built-In Sample Data)

**Try the interactive story feature:**

1. Open **http://localhost:8000/**
2. Navigate to **Libraries** page
3. Click **"🧪 Load Sample Story Data"**
4. Wait ~20-30 seconds (loads 9 story chapters with embeddings)
5. Go to **Search** page, select the sample library
6. Try these queries:
   - `"vector database technology"`
   - `"what happened during the consolidation?"`
   - `"Sarah's escape from the facility"`

**Story**: "The Last Engineer" - A sci-fi tale about vector databases!

---

## 📊 Performance at Scale

### Measured Benchmarks

All numbers below were measured in October 2026 on an AMD Ryzen 7 8845HS (16 threads), Python 3.12, single process. Absolute times vary between runs on the same laptop (power state), so compare numbers within one table rather than across tables.

#### Real embeddings

AG News passages embedded with `all-MiniLM-L6-v2` (384-d, normalized), 50 held-out test passages as queries, cosine metric, top-10, default IVF settings (100 clusters, `n_probe=10`). Recall is measured against exact (Flat) results.

```bash
pip install datasets sentence-transformers   # only needed for this benchmark
python benchmarks/embed_agnews.py --n 20000 --out /tmp/agnews_minilm.npz
python benchmarks/bench_real_embeddings.py --data /tmp/agnews_minilm.npz --sizes 5000 10000 20000
```

| Vectors | Flat (exact) | IVF (approximate) | Speedup | IVF build (bulk) | IVF recall@10 (bulk) | IVF recall@10 (one insert at a time) |
|---------|--------------|-------------------|---------|------------------|----------------------|--------------------------------------|
| 5,000 | 13.7 ms | 1.9 ms | ~7x | 15 s | 0.91 | 0.91 |
| 10,000 | 28.5 ms | 3.9 ms | ~7x | 31 s | 0.92 | 0.91 |
| 20,000 | 56.9 ms | 7.2 ms | ~8x | 60 s | 0.94 | 0.94 |

"Bulk" is one `add()` call with every vector, which is what happens when the server starts and rebuilds indexes from stored chunks. "One insert at a time" is how a library filled through `POST /chunks` is built: IVF trains k-means once it has 100 vectors and retrains each time the index doubles (100, 200, 400, ... 12,800 vectors for 20K), so it reaches the same recall as a bulk build. Building 20K vectors that way took 78 s in total, and the insert that triggers a retrain waits for k-means (see [Known Limitations](#-known-limitations)).

k-means initialization is seeded, so the same vectors in the same order always give the same index. An earlier run of this table, before IVF retrained and before the seed was added, measured 71.0 ms (Flat) vs 8.1 ms (IVF) at 0.92 recall@10 for 20K vectors, and 0.70-0.75 recall@10 for an index built one insert at a time. Running that older code again next to the current code gave 56.4 ms vs 7.4 ms at 0.93 recall@10, so the fixes did not change search speed; the recall moved from 0.92-0.93 to 0.94 because the seeded initialization picks a different starting sample.

For scale: a vectorized NumPy brute-force search over the same 20K vectors takes about 1-2 ms. Both indexes here search with plain Python loops, which is where most of their time goes.

#### Synthetic vectors

Reproduce with `python benchmarks/bench_indexes.py --n 100000 --data random` (or `--data clustered`). Synthetic 384-dimension vectors, Euclidean metric, top-10 search, median of 20 queries, default IVF settings.

| Data | Vectors | Flat (exact) | IVF (approximate) | Speedup | IVF build | IVF recall@10 |
|------|---------|--------------|-------------------|---------|-----------|---------------|
| Uniform random | 10,000 | 17 ms | 4 ms | ~4.4x | 34 s | not measured |
| Uniform random | 100,000 | 206 ms | 30 ms | ~6.9x | 380 s | 0.20 |
| Clustered | 10,000 | 19 ms | 9 ms | ~2x | 12 s | 1.00 |

Speed and recall trade off with the data: on uniform random vectors (worst case for IVF) every cluster is similar in size, so IVF is fast but misses most true neighbours. On clustered vectors, closer to real embeddings, IVF finds every true neighbour but probes larger clusters.

**Not measured at 1M.** k-means training and IVF search are currently pure-Python loops, so build time grows linearly (~1 hour projected at 1M) and IVF search would scan ~100K vectors per query. Vectorizing both with NumPy is the next step before claiming million-scale numbers.

#### Concurrent requests

Real uvicorn server (1 worker, as in the Dockerfile), persistence off, 1,000 search requests per level sent with `aiohttp`. Reproduce with `python benchmarks/bench_http_concurrency.py --data /tmp/agnews_minilm.npz --n 10000 --index ivf --levels 1 1000 --requests 1000`.

| Library | Requests in flight | Throughput | p50 latency | Errors |
|---------|--------------------|------------|-------------|--------|
| IVF, 10K vectors | 1 | 109.6 req/s | 9 ms | 0 |
| IVF, 10K vectors | 1,000 | 55.2 req/s | 17.6 s | 0 |
| Flat, 10K vectors (before the fixes) | 1 | 16.7 req/s | 60 ms | 0 |
| Flat, 10K vectors (before the fixes) | 1,000 | 7.6 req/s | 130 s | 0 |

The IVF rows were re-measured after removing the per-query debug output (which printed, and built a list of every chunk id, on each search); before that, the same runs gave 34.5 req/s at 1 request in flight and 24.3 req/s at 1,000. The Flat rows have not been re-run.

The reader-writer locks hold up: 1,000 simultaneous requests return no errors, and a 30-second mixed run (100 search clients plus 8 create/update/delete clients, `--mixed`) ended with the index and chunk store in agreement. But search does not run in parallel. Python's GIL serializes the pure-Python search loops, so extra concurrency only adds queueing, and running more uvicorn workers would give each worker its own separate in-memory database.

### Algorithm Comparison

| Feature | Flat Index | IVF Index |
|---------|------------|-----------|
| **Build Time** | Instant | O(n·k·i), 380 s measured for 100K |
| **Search Time** | O(n·d) | O(k·d + (n_probe/k)·n·d): scans ~10% of vectors by default |
| **Memory** | O(n·d) | O(n·d + k·d) |
| **Accuracy** | 100% (exact) | 0.94 recall@10 on 20K real embeddings (bulk or one insert at a time); 1.00 clustered, 0.20 uniform random |
| **Best For** | Small collections, exact results | Larger, clustered collections |

**Where:**
- `n` = number of vectors
- `d` = dimensions (384)
- `k` = number of clusters (100)
- `i` = k-means iterations (10)

---

## 🔧 Tech Stack

**Frontend**: Vanilla JavaScript, Responsive CSS  
**Backend**: Python 3.11, FastAPI, NumPy 2.0+, Uvicorn  
**AI**: Cohere API (embed-english-light-v3.0, 384D)  
**Infrastructure**: Docker, Docker Compose

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)
```powershell
# Quick start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Docker (Manual)
```powershell
# Build
docker build -t vectordb-q .

# Run
docker run -p 8000:8000 -v ./data:/app/data vectordb-q
```

### Option 3: Local Development
```powershell
# Setup environment
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your Cohere API key

# Run
uvicorn app.main:app --reload
```

### Option 4: Quick Deploy Script
```powershell
# Windows
.\deploy.ps1

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

---

## � API Quick Reference

### Create Library
```powershell
curl -X POST "http://localhost:8000/api/v1/libraries" `
  -H "Content-Type: application/json" `
  -d '{"name": "My Library", "index_type": "flat"}'
```

### Add Chunk
```powershell
curl -X POST "http://localhost:8000/api/v1/libraries/{library_id}/chunks" `
  -H "Content-Type: application/json" `
  -d '{
    "text": "Sample text",
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "metadata": {"source": "test"}
  }'
```

### Search
```powershell
curl -X POST "http://localhost:8000/api/v1/libraries/{library_id}/search" `
  -H "Content-Type: application/json" `
  -d '{
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    "k": 5,
    "metric": "cosine"
  }'
```

**📖 Full API reference:** [API_REFERENCE.md](API_REFERENCE.md)  
**🌐 Interactive docs:** http://localhost:8000/docs

---

## 🏆 Technical Highlights

- **Hand-written indexes**: Flat (exact) and IVF with seeded k-means that retrains as the index grows, ~7-8x faster than exact search on real embeddings at 0.91-0.94 recall@10
- **Thread-safe**: reader-writer locks; load-tested with 1,000 simultaneous requests and 0 errors
- **Real AI**: Cohere embeddings
- **Clean Architecture**: 4-layer DDD design
- **Beautiful UX**: Responsive with sample data

---

## ⚠️ Known Limitations

Found by stress-testing the code in October 2026.

**Fixed since then** (with tests in `tests/`):
- IVF retrains k-means each time the index doubles, so a library filled through `POST /chunks` reaches the same recall as a bulk build (0.94 at 20K). k-means is seeded.
- Snapshots are fsynced (temp file, then rename, then directory) instead of only renamed.
- `libraries.pkl` no longer stores a second copy of every chunk, and deleting a library deletes its chunks.
- A chunk with the wrong embedding dimension is rejected with 400 before anything is stored. Wrong-dimension queries and updates also return 400.
- Metadata filters are applied before the top-k is chosen, so a filtered search returns up to k matching chunks.
- `index_type: "hnsw"` is rejected (422) instead of silently creating a Flat index. Changing a library's `index_type` refills the new index from stored chunks.
- Debug output on the search path is gone (see [Concurrent requests](#concurrent-requests)).

**Still open:**
- **Single process, GIL-bound.** Searches are served one after another (see [Concurrent requests](#concurrent-requests)).
- **IVF retraining blocks.** Retraining runs while the index write lock is held, so the insert that triggers it, and every search on that library, waits for k-means. At 20K vectors the largest retrain (on 12,800 vectors) takes roughly 40 s.
- **IVF results can shift after the first restart.** On startup an index is rebuilt in one pass and trained on all its vectors, while an index built one insert at a time was last trained on a prefix. Recall is the same, but individual results can differ from before the restart. Later restarts rebuild the same index.
- **Persistence rewrites everything.** Every write pickles and fsyncs the whole chunk store, so inserts slow down as data grows (28 inserts/s at 2,000 chunks). A SIGKILL during concurrent writes lost no acknowledged writes; an actual power cut has not been tested.
- **No index checkpoints.** Indexes are rebuilt from stored chunks on startup. `CHECKPOINT_INTERVAL` in `.env.example` is not used.
- **Changing `index_type` is not atomic.** A chunk inserted while a library switches index type can be missing from the new index until the next restart.
- **Tests.** The 41 service-layer tests mock the repositories. 34 more tests cover the indexes, the reader-writer lock, persistence, and the HTTP API with real repositories. Load and crash behaviour is checked by the scripts in `benchmarks/`, not by `pytest`.

---

## 📄 License

MIT License

---

## 🎉 Project Status

A working prototype, built to learn how vector search works under the hood. It showcases:

✅ **Full-Stack Development** - Frontend + Backend + Infrastructure  
✅ **Modern Tech Stack** - FastAPI, Docker, Cohere AI  
✅ **Clean Code** - Architecture, documentation, testing  
✅ **Performance** - IVF search ~7-8x faster than exact search on real embeddings, with reproducible benchmark scripts  
✅ **UX Polish** - Responsive design, sample data, real-time search  

**🚀 Deploy Now:**
```powershell
docker-compose up -d
```