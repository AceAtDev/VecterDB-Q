# 🎨 Visual Architecture Diagram

## Data Flow Example: Creating a Chunk

```
┌─────────────────────────────────────────────────────────────────┐
│  CLIENT (Browser, curl, Python script)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST Request
                            │ /api/v1/libraries/{id}/chunks
                            │ { "text": "...", "embedding": [...] }
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  API LAYER (app/api/v1/chunks.py)                               │
│                                                                  │
│  @router.post("/{library_id}/chunks")                           │
│  def create_chunk(library_id, chunk, service):                  │
│      ├─ Validate HTTP request                                   │
│      ├─ Parse JSON data                                         │
│      ├─ Call service ─────────────┐                             │
│      └─ Return HTTP response      │                             │
└───────────────────────────────────┼─────────────────────────────┘
                                    │
                                    │ service.create_chunk()
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER (app/services/vectordb_service.py)               │
│                                                                  │
│  def create_chunk(library_id, chunk_create):                    │
│      ├─ Check if library exists ────────┐                       │
│      ├─ Validate business rules         │                       │
│      ├─ Create Chunk object             │                       │
│      ├─ Find/create Document            │                       │
│      ├─ Add chunk to document           │                       │
│      └─ Call repository ────────────────┼──┐                    │
└─────────────────────────────────────────┼──┼────────────────────┘
                                          │  │
                      repository.get()    │  │ repository.add()
                                          ▼  ▼
┌─────────────────────────────────────────────────────────────────┐
│  REPOSITORY LAYER (app/repositories/vectordb_repository.py)     │
│                                                                  │
│  def add_chunk_to_library(library_id, chunk):                   │
│      ├─ Acquire write lock 🔒                                   │
│      ├─ Store chunk in memory                                   │
│      ├─ Update vector index ───────────┐                        │
│      ├─ Persist to disk               │                        │
│      └─ Release lock 🔓                │                        │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                                         │ index.add()
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CORE - INDEXES (app/core/indexes/flat_index.py)                │
│                                                                  │
│  def add(vectors, ids):                                          │
│      ├─ Store vector with ID                                    │
│      └─ Rebuild search matrix                                   │
└─────────────────────────────────────────────────────────────────┘
                                         │
                                         │ Success!
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  DOMAIN MODELS (app/domain/models.py)                           │
│                                                                  │
│  class Chunk(BaseModel):                                         │
│      id: UUID                                                    │
│      text: str                                                   │
│      embedding: List[float]                                      │
│      metadata: ChunkMetadata                                     │
│                                                                  │
│  (Used by ALL layers to represent data)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

```
┌──────────────────────────────────────────────────────────────┐
│ API LAYER                                                     │
│ • Parse HTTP requests                                         │
│ • Validate input                                              │
│ • Handle errors → HTTP status codes                           │
│ • Return responses                                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ SERVICE LAYER                                                 │
│ • Business logic & validation                                 │
│ • Orchestrate multiple operations                             │
│ • Apply business rules                                        │
│ • Coordinate between repositories                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ REPOSITORY LAYER                                              │
│ • CRUD operations (Create, Read, Update, Delete)              │
│ • Thread-safe access (locks)                                  │
│ • Persistence to disk                                         │
│ • Manage indexes                                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ DOMAIN MODELS                                                 │
│ • Define data structures                                      │
│ • Validation rules                                            │
│ • Type safety                                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Simple Analogy: Building a House

```
┌─────────────────────────────────────────────────────────┐
│  YOU (Client)                                            │
│  "I want to build a house"                               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  RECEPTIONIST (API)                                      │
│  • Takes your request                                    │
│  • Gives you forms to fill                               │
│  • Schedules appointment                                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  ARCHITECT (Service)                                     │
│  • Reviews your requirements                             │
│  • Checks building codes (business rules)                │
│  • Designs the plan                                      │
│  • Coordinates everything                                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  CONTRACTOR (Repository)                                 │
│  • Actually builds the house                             │
│  • Manages materials (data)                              │
│  • Handles construction (storage)                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  BLUEPRINT (Domain Models)                               │
│  • Defines what a "house" is                             │
│  • Specifications (rooms, doors, windows)                │
│  • Standards everyone follows                            │
└─────────────────────────────────────────────────────────┘
```

---

## Code Example: All Layers Together

### Request: "Create a chunk in library abc-123"

