"""Dependencies for API endpoints."""
from functools import lru_cache

from app.core.config import settings
from app.repositories.vectordb_repository import VectorDBRepository
from app.services.vectordb_service import VectorDBService


@lru_cache()
def get_repository() -> VectorDBRepository:
    """
    Get or create the vector database repository singleton.
    
    Uses lru_cache to ensure single instance across application.
    """
    persistence_path = settings.persistence_path if settings.persistence_enabled else None
    return VectorDBRepository(persistence_path=persistence_path)


def get_service() -> VectorDBService:
    """
    Get the vector database service.
    
    Creates a new service instance with the repository dependency.
    """
    repository = get_repository()
    return VectorDBService(repository=repository)
