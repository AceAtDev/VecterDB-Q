"""FastAPI application entry point."""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api.v1 import api_router


app = FastAPI(
    title="VectorDB-Q",
    description="A REST API for indexing and querying documents within a Vector Database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize repositories on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the repositories on startup to load persisted data."""
    from app.api.dependencies import (
        get_library_repository, 
        get_chunk_repository, 
        get_index_repository
    )
    print("\n🚀 [APP STARTUP] Initializing repositories...")
    
    # Initialize all repositories (triggers data loading from disk)
    library_repo = get_library_repository()
    chunk_repo = get_chunk_repository()
    index_repo = get_index_repository()
    
    print(f"✅ [APP STARTUP] Library repository initialized with {len(library_repo._libraries)} libraries")
    
    # Count total chunks across all libraries
    total_chunks = sum(len(chunks) for chunks in chunk_repo._chunks.values())
    print(f"✅ [APP STARTUP] Chunk repository initialized with {total_chunks} chunks")
    
    # Drop chunks left behind by libraries deleted before delete cascaded to chunks
    orphaned = [lib_id for lib_id in list(chunk_repo._chunks) if lib_id not in library_repo._libraries]
    for lib_id in orphaned:
        removed = chunk_repo.delete_library_chunks(lib_id)
        print(f"🧹 [APP STARTUP] Removed {removed} orphaned chunks of deleted library {lib_id}")
    
    # Rebuild indexes for all libraries
    for library_id, library in library_repo._libraries.items():
        try:
            # Create index if it doesn't exist
            if index_repo.get_index(library_id) is None:
                print(f"🔨 [APP STARTUP] Creating index for library: {library.name}")
                index_repo.create_index(library_id, library.index_type)
            
            # Rebuild index with all chunks
            documents = chunk_repo.get_documents_for_library(library_id)
            if documents:
                vectors = []
                chunk_ids = []
                for doc in documents:
                    for chunk in doc.chunks:
                        vectors.append(chunk.embedding)
                        chunk_ids.append(str(chunk.id))
                
                if vectors:
                    import numpy as np
                    index_repo.rebuild_index(library_id, np.array(vectors), chunk_ids)
                    print(f"✅ [APP STARTUP] Rebuilt index for '{library.name}' with {len(vectors)} vectors")
        except Exception as e:
            print(f"❌ [APP STARTUP] Error rebuilding index for library {library_id}: {e}")
    
    print(f"✅ [APP STARTUP] Index repository initialized with {len(index_repo._indexes)} indexes\n")

# CORS middleware - allow all origins for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Serve frontend if it exists
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/", tags=["root"])
async def root():
    """Serve the frontend or API info."""
    frontend_file = frontend_dir / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    return {
        "name": "VectorDB-Q",
        "version": "1.0.0",
        "description": "Vector Database REST API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "vectordb-q"
    }


@app.get("/debug/indexes", tags=["debug"])
async def debug_indexes():
    """Debug endpoint to check index status."""
    from app.api.dependencies import (
        get_library_repository,
        get_chunk_repository,
        get_index_repository
    )
    
    library_repo = get_library_repository()
    chunk_repo = get_chunk_repository()
    index_repo = get_index_repository()
    
    debug_info = {
        "total_libraries": len(library_repo._libraries),
        "total_indexes": len(index_repo._indexes),
        "libraries": {}
    }
    
    for lib_id, library in library_repo._libraries.items():
        index = index_repo.get_index(lib_id)
        documents = chunk_repo.get_documents_for_library(lib_id)
        total_chunks = sum(len(doc.chunks) for doc in documents)
        
        # More detailed debugging
        index_info = {
            "library_name": library.name,
            "index_type": library.index_type,
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "index_exists": index is not None,
            "index_type_str": str(type(index)),
        }
        
        # Try to get index properties
        try:
            index_info["index_size"] = len(index) if index is not None else 0
        except:
            index_info["index_size"] = "ERROR"
        
        try:
            index_info["index_class"] = type(index).__name__ if index is not None else None
        except:
            index_info["index_class"] = "ERROR"
            
        debug_info["libraries"][str(lib_id)] = index_info
    
    return debug_info


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
