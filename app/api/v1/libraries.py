"""Library CRUD endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.models import Library, LibraryCreate, LibraryUpdate
from app.services.vectordb_service import VectorDBService
from app.api.dependencies import get_service


router = APIRouter()


@router.post("", response_model=Library, status_code=status.HTTP_201_CREATED)
def create_library(
    library: LibraryCreate,
    service: VectorDBService = Depends(get_service)
) -> Library:
    try:
        return service.create_library(library)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create library: {str(e)}"
        )


@router.get("", response_model=List[Library])
def list_libraries(service: VectorDBService = Depends(get_service)) -> List[Library]:
    return service.list_libraries()


@router.get("/{library_id}", response_model=Library)
def get_library(
    library_id: UUID,
    service: VectorDBService = Depends(get_service)
) -> Library:
    library = service.get_library(library_id)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
    return library


@router.put("/{library_id}", response_model=Library)
def update_library(
    library_id: UUID,
    library_update: LibraryUpdate,
    service: VectorDBService = Depends(get_service)
) -> Library:
    library = service.update_library(library_id, library_update)
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
    return library


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_library(
    library_id: UUID,
    service: VectorDBService = Depends(get_service)
) -> None:
    success = service.delete_library(library_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Library with ID {library_id} not found"
        )