```python
# ============================================================
# 1. API LAYER - Takes the request
# ============================================================
# File: app/api/v1/chunks.py

@router.post("/{library_id}/chunks")
def create_chunk(
    library_id: UUID,
    chunk: ChunkCreate,  # ← Uses Domain Model
    service: VectorDBService = Depends(get_service)
):
    """
    My job:
    - Receive HTTP request
    - Validate it's proper JSON
    - Pass to service
    - Return HTTP response
    """
    result = service.create_chunk(library_id, chunk)
    
    if not result:
        raise HTTPException(404, "Library not found")
    
    return result  # FastAPI converts to JSON


# ============================================================
# 2. SERVICE LAYER - Implements business logic
# ============================================================
# File: app/services/vectordb_service.py

class VectorDBService:
    def create_chunk(self, library_id: UUID, chunk_create: ChunkCreate):
        """
        My job:
        - Check business rules
        - Coordinate operations
        - Transform data if needed
        """
        # Business rule: Library must exist
        library = self.repository.get_library(library_id)
        if not library:
            return None
        
        # Create the domain object
        chunk = Chunk(
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata
        )
        
        # Business rule: Chunk needs a document parent
        document = self._find_or_create_document(library, chunk)
        document.chunks.append(chunk)
        
        # Store it
        self.repository.add_chunk_to_library(library_id, chunk)
        
        return chunk


# ============================================================
# 3. REPOSITORY LAYER - Handles storage
# ============================================================
# File: app/repositories/vectordb_repository.py

class VectorDBRepository:
    def add_chunk_to_library(self, library_id: UUID, chunk: Chunk):
        """
        My job:
        - Store data safely
        - Update indexes
        - Handle persistence
        - Ensure thread-safety
        """
        with self._lock.write_lock():  # Thread-safe!
            # Get the index for this library
            index = self._indexes.get(library_id)
            
            # Add to vector index
            vector = np.array(chunk.embedding)
            index.add(np.array([vector]), [str(chunk.id)])
            
            # Persist to disk
            self._persist()
        
        return chunk


# ============================================================
# 4. DOMAIN MODELS - Defines what data looks like
# ============================================================
# File: app/domain/models.py

class Chunk(BaseModel):
    """
    My job:
    - Define the structure of a Chunk
    - Validate data
    - Provide type safety
    """
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_length=1)
    metadata: ChunkMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChunkCreate(BaseModel):
    """Schema for creating a chunk (no ID yet)"""
    text: str
    embedding: List[float]
    metadata: ChunkMetadata
```

---

## Why Each Layer Matters

### Without Layers (Mixed Together):
```python
# ❌ Everything in one place - HARD to maintain!

@app.post("/chunks")
def create_chunk(request):
    # HTTP stuff
    data = request.json()
    
    # Validation
    if not data.get("text"):
        return Response(400)
    
    # Database access
    chunk = {"id": uuid4(), "text": data["text"]}
    in_memory_db[chunk["id"]] = chunk
    
    # Index update
    vector_index.add(data["embedding"])
    
    # Persistence
    with open("db.pkl", "wb") as f:
        pickle.dump(in_memory_db, f)
    
    # HTTP response
    return JSONResponse(chunk)

# Problems:
# - Can't test without HTTP server
# - Can't change database without rewriting everything
# - Hard to understand what's happening
# - Violates "Single Responsibility Principle"
```

### With Layers (Clean Separation):
```python
# ✅ Each piece does ONE thing - EASY to maintain!

# API: Just HTTP
@app.post("/chunks")
def create_chunk(data, service):
    return service.create_chunk(data)

# Service: Just business logic
def create_chunk(self, data):
    chunk = Chunk(**data)
    return self.repo.save(chunk)

# Repository: Just storage
def save(self, chunk):
    with self.lock:
        self.storage[chunk.id] = chunk
        self.persist()

# Benefits:
# ✓ Test service without HTTP
# ✓ Change database easily
# ✓ Clear responsibilities
# ✓ Easy to understand
```

---

## 🎓 Summary

**Domain Models**: "What is the data?" → Blueprints
**Repository**: "Where is the data?" → Storage manager
**Service**: "How to process?" → Business logic
**API**: "How to access?" → Interface

Each layer talks to the layer below it:
```
API → Service → Repository → Storage
```

Never skip layers! ❌
```
API → Repository  # Skip service? Bad!
API → Storage     # Skip everything? Terrible!
```

---

Hope this makes it crystal clear! 🎉
