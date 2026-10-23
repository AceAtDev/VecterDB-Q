"""Library service containing business logic for library operations."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.models import Library, LibraryCreate, LibraryUpdate


class LibraryService:
    """Service layer for library management operations.
    
    Handles all business logic related to library CRUD operations.
    Follows Single Responsibility Principle - only manages libraries.
    """
    
    def __init__(self, repository, index_repository=None, chunk_repository=None) -> None:
        """Initialize library service with repository dependency.
        
        Args:
            repository: LibraryRepository instance for data access
            index_repository: Optional IndexRepository for creating indexes
            chunk_repository: Optional ChunkRepository for hydrating libraries with documents
        """
        self.repository = repository
        self.index_repository = index_repository
        self.chunk_repository = chunk_repository
    
    def create_library(self, library_create: LibraryCreate) -> Library:
        """Create a new library.
        
        Args:
            library_create: Library creation request with name, description, metadata
            
        Returns:
            Created Library object with generated ID and timestamps
        """
        library = Library(
            name=library_create.name,
            description=library_create.description,
            metadata=library_create.metadata,
            index_type=library_create.index_type
        )
        result = self.repository.create_library(library)
        
        # Create vector index for the library
        if self.index_repository:
            self.index_repository.create_index(result.id, result.index_type)
        
        return result
    
    def _hydrate_library(self, library: Library) -> Library:
        """Hydrate a library with its documents and chunks from chunk repository.
        
        Args:
            library: Library object to hydrate
            
        Returns:
            Copy of the library with populated documents field. The stored
            library is left untouched, so libraries.pkl does not duplicate
            the chunk data held by the chunk repository.
        """
        if self.chunk_repository:
            documents = self.chunk_repository.get_documents_for_library(library.id)
            return library.model_copy(update={"documents": documents})
        return library
    
    def get_library(self, library_id: UUID) -> Optional[Library]:
        """Retrieve a library by ID.
        
        Args:
            library_id: UUID of the library to retrieve
            
        Returns:
            Library object if found, None otherwise
        """
        library = self.repository.get_library(library_id)
        if library:
            library = self._hydrate_library(library)
        return library
    
    def list_libraries(self) -> List[Library]:
        """Retrieve all libraries.
        
        Returns:
            List of all Library objects in the system
        """
        libraries = self.repository.list_libraries()
        # Hydrate each library with its documents
        return [self._hydrate_library(lib) for lib in libraries]
    
    def update_library(self, library_id: UUID, library_update: LibraryUpdate) -> Optional[Library]:
        """Update an existing library.
        
        Args:
            library_id: UUID of the library to update
            library_update: Library update request with optional fields
            
        Returns:
            Updated Library object if found, None otherwise
        """
        library = self.repository.get_library(library_id)
        if not library:
            return None
        
        # Check if index type is changing
        old_index_type = library.index_type
        index_type_changed = False
        
        # Update only provided fields
        if library_update.name is not None:
            library.name = library_update.name
        if library_update.description is not None:
            library.description = library_update.description
        if library_update.metadata is not None:
            library.metadata = library_update.metadata
        if library_update.index_type is not None:
            library.index_type = library_update.index_type
            if old_index_type != library_update.index_type:
                index_type_changed = True
        
        library.updated_at = datetime.utcnow()
        
        result = self.repository.update_library(library_id, library)
        
        # Recreate index if type changed
        if index_type_changed and self.index_repository:
            self.index_repository.delete_index(library_id)
            self.index_repository.create_index(library_id, library.index_type)
        
        return result
    
    def delete_library(self, library_id: UUID) -> bool:
        """Delete a library by ID.
        
        Args:
            library_id: UUID of the library to delete
            
        Returns:
            True if library was deleted, False if not found
        """
        result = self.repository.delete_library(library_id)
        
        # Delete associated index
        if result and self.index_repository:
            self.index_repository.delete_index(library_id)
        
        # Delete associated chunks so they are not left orphaned in chunks.pkl
        if result and self.chunk_repository:
            self.chunk_repository.delete_library_chunks(library_id)
        
        return result
