"""Dependencies for API endpoints with proper separation of concerns."""
from functools import lru_cache

from app.core.config import settings
from app.repositories.library_repository import LibraryRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.index_repository import IndexRepository
from app.services.library_service import LibraryService
from app.services.chunk_service import ChunkService
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService


# ============================================================================
# Repository Singletons (Data Access Layer)
# ============================================================================

@lru_cache()
def get_library_repository() -> LibraryRepository:
    """
    Get or create the library repository singleton.
    
    Uses lru_cache to ensure single instance across application.
    Handles library data persistence and retrieval.
    """
    persistence_path = settings.persistence_path if settings.persistence_enabled else None
    return LibraryRepository(persistence_path=persistence_path)


@lru_cache()
def get_chunk_repository() -> ChunkRepository:
    """
    Get or create the chunk repository singleton.
    
    Uses lru_cache to ensure single instance across application.
    Handles chunk data persistence and retrieval.
    """
    persistence_path = settings.persistence_path if settings.persistence_enabled else None
    return ChunkRepository(persistence_path=persistence_path)


@lru_cache()
def get_index_repository() -> IndexRepository:
    """
    Get or create the index repository singleton.
    
    Uses lru_cache to ensure single instance across application.
    Handles vector index operations (not persisted - rebuilt on load).
    """
    return IndexRepository()


# ============================================================================
# Service Layer (Business Logic)
# ============================================================================

def get_library_service() -> LibraryService:
    """
    Get the library service with its dependencies.
    
    Service handles library business logic, index creation, and hydrates libraries with documents.
    Depends on: LibraryRepository, IndexRepository, ChunkRepository
    """
    library_repo = get_library_repository()
    index_repo = get_index_repository()
    chunk_repo = get_chunk_repository()
    return LibraryService(
        repository=library_repo, 
        index_repository=index_repo,
        chunk_repository=chunk_repo
    )


def get_chunk_service() -> ChunkService:
    """
    Get the chunk service with its dependencies.
    
    Service handles chunk business logic and index updates.
    Depends on: ChunkRepository, LibraryService, IndexRepository
    """
    chunk_repo = get_chunk_repository()
    library_service = get_library_service()
    index_repo = get_index_repository()
    return ChunkService(
        repository=chunk_repo,
        library_service=library_service,
        index_repository=index_repo
    )


def get_search_service() -> SearchService:
    """
    Get the search service with its dependencies.
    
    Service handles vector search operations.
    Depends on: LibraryService, ChunkRepository, IndexRepository
    """
    library_service = get_library_service()
    chunk_repo = get_chunk_repository()
    index_repo = get_index_repository()
    return SearchService(
        library_service=library_service,
        chunk_repository=chunk_repo,
        index_repository=index_repo
    )


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    Get or create the embedding service singleton.

    Singleton so the local model is loaded once and shared across requests.
    """
    return EmbeddingService(
        provider=settings.embedding_provider,
        cohere_api_key=settings.cohere_api_key,
        local_model=settings.local_embedding_model
    )
