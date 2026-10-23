"""Chunk service containing business logic for chunk operations."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.models import Chunk, ChunkCreate, ChunkUpdate


class ChunkService:
    """Service layer for chunk management operations.
    
    Handles all business logic related to chunk CRUD operations.
    Follows Single Responsibility Principle - only manages chunks.
    """
    
    def __init__(self, repository, library_service, index_repository) -> None:
        """Initialize chunk service with dependencies.
        
        Args:
            repository: ChunkRepository instance for data access
            library_service: LibraryService for library validation
            index_repository: IndexRepository for updating vector indexes
        """
        self.repository = repository
        self.library_service = library_service
        self.index_repository = index_repository
    
    def create_chunk(self, library_id: UUID, chunk_create: ChunkCreate) -> Optional[Chunk]:
        """Create a new chunk and add it to a library.
        
        Args:
            library_id: UUID of the library to add chunk to
            chunk_create: Chunk creation request with text, embedding, metadata
            
        Returns:
            Created Chunk object if library exists, None otherwise
            
        Raises:
            ValueError: If the embedding dimension does not match the library's index.
                Nothing is stored in that case.
        """
        # Validate library exists
        library = self.library_service.get_library(library_id)
        if not library:
            return None
        
        # Reject a wrong-dimension embedding before anything is stored
        self.index_repository.validate_vector(library_id, chunk_create.embedding)
        
        # Create the chunk object
        chunk = Chunk(
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata,
            document_id=chunk_create.document_id
        )
        
        # Let the repository handle the actual addition (with proper locking)
        result = self.repository.create_chunk_in_library(library_id, chunk)
        
        # Update the vector index with new chunk
        if result:
            try:
                self.index_repository.add_vector(library_id, str(result.id), result.embedding)
            except ValueError:
                # A concurrent insert can change the index dimension between the
                # check above and this add; undo the store so nothing is left behind
                self.repository.delete_chunk(library_id, result.id)
                raise
        
        return result
    
    def get_chunk(self, library_id: UUID, chunk_id: UUID) -> Optional[Chunk]:
        """Retrieve a chunk by ID from a specific library.
        
        Args:
            library_id: UUID of the library containing the chunk
            chunk_id: UUID of the chunk to retrieve
            
        Returns:
            Chunk object if found, None otherwise
        """
        return self.repository.get_chunk(library_id, chunk_id)
    
    def list_chunks(self, library_id: UUID) -> List[Chunk]:
        """Retrieve all chunks in a library.
        
        Args:
            library_id: UUID of the library to list chunks from
            
        Returns:
            List of all Chunk objects in the library
        """
        return self.repository.list_chunks(library_id)
    
    def update_chunk(self, library_id: UUID, chunk_id: UUID, chunk_update: ChunkUpdate) -> Optional[Chunk]:
        """Update an existing chunk.
        
        Args:
            library_id: UUID of the library containing the chunk
            chunk_id: UUID of the chunk to update
            chunk_update: Chunk update request with optional fields
            
        Returns:
            Updated Chunk object if found, None otherwise
            
        Raises:
            ValueError: If the new embedding dimension does not match the library's index
        """
        existing = self.repository.get_chunk(library_id, chunk_id)
        if not existing:
            return None
        
        if chunk_update.embedding is not None:
            self.index_repository.validate_vector(library_id, chunk_update.embedding)
        
        # Work on a copy: the stored chunk is shared with concurrent readers and
        # must only change inside the repository's write lock
        chunk = existing.model_copy(deep=True)
        
        # Update only provided fields
        if chunk_update.text is not None:
            chunk.text = chunk_update.text
        if chunk_update.embedding is not None:
            chunk.embedding = chunk_update.embedding
        if chunk_update.metadata is not None:
            chunk.metadata = chunk_update.metadata
        if chunk_update.document_id is not None:
            chunk.document_id = chunk_update.document_id
        
        chunk.updated_at = datetime.utcnow()
        
        result = self.repository.update_chunk(library_id, chunk_id, chunk)
        
        # Update vector index if embedding changed
        if result and chunk_update.embedding is not None:
            self.index_repository.update_vector(library_id, str(chunk_id), chunk_update.embedding)
        
        return result
    
    def delete_chunk(self, library_id: UUID, chunk_id: UUID) -> bool:
        """Delete a chunk by ID from a library.
        
        Args:
            library_id: UUID of the library containing the chunk
            chunk_id: UUID of the chunk to delete
            
        Returns:
            True if chunk was deleted, False if not found
        """
        result = self.repository.delete_chunk(library_id, chunk_id)
        
        # Remove from vector index if deletion successful
        if result:
            self.index_repository.remove_vector(library_id, str(chunk_id))
        
        return result
