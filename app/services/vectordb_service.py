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
        """Create a new chunk and add it to a library."""
        # Create the chunk object
        chunk = Chunk(
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata,
            document_id=chunk_create.document_id
        )
        
        # Let the repository handle the actual addition (with proper locking)
        result = self.repository.create_chunk_in_library(library_id, chunk)
        return result
    
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
            print(f"❌ [SEARCH] Library {library_id} not found")
            return []
        
        # Log search details
        total_chunks = sum(len(doc.chunks) for doc in library.documents)
        print(f"\n🔍 [SEARCH] Library: {library.name} (ID: {library_id})")
        print(f"   Index type: {library.index_type}")
        print(f"   Total chunks in library: {total_chunks}")
        print(f"   Total documents: {len(library.documents)}")
        print(f"   Search k: {search_query.k}, metric: {search_query.metric}")
        
        # Debug: print first few chunk IDs from library
        if total_chunks > 0:
            chunk_ids = []
            for doc in library.documents:
                for chunk in doc.chunks:
                    chunk_ids.append(str(chunk.id))
            print(f"   📋 Chunk IDs in library (first 5): {chunk_ids[:5]}")
        
        query_vector = np.array(search_query.embedding)
        results = self.repository.search_library(
            library_id, 
            query_vector, 
            search_query.k, 
            search_query.metric
        )
        
        print(f"   📊 Raw results from index: {len(results)} results")
        if results:
            print(f"   🎯 Results: {[(r[0][:8], round(r[1], 4)) for r in results[:3]]}")
        
        search_results = []
        for chunk_id_str, distance in results:
            chunk_id = UUID(chunk_id_str)
            chunk = self.repository.get_chunk(library_id, chunk_id)
            
            if not chunk:
                print(f"   ⚠️ [SEARCH] Chunk {chunk_id_str[:8]} from index not found in library!")
                continue
            
            if search_query.filters and not self._matches_filters(chunk, search_query.filters):
                print(f"   🚫 [SEARCH] Chunk {chunk_id_str[:8]} filtered out by metadata")
                continue
            
            if search_query.metric == "cosine":
                similarity = 1.0 - distance
            else:
                similarity = 1.0 / (1.0 + distance)
            
            search_results.append(SearchResult(
                chunk=chunk,
                score=similarity,
                distance=distance
            ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        final_results = search_results[:search_query.k]
        print(f"   ✅ [SEARCH] Returning {len(final_results)} results after filtering")
        return final_results
    
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
