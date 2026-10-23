"""Search service containing business logic for vector search operations."""
from typing import List, Dict, Any
from uuid import UUID
import logging
import numpy as np

from app.domain.models import SearchQuery, SearchResult, Chunk


logger = logging.getLogger(__name__)

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
            logger.debug("Search: library %s not found", library_id)
            return []
        
        # Apply metadata filters before the top-k is chosen: the index only
        # ranks chunks that match, so a filtered search still returns up to k
        allowed_ids = None
        if search_query.filters:
            allowed_ids = set()
            for document in self.chunk_repository.get_documents_for_library(library_id):
                for chunk in document.chunks:
                    if self._matches_filters(chunk, search_query.filters):
                        allowed_ids.add(str(chunk.id))
            if not allowed_ids:
                return []
        
        # Perform vector search using index
        query_vector = np.array(search_query.embedding)
        results = self.index_repository.search_library(
            library_id, 
            query_vector, 
            search_query.k, 
            search_query.metric,
            allowed_ids=allowed_ids
        )
        logger.debug("Search in library %s: %d raw results", library_id, len(results))
        
        # Convert index results to SearchResult objects
        search_results = []
        for chunk_id_str, distance in results:
            chunk_id = UUID(chunk_id_str)
            chunk = self.chunk_repository.get_chunk(library_id, chunk_id)
            
            if not chunk:
                logger.debug("Search: chunk %s from index not found in library", chunk_id_str)
                continue
            
            # Re-check filters: metadata may have changed since allowed_ids was built
            if search_query.filters and not self._matches_filters(chunk, search_query.filters):
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
        return search_results[:search_query.k]
    
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
