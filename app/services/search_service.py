"""Search service containing business logic for vector search operations."""
from typing import List, Dict, Any
from uuid import UUID
import numpy as np

from app.domain.models import SearchQuery, SearchResult, Chunk


class SearchService:
    """Service layer for vector search operations.
    
    Handles all business logic related to k-NN search with metadata filtering.
    Follows Single Responsibility Principle - only manages search operations.
    """
    
    def __init__(self, library_service, chunk_repository, index_repository) -> None:
        """Initialize search service with dependencies.
        
        Args:
            library_service: LibraryService for library validation
            chunk_repository: ChunkRepository for fetching chunk data
            index_repository: IndexRepository for vector search operations
        """
        self.library_service = library_service
        self.chunk_repository = chunk_repository
        self.index_repository = index_repository
    
    def search(self, library_id: UUID, search_query: SearchQuery) -> List[SearchResult]:
        """Perform k-NN search with optional metadata filtering.
        
        Args:
            library_id: UUID of the library to search in
            search_query: Search request with query vector, k, metric, and filters
            
        Returns:
            List of SearchResult objects sorted by relevance score
        """
        # Validate library exists
        library = self.library_service.get_library(library_id)
        if not library:
            print(f"❌ [SEARCH] Library {library_id} not found")
            return []
        
        # Get documents from chunk repository to count chunks
        documents = self.chunk_repository.get_documents_for_library(library_id)
        total_chunks = sum(len(doc.chunks) for doc in documents)
        
        # Log search details
        print(f"\n🔍 [SEARCH] Library: {library.name} (ID: {library_id})")
        print(f"   Index type: {library.index_type}")
        print(f"   Total chunks in library: {total_chunks}")
        print(f"   Total documents: {len(documents)}")
        print(f"   Search k: {search_query.k}, metric: {search_query.metric}")
        
        # Debug: print first few chunk IDs from library
        if total_chunks > 0:
            chunk_ids = []
            for doc in documents:
                for chunk in doc.chunks:
                    chunk_ids.append(str(chunk.id))
            print(f"   📋 Chunk IDs in library (first 5): {chunk_ids[:5]}")
        
        # Perform vector search using index
        query_vector = np.array(search_query.embedding)
        results = self.index_repository.search_library(
            library_id, 
            query_vector, 
            search_query.k, 
            search_query.metric
        )
        
        print(f"   📊 Raw results from index: {len(results)} results")
        if results:
            print(f"   🎯 Results: {[(r[0][:8], round(r[1], 4)) for r in results[:3]]}")
        
        # Convert index results to SearchResult objects with metadata filtering
        search_results = []
        for chunk_id_str, distance in results:
            chunk_id = UUID(chunk_id_str)
            chunk = self.chunk_repository.get_chunk(library_id, chunk_id)
            
            if not chunk:
                print(f"   ⚠️ [SEARCH] Chunk {chunk_id_str[:8]} from index not found in library!")
                continue
            
            # Apply metadata filters if provided
            if search_query.filters and not self._matches_filters(chunk, search_query.filters):
                print(f"   🚫 [SEARCH] Chunk {chunk_id_str[:8]} filtered out by metadata")
                continue
            
            # Convert distance to similarity score
            if search_query.metric == "cosine":
                similarity = 1.0 - distance
            else:  # euclidean
                similarity = 1.0 / (1.0 + distance)
            
            search_results.append(SearchResult(
                chunk=chunk,
                score=similarity,
                distance=distance
            ))
        
        # Sort by score and limit to k results
        search_results.sort(key=lambda x: x.score, reverse=True)
        final_results = search_results[:search_query.k]
        print(f"   ✅ [SEARCH] Returning {len(final_results)} results after filtering")
        return final_results
    
    @staticmethod
    def _matches_filters(chunk: Chunk, filters: Dict[str, Any]) -> bool:
        """Check if chunk matches metadata filters.
        
        Supports nested keys with dot notation (e.g., "author.name").
        
        Args:
            chunk: Chunk object to check
            filters: Dictionary of metadata filters to apply
            
        Returns:
            True if chunk matches all filters, False otherwise
            
        Examples:
            >>> filters = {"category": "science", "author.name": "John"}
            >>> _matches_filters(chunk, filters)
            True
        """
        metadata_dict = chunk.metadata.model_dump()
        
        for key, value in filters.items():
            # Support dot notation for nested keys
            keys = key.split('.')
            current = metadata_dict
            
            try:
                for k in keys:
                    current = current[k]
            except (KeyError, TypeError):
                return False
            
            # String comparison (case-insensitive substring match)
            if isinstance(value, str) and isinstance(current, str):
                if value.lower() not in current.lower():
                    return False
            # List comparison (value must be in list)
            elif isinstance(value, list):
                if current not in value:
                    return False
            # Exact match for other types
            else:
                if current != value:
                    return False
        
        return True
