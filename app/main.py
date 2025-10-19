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

# Initialize repository on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the repository on startup to load persisted data."""
    from app.api.dependencies import get_repository
    print("\n🚀 [APP STARTUP] Initializing repository...")
    repo = get_repository()
    print(f"✅ [APP STARTUP] Repository initialized with {len(repo._libraries)} libraries\n")

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
    from app.api.dependencies import get_repository
    repo = get_repository()
    
    debug_info = {
        "total_libraries": len(repo._libraries),
        "total_indexes": len(repo._indexes),
        "libraries": {}
    }
    
    for lib_id, library in repo._libraries.items():
        index = repo._indexes.get(lib_id)
        total_chunks = sum(len(doc.chunks) for doc in library.documents)
        
        # More detailed debugging
        index_info = {
            "library_name": library.name,
            "index_type": library.index_type,
            "total_chunks": total_chunks,
            "index_is_none": index is None,
            "index_exists_in_dict": lib_id in repo._indexes,
            "index_type_str": str(type(index)),
            "index_repr": repr(index),
        }
        
        # Try to get index properties
        try:
            index_info["index_len"] = len(index) if index else 0
        except:
            index_info["index_len"] = "ERROR"
        
        try:
            index_info["index_class"] = type(index).__name__ if index else None
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
