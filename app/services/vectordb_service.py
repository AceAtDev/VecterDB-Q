"""Vector database service containing business logic."""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import numpy as np

from app.domain.models import (
    Library, LibraryCreate, LibraryUpdate,
    Chunk, ChunkCreate, ChunkUpdate, Document, DocumentMetadata,
    SearchQuery, SearchResult
)
from app.repositories.vectordb_repository import VectorDBRepository


class VectorDBService:
    """Service layer for vector database operations."""
    
    def __init__(self, repository: VectorDBRepository) -> None:
        self.repository = repository
    
    def create_library(self, library_create: LibraryCreate) -> Library:
        library = Library(
            name=library_create.name,
            description=library_create.description,
            metadata=library_create.metadata,
            index_type=library_create.index_type
        )
        return self.repository.create_library(library)
    
    def get_library(self, library_id: UUID) -> Optional[Library]:
        return self.repository.get_library(library_id)
    
    def list_libraries(self) -> List[Library]:
        return self.repository.list_libraries()
    
    def update_library(self, library_id: UUID, library_update: LibraryUpdate) -> Optional[Library]:
        library = self.repository.get_library(library_id)
        if not library:
            return None
        
        if library_update.name is not None:
            library.name = library_update.name
        if library_update.description is not None:
            library.description = library_update.description
        if library_update.metadata is not None:
            library.metadata = library_update.metadata
        if library_update.index_type is not None:
            library.index_type = library_update.index_type
        
        library.updated_at = datetime.utcnow()
        
        return self.repository.update_library(library_id, library)
    
    def delete_library(self, library_id: UUID) -> bool:
        return self.repository.delete_library(library_id)
    
    def create_chunk(self, library_id: UUID, chunk_create: ChunkCreate) -> Optional[Chunk]:
        library = self.repository.get_library(library_id)
        if not library:
            return None
        
        chunk = Chunk(
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata,
            document_id=chunk_create.document_id
        )
        
        document = None
        if chunk_create.document_id:
            for doc in library.documents:
                if doc.id == chunk_create.document_id:
                    document = doc
                    break
        
        if not document:
            document = Document(
                library_id=library_id,
                metadata=DocumentMetadata(title="Default Document")
            )
            library.documents.append(document)
            chunk.document_id = document.id
        
        document.chunks.append(chunk)
        document.updated_at = datetime.utcnow()
        library.updated_at = datetime.utcnow()
        
        self.repository.add_chunk_to_library(library_id, chunk)
        
        return chunk
    
    def get_chunk(self, library_id: UUID, chunk_id: UUID) -> Optional[Chunk]:
        return self.repository.get_chunk(library_id, chunk_id)
    
    def list_chunks(self, library_id: UUID) -> List[Chunk]:
        return self.repository.list_chunks(library_id)
    
    def update_chunk(self, library_id: UUID, chunk_id: UUID, chunk_update: ChunkUpdate) -> Optional[Chunk]:
        chunk = self.repository.get_chunk(library_id, chunk_id)
        if not chunk:
            return None
        
        if chunk_update.text is not None:
            chunk.text = chunk_update.text
        if chunk_update.embedding is not None:
            chunk.embedding = chunk_update.embedding
        if chunk_update.metadata is not None:
            chunk.metadata = chunk_update.metadata
        if chunk_update.document_id is not None:
            chunk.document_id = chunk_update.document_id
        
        chunk.updated_at = datetime.utcnow()
        
        return self.repository.update_chunk(library_id, chunk_id, chunk)
    
    def delete_chunk(self, library_id: UUID, chunk_id: UUID) -> bool:
        return self.repository.delete_chunk(library_id, chunk_id)
    
    def search(self, library_id: UUID, search_query: SearchQuery) -> List[SearchResult]:
        """Perform k-NN search with optional metadata filtering."""
        library = self.repository.get_library(library_id)
        if not library:
            return []
        
        query_vector = np.array(search_query.embedding)
        results = self.repository.search_library(library_id, query_vector, search_query.k)
        
        search_results = []
        for chunk_id_str, distance in results:
            chunk_id = UUID(chunk_id_str)
            chunk = self.repository.get_chunk(library_id, chunk_id)
            
            if not chunk:
                continue
            
            if search_query.filters and not self._matches_filters(chunk, search_query.filters):
                continue
            
            similarity = 1.0 / (1.0 + distance)
            
            search_results.append(SearchResult(
                chunk=chunk,
                score=similarity,
                distance=distance
            ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:search_query.k]
    
    @staticmethod
    def _matches_filters(chunk: Chunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk matches metadata filters. Supports nested keys with dot notation."""
        metadata_dict = chunk.metadata.model_dump()
        
        for key, value in filters.items():
            keys = key.split('.')
            current = metadata_dict
            
            try:
                for k in keys:
                    current = current[k]
            except (KeyError, TypeError):
                return False
            
            if isinstance(value, str) and isinstance(current, str):
                if value.lower() not in current.lower():
                    return False
            elif isinstance(value, list):
                if current not in value:
                    return False
            else:
                if current != value:
                    return False
        
        return True
