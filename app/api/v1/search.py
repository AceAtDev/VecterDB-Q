"""Search endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.models import SearchQuery, SearchResult
from app.services.vectordb_service import VectorDBService
from app.api.dependencies import get_service


router = APIRouter()


@router.post(
    "/{library_id}/search",
    response_model=List[SearchResult],
    summary="Search for similar vectors",
    description="Perform k-NN search in a library with optional metadata filtering."
)
def search_library(
    library_id: UUID,
    query: SearchQuery,
    service: VectorDBService = Depends(get_service)
) -> List[SearchResult]:
    """
    Search for k nearest neighbors in a library.
    
    The search uses the library's configured index type and returns
    results sorted by similarity score (higher is more similar).
    
    Metadata filters can be applied to narrow down results.
    """
    # Verify library exists
    library = service.get_library(library_id)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
    
    try:
        results = service.search(library_id, query)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
