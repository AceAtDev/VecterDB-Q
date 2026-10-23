# 🏗️ VectorDB-Q Architecture

This document explains the internal design of VectorDB-Q, focusing on the service layer architecture and how components work together.

---

## 📐 Design Principles

VectorDB-Q follows **SOLID principles** and **Domain-Driven Design**:

- **Single Responsibility** - Each service handles one domain
- **Separation of Concerns** - Clear boundaries between layers
- **Dependency Injection** - Services receive dependencies, not create them
- **Testability** - All services can be tested with mocked dependencies

---

## 🎯 Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│                    API Routes                            │
│  • Handle HTTP requests/responses                       │
│  • Validate input                                       │
│  • Call appropriate service                             │
└────────────────────┬────────────────────────────────────┘
                     │ Dependency Injection
┌────────────────────▼────────────────────────────────────┐
│                  Service Layer                           │
│  • LibraryService  - Library CRUD + index creation      │
│  • ChunkService    - Chunk CRUD + index updates         │
│  • SearchService   - Vector search + metadata filtering │
└────────────────────┬────────────────────────────────────┘
                     │ Data Access
┌────────────────────▼────────────────────────────────────┐
│                Repository Layer                          │
│  • LibraryRepository - Library data persistence         │
│  • ChunkRepository   - Chunk/document storage           │
│  • IndexRepository   - Vector index management          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Service Layer Architecture

### LibraryService
**Purpose**: Manage libraries and their indexes

**Dependencies**:
- `LibraryRepository` - Store/retrieve library data
- `IndexRepository` - Create/manage vector indexes
- `ChunkRepository` - Get documents for library hydration

**Key Methods**:
```python
create_library(library_create) -> Library
  • Creates library in repository
  • Creates corresponding vector index
  • Returns library with index type

get_library(library_id) -> Library | None
  • Retrieves library from repository
  • Hydrates with documents from ChunkRepository
  • Returns complete library object

list_libraries() -> List[Library]
  • Gets all libraries
  • Hydrates each with their documents
  • Returns complete library list

update_library(library_id, update_data) -> Library | None
  • Updates library metadata
  • If index type changes, recreates index
  • Returns updated library

delete_library(library_id) -> bool
  • Removes library from repository
  • Deletes associated index
  • Returns success status
```

### ChunkService
**Purpose**: Manage text chunks and keep indexes in sync

**Dependencies**:
- `ChunkRepository` - Store/retrieve chunks
- `LibraryService` - Validate library exists
- `IndexRepository` - Update vector indexes

**Key Methods**:
```python
create_chunk(library_id, chunk_create) -> Chunk | None
  • Validates library exists
  • Creates chunk in repository
  • Adds vector to library's index
  • Returns created chunk

get_chunk(library_id, chunk_id) -> Chunk | None
  • Retrieves chunk from repository
  • Returns chunk or None if not found

list_chunks(library_id) -> List[Chunk]
  • Gets all chunks in library
  • Returns list (empty if none)

update_chunk(library_id, chunk_id, update_data) -> Chunk | None
  • Updates chunk in repository
  • If embedding changed, updates index
  • Returns updated chunk

delete_chunk(library_id, chunk_id) -> bool
  • Removes chunk from repository
  • Removes vector from index
  • Returns success status
```

### SearchService
**Purpose**: Perform semantic search with filtering

**Dependencies**:
- `LibraryService` - Validate library exists
- `ChunkRepository` - Get chunk details
- `IndexRepository` - Search vector index

**Key Methods**:
```python
search(library_id, search_query) -> List[SearchResult]
  • Validates library exists
  • Searches index with query vector
  • Retrieves chunk details for results
  • Applies metadata filters
  • Sorts by relevance score
  • Returns top K results

_matches_filters(chunk, filters) -> bool
  • Helper to check metadata filters
  • Supports dot notation (e.g., "custom.category")
  • Case-insensitive string matching
  • Returns True if all filters match
```

---

## 🔌 Dependency Injection Pattern

All services are created with dependency injection using FastAPI's dependency system:

