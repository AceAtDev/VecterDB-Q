"""API v1 routes."""
from fastapi import APIRouter
from app.api.v1 import libraries, chunks, search

api_router = APIRouter()

# Include sub-routers
api_router.include_router(libraries.router, prefix="/libraries", tags=["libraries"])
api_router.include_router(chunks.router, prefix="/libraries", tags=["chunks"])
api_router.include_router(search.router, prefix="/libraries", tags=["search"])
