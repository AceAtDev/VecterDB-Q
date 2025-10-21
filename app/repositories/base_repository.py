"""Base repository with common CRUD operations and thread-safe access."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID

from app.core.locks import RWLock


T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository providing common CRUD operations.
    
    Features:
    - Generic type support for any entity type
    - Thread-safe operations with read-write locks
    - Common interface for all repositories
    - Single Responsibility: Data access layer only
    
    Type Parameters:
        T: The entity type this repository manages
        
    Example:
        >>> class LibraryRepository(BaseRepository[Library]):
        ...     def save(self, entity: Library) -> Library:
        ...         # Implementation
        ...         pass
    """
    
    def __init__(self) -> None:
        """Initialize repository with thread-safe lock."""
        self._lock = RWLock()
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """Save an entity to the repository.
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with any modifications (e.g., generated ID)
            
        Raises:
            ValueError: If entity already exists or validation fails
        """
        pass
    
    @abstractmethod
    def find_by_id(self, id: UUID) -> Optional[T]:
        """Find an entity by its ID.
        
        Args:
            id: UUID of the entity to find
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """Retrieve all entities.
        
        Returns:
            List of all entities in the repository
        """
        pass
    
    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """Delete an entity by its ID.
        
        Args:
            id: UUID of the entity to delete
            
        Returns:
            True if entity was deleted, False if not found
        """
        pass