```python
# app/api/dependencies.py

# Repository Singletons (one instance per app)
@lru_cache()
def get_library_repository() -> LibraryRepository:
    return LibraryRepository(persistence_path=settings.persistence_path)

@lru_cache()
def get_chunk_repository() -> ChunkRepository:
    return ChunkRepository(persistence_path=settings.persistence_path)

@lru_cache()
def get_index_repository() -> IndexRepository:
    return IndexRepository()

# Service Factory Functions (new instance per request)
def get_library_service() -> LibraryService:
    return LibraryService(
        repository=get_library_repository(),
        index_repository=get_index_repository(),
        chunk_repository=get_chunk_repository()
    )

def get_chunk_service() -> ChunkService:
    return ChunkService(
        repository=get_chunk_repository(),
        library_service=get_library_service(),
        index_repository=get_index_repository()
    )

def get_search_service() -> SearchService:
    return SearchService(
        library_service=get_library_service(),
        chunk_repository=get_chunk_repository(),
        index_repository=get_index_repository()
    )
```

**Why This Works**:
- **Repositories are singletons** (`@lru_cache`) - Only one instance per app
- **Services are created per request** - Fresh instance with injected dependencies
- **No global state** - Dependencies passed explicitly
- **Easy to test** - Can inject mocks instead of real repositories

---

## 📂 Repository Layer

### LibraryRepository
**Storage**: In-memory dictionary `{library_id: Library}`  
**Persistence**: Saves to `data/vectordb/libraries.pkl`  
**Thread-Safe**: Uses RWLock for concurrent access

**Key Features**:
- CRUD operations for libraries
- Whole-store snapshot on every write (temp file, fsync, rename, directory fsync)
- Stores libraries without their documents; chunk data lives only in `chunks.pkl`
- Automatic persistence on changes

### ChunkRepository
**Storage**: Nested dictionaries `{library_id: {chunk_id: Chunk}}`  
**Documents**: Separate storage `{library_id: [Document]}`  
**Persistence**: Saves to `data/vectordb/chunks.pkl`  
**Thread-Safe**: Uses RWLock for concurrent access

**Key Features**:
- CRUD operations for chunks
- Document management per library
- Batch operations for efficiency
- Whole-store snapshot on every write (temp file, fsync, rename, directory fsync)
- Deleting a library deletes its chunks and documents

### IndexRepository
**Storage**: In-memory dictionary `{library_id: VectorIndex}`  
**Persistence**: No persistence (rebuilt from chunks on startup)  
**Thread-Safe**: Uses RWLock for concurrent access

**Key Features**:
- Creates Flat or IVF indexes
- Add/update/remove vectors dynamically
- Rebuild indexes from source data
- K-NN search with cosine or euclidean distance

---

## 🔄 Data Flow Examples

### Creating a Chunk

```
Client Request → API Route → ChunkService
                                 │
                                 ├─→ LibraryService.get_library()
                                 │   └─→ LibraryRepository.get()
                                 │
                                 ├─→ ChunkRepository.create_chunk()
                                 │   └─→ Save to pickle file
                                 │
                                 └─→ IndexRepository.add_vector()
                                     └─→ Update in-memory index
                                           
Response ← Chunk Object
```

### Searching

```
Client Request → API Route → SearchService
                                 │
                                 ├─→ LibraryService.get_library()
                                 │   └─→ LibraryRepository.get()
                                 │
                                 ├─→ IndexRepository.search_library()
                                 │   └─→ K-NN search in index
                                 │
                                 ├─→ ChunkRepository.get_chunk() (for each result)
                                 │   └─→ Get chunk details
                                 │
                                 └─→ Apply filters, sort by score
                                           
Response ← List[SearchResult]
```

### Getting a Library (with Documents)

```
Client Request → API Route → LibraryService.get_library()
                                 │
                                 ├─→ LibraryRepository.get()
                                 │   └─→ Get library object
                                 │
                                 └─→ _hydrate_library()
                                     └─→ ChunkRepository.get_documents_for_library()
                                         └─→ Populate library.documents field
                                           
Response ← Library (with documents)
```

---

## 🧪 Testing Strategy

Each service has comprehensive unit tests with mocked dependencies:

### Test Structure
```python
# tests/services/test_library_service.py

@pytest.fixture
def mock_library_repository():
    return Mock()  # Mock repository

@pytest.fixture
def library_service(mock_library_repository, ...):
    return LibraryService(
        repository=mock_library_repository,
        index_repository=mock_index_repository,
        chunk_repository=mock_chunk_repository
    )

def test_create_library_success(library_service, mock_library_repository):
    # Arrange: Set up mocks
    mock_library_repository.create_library.return_value = sample_library
    
    # Act: Call service method
    result = library_service.create_library(library_create)
    
    # Assert: Verify behavior
    assert result is not None
    mock_library_repository.create_library.assert_called_once()
```

