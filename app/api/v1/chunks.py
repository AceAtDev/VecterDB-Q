"""Chunk CRUD endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.models import Chunk, ChunkCreate, ChunkUpdate
from app.services.chunk_service import ChunkService
from app.api.dependencies import get_chunk_service


router = APIRouter()


@router.post(
    "/{library_id}/chunks",
    response_model=Chunk,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chunk in a library",
    description="Add a new chunk with embedding to the specified library."
)
def create_chunk(
    library_id: UUID,
    chunk: ChunkCreate,
    service: ChunkService = Depends(get_chunk_service)
) -> Chunk:
    """Create a chunk in a library."""
    try:
        created_chunk = service.create_chunk(library_id, chunk)
    except ValueError as e:
        # e.g. embedding dimension does not match the library's index; nothing was stored
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not created_chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
    return created_chunk


@router.get(
    "/{library_id}/chunks",
    response_model=List[Chunk],
    summary="List chunks in a library",
    description="Retrieve all chunks from the specified library."
)
def list_chunks(
    library_id: UUID,
    service: ChunkService = Depends(get_chunk_service)
) -> List[Chunk]:
    """List all chunks in a library."""
    # Verify library exists
    library = service.library_service.get_library(library_id)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
    
    return service.list_chunks(library_id)


@router.get(
    "/{library_id}/chunks/{chunk_id}",
    response_model=Chunk,
    summary="Get a chunk by ID",
    description="Retrieve a specific chunk from a library."
)
def get_chunk(
    library_id: UUID,
    chunk_id: UUID,
    service: ChunkService = Depends(get_chunk_service)
) -> Chunk:
    """Get a chunk by ID."""
    chunk = service.get_chunk(library_id, chunk_id)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk with ID {chunk_id} not found in library {library_id}"
        )
    return chunk


@router.put(
    "/{library_id}/chunks/{chunk_id}",
    response_model=Chunk,
    summary="Update a chunk",
    description="Update an existing chunk's content or metadata."
)
def update_chunk(
    library_id: UUID,
    chunk_id: UUID,
    chunk_update: ChunkUpdate,
    service: ChunkService = Depends(get_chunk_service)
) -> Chunk:
    """Update a chunk."""
    try:
        chunk = service.update_chunk(library_id, chunk_id, chunk_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk with ID {chunk_id} not found in library {library_id}"
        )
    return chunk


@router.delete(
    "/{library_id}/chunks/{chunk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chunk",
    description="Remove a chunk from a library."
)
def delete_chunk(
    library_id: UUID,
    chunk_id: UUID,
    service: ChunkService = Depends(get_chunk_service)
) -> None:
    """Delete a chunk."""
    success = service.delete_chunk(library_id, chunk_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk with ID {chunk_id} not found in library {library_id}"
        )
