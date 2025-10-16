# Quick Start Guide - VectorDB-Q

## 🚀 Getting Started

This project is now fully set up! Here's how to get it running:

### Option 1: Using Docker (Recommended)

```powershell
# Build and start the container
docker-compose up --build

# The API will be available at:
# - Main API: http://localhost:8000
# - Interactive Docs: http://localhost:8000/docs
# - Alternative Docs: http://localhost:8000/redoc
```

### Option 2: Local Development

```powershell
# Create a virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 Testing the API

### Using the Demo Script

```powershell
# With the API running, run the demo in another terminal
python demo.py
```

### Using the Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Try creating a library, adding chunks, and searching!

### Using curl

```powershell
# Create a library
curl -X POST "http://localhost:8000/api/v1/libraries" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "My Library",
    "description": "Test library",
    "metadata": {"category": "test"},
    "index_type": "flat"
  }'
```

## 🧪 Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
# Open htmlcov/index.html in your browser
```

## 📁 Project Structure

```
VecterDB-Q/
├── app/
│   ├── api/              # API endpoints (controllers)
│   │   └── v1/
│   │       ├── libraries.py    # Library CRUD
│   │       ├── chunks.py       # Chunk CRUD
│   │       └── search.py       # Search endpoint
│   ├── core/             # Core components
│   │   ├── config.py          # Configuration
│   │   ├── locks.py           # Thread-safety
│   │   └── indexes/           # Vector indexes
│   │       ├── base.py        # Base index interface
│   │       ├── flat_index.py  # Brute-force index
│   │       └── ivf_index.py   # IVF index
│   ├── domain/           # Domain models
│   │   └── models.py          # Pydantic schemas
│   ├── repositories/     # Data access layer
│   │   └── vectordb_repository.py
│   ├── services/         # Business logic layer
│   │   └── vectordb_service.py
│   └── main.py           # FastAPI application
├── tests/                # Unit tests
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker orchestration
└── README.md           # Full documentation
```

## 🎯 Key Features Implemented

✅ **CRUD Operations**: Full Create, Read, Update, Delete for libraries and chunks
✅ **Custom Indexing**: Flat and IVF indexes implemented from scratch
✅ **Thread-Safe**: Reader-writer locks for concurrent access
✅ **Metadata Filtering**: Advanced query filtering
✅ **Persistence**: Optional disk persistence
✅ **Docker Ready**: Fully containerized
✅ **API Documentation**: Auto-generated OpenAPI docs
✅ **Tests**: Unit tests included

## 🔧 Configuration

Edit `.env` file to customize:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Cohere API Key (for embeddings)
COHERE_API_KEY=your_key_here

# Database Configuration
PERSISTENCE_ENABLED=true
PERSISTENCE_PATH=/app/data/vectordb.pkl

# Logging
LOG_LEVEL=INFO
```

## 📚 Next Steps

1. **Review the code** - Start with `app/main.py` and explore the architecture
2. **Read the README.md** - Detailed documentation on design choices
3. **Run the demo** - See the API in action with `python demo.py`
4. **Explore the tests** - Understand how components work
5. **Try the interactive docs** - Play with the API at http://localhost:8000/docs

## 🐛 Troubleshooting

**Port already in use?**
```powershell
# Change port in .env file
API_PORT=8001
```

**Dependencies not installing?**
```powershell
# Upgrade pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Docker issues?**
```powershell
# Remove old containers
docker-compose down
docker system prune -f
docker-compose up --build
```

## 💡 Tips

- The **Flat index** is best for small datasets (<10k vectors)
- The **IVF index** is better for larger datasets (10k-1M vectors)
- Use **metadata filters** to narrow down search results
- Check the **logs** for debugging: `docker-compose logs -f`

Happy coding! 🎉