### Test Coverage
- **LibraryService**: 13 tests (create, get, list, update, delete + edge cases)
- **ChunkService**: 13 tests (CRUD + index synchronization)
- **SearchService**: 15 tests (search, filtering, metrics, edge cases)
- **Total**: 41 passing service-layer tests with mocked repositories (`tests/services`)

Outside the service layer, with real objects instead of mocks:
- **Indexes** (`tests/indexes`): 14 tests (IVF retraining and recall vs bulk build, seeded k-means, filtered search, dimension checks)
- **Persistence** (`tests/repositories`): 5 tests (round trip, no chunk copy in `libraries.pkl`, delete cascade, fsync, failed write keeps the old snapshot)
- **Reader-writer lock** (`tests/core`): 4 tests
- **HTTP API** (`tests/api`): 11 tests (wrong-dimension rejection, filter before top-k, `hnsw` rejection, index type change, `/debug/indexes`)

Load and crash behaviour is checked by the scripts in `benchmarks/`, not by `pytest`.

---

## 🚀 Benefits of This Architecture

### 1. **Single Responsibility**
Each service does one thing:
- LibraryService → Libraries
- ChunkService → Chunks
- SearchService → Search

### 2. **Easy to Test**
Mock dependencies and test in isolation:
```python
mock_repo = Mock()
service = ChunkService(repository=mock_repo, ...)
# Test service logic without touching database
```

### 3. **Easy to Extend**
Want to add a new feature? Add it to the right service:
- Batch chunk upload? → Add to `ChunkService`
- Advanced library search? → Add to `LibraryService`
- New search algorithm? → Add to `SearchService`

### 4. **Clear Boundaries**
Know exactly where to look:
- Bug in library creation? → `LibraryService`
- Search returning wrong results? → `SearchService`
- Data not persisting? → Repository layer

### 5. **Maintainable**
Each file has one clear purpose:
- `library_service.py` - ~150 lines
- `chunk_service.py` - ~130 lines
- `search_service.py` - ~150 lines

Compare to old monolithic `vectordb_service.py` (~400+ lines)!

---

## 📝 Design Decisions

### Why Separate Services?
**Before**: One `VectorDBService` handled everything  
**After**: Three focused services, each with clear responsibility  
**Reason**: Easier to understand, test, and modify

### Why Inject Dependencies?
**Before**: Services created their own repositories  
**After**: Dependencies passed in via constructor  
**Reason**: Can inject mocks for testing, easier to swap implementations

### Why Singleton Repositories?
**Before**: New repository instance per request  
**After**: One repository instance per app  
**Reason**: Repositories manage shared state (in-memory data), should be shared

### Why Hydrate Libraries?
**Before**: Libraries didn't include documents  
**After**: Service layer hydrates libraries with documents  
**Reason**: API responses need complete data, but storage is separated

---

## 🔍 Finding Your Way Around

### Adding a New Feature

**Question**: Where do I add library export functionality?

1. **Service Layer** (`app/services/library_service.py`):
   ```python
   def export_library(self, library_id: UUID) -> Dict:
       library = self.repository.get_library(library_id)
       documents = self.chunk_repository.get_documents_for_library(library_id)
       return {"library": library, "documents": documents}
   ```

2. **API Route** (`app/api/v1/libraries.py`):
   ```python
   @router.get("/{library_id}/export")
   def export_library(
       library_id: UUID,
       service: LibraryService = Depends(get_library_service)
   ):
       return service.export_library(library_id)
   ```

3. **Test** (`tests/services/test_library_service.py`):
   ```python
   def test_export_library(library_service, mock_repository):
       # Test the export logic with mocks
   ```

### Debugging a Bug

**Issue**: Search returns wrong results

1. **Start at Service** (`app/services/search_service.py`):
   - Check `search()` method logic
   - Verify filter matching in `_matches_filters()`

2. **Check Repository** (`app/repositories/index_repository.py`):
   - Verify `search_library()` implementation
   - Check index building in `rebuild_index()`

3. **Verify Data** (`app/repositories/chunk_repository.py`):
   - Ensure chunks are stored correctly
   - Check embeddings are valid

---

## 📚 Related Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - How to run and write tests

---

## 🎓 Key Takeaways

1. **Services = Business Logic** - Each service handles one domain
2. **Repositories = Data Access** - Each repository manages one type of data
3. **Dependency Injection** - Dependencies passed in, not created
4. **Testability** - Mock dependencies to test in isolation
5. **SOLID Principles** - Single Responsibility, easy to maintain

This architecture makes VectorDB-Q easy to understand, test, and extend! 🚀
