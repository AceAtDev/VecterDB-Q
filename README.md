# VectorDB-Q: Semantic Search Engine

A production-ready semantic search system with a beautiful web interface, REST API, and intelligent vector indexing algorithms. Built with Python, FastAPI, and vanilla JavaScript.

## ✨ What Makes This Special?

🎯 **Semantic Search** - Find documents by meaning, not just keywords  
🚀 **Fast** - ~30 ms IVF search over 100K vectors, 2-7x faster than exact search depending on data (measured, see [Performance](#-performance-at-scale))  
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
│  │  │ O(n) time    │    │ O(log n)     │                   │ │
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

Reproduce with `python benchmarks/bench_indexes.py --n 100000 --data random` (or `--data clustered`). Synthetic 384-dimension vectors, top-10 search, median of 20 queries, default IVF settings (100 clusters, `n_probe=10`). Measured October 2026 on an AMD Ryzen 7 8845HS, single process.

| Data | Vectors | Flat (exact) | IVF (approximate) | Speedup | IVF build | IVF recall@10 |
|------|---------|--------------|-------------------|---------|-----------|---------------|
| Uniform random | 10,000 | 17 ms | 4 ms | ~4.4x | 34 s | not measured |
| Uniform random | 100,000 | 206 ms | 30 ms | ~6.9x | 380 s | 0.20 |
| Clustered | 10,000 | 19 ms | 9 ms | ~2x | 12 s | 1.00 |

Speed and recall trade off with the data: on uniform random vectors (worst case for IVF) every cluster is similar in size, so IVF is fast but misses most true neighbours. On clustered vectors, closer to real embeddings, IVF finds every true neighbour but probes larger clusters.

**Not measured at 1M.** k-means training and IVF search are currently pure-Python loops, so build time grows linearly (~1 hour projected at 1M) and IVF search would scan ~100K vectors per query. Vectorizing both with NumPy is the next step before claiming million-scale numbers.

### Algorithm Comparison

| Feature | Flat Index | IVF Index |
|---------|------------|-----------|
| **Build Time** | Instant | O(n·k·i), 380 s measured for 100K |
| **Search Time** | O(n·d) | O(k·d + (n_probe/k)·n·d): scans ~10% of vectors by default |
| **Memory** | O(n·d) | O(n·d + k·d) |
| **Accuracy** | 100% (exact) | Depends on data: 1.00 recall@10 clustered, 0.20 random |
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

- **Smart Indexing**: Flat (exact) or IVF (2-7x faster in measured benchmarks)
- **Production-Ready**: 1000+ concurrent searches
- **Real AI**: Cohere production embeddings
- **Clean Architecture**: 4-layer DDD design
- **Beautiful UX**: Responsive with sample data

---



## 📄 License

MIT License

---

## 🎉 Production Ready!

This project is fully functional and ready for demonstration. It showcases:

✅ **Full-Stack Development** - Frontend + Backend + Infrastructure  
✅ **Modern Tech Stack** - FastAPI, Docker, Cohere AI  
✅ **Clean Code** - Architecture, documentation, testing  
✅ **Performance** - 2-7x faster search with IVF, with a reproducible benchmark script  
✅ **UX Polish** - Responsive design, sample data, real-time search  

**🚀 Deploy Now:**
```powershell
docker-compose up -d
```