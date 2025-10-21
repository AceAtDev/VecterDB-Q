"""Index repository for managing vector indexes and search operations."""
from typing import Dict, Optional, List, Tuple
from uuid import UUID
import numpy as np

from app.core.locks import RWLock
from app.core.indexes import VectorIndex, FlatIndex, IVFIndex


class IndexRepository:
    """Repository for vector index management and search operations.
    
    Responsibilities:
    - Create and manage vector indexes for libraries
    - Perform vector search operations
    - Maintain index-to-library mappings
    - Ensure thread-safe concurrent access
    - Single Responsibility: Vector index operations only
    
    Note: Indexes are NOT persisted to disk - they are rebuilt on load.
    This is because index structures are complex and better rebuilt from source data.
    """
    
    def __init__(self) -> None:
        """Initialize index repository."""
        self._indexes: Dict[UUID, VectorIndex] = {}
        self._lock = RWLock()
        
        print(f"[INDEX_REPO] 🚀 Initialized IndexRepository")
    
    def create_index(self, library_id: UUID, index_type: str = "flat") -> VectorIndex:
        """Create a vector index for a library.
        
        Args:
            library_id: UUID of the library to create index for
            index_type: Type of index ("flat" or "ivf")
            
        Returns:
            Created VectorIndex instance
            
        Raises:
            ValueError: If library already has an index
        """
        with self._lock.write_lock():
            if library_id in self._indexes:
                raise ValueError(f"Index for library {library_id} already exists")
            
            if index_type == "flat":
                index = FlatIndex()
                print(f"[INDEX_REPO] ✅ Created FlatIndex for library {library_id}")
            elif index_type == "ivf":
                index = IVFIndex(n_clusters=100, n_probe=10)
                print(f"[INDEX_REPO] ✅ Created IVFIndex for library {library_id}")
            else:
                # Default to flat
                index = FlatIndex()
                print(f"[INDEX_REPO] ✅ Created FlatIndex (default) for library {library_id}")
            
            self._indexes[library_id] = index
            return index
    
    def get_index(self, library_id: UUID) -> Optional[VectorIndex]:
        """Get the vector index for a library.
        
        Args:
            library_id: UUID of the library
            
        Returns:
            VectorIndex if found, None otherwise
        """
        with self._lock.read_lock():
            return self._indexes.get(library_id)
    
    def delete_index(self, library_id: UUID) -> bool:
        """Delete the vector index for a library.
        
        Args:
            library_id: UUID of the library
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock.write_lock():
            if library_id not in self._indexes:
                return False
            
            del self._indexes[library_id]
            print(f"[INDEX_REPO] 🗑️ Deleted index for library {library_id}")
            return True
    
    def add_vector(self, library_id: UUID, chunk_id: str, embedding: List[float]) -> None:
        """Add a vector to a library's index.
        
        Args:
            library_id: UUID of the library
            chunk_id: String ID of the chunk
            embedding: Vector embedding as list of floats
            
        Raises:
            ValueError: If index not found for library
        """
        with self._lock.write_lock():
            index = self._indexes.get(library_id)
            if index is None:
                raise ValueError(f"No index found for library {library_id}")
            
            vector = np.array(embedding)
            index.add(np.array([vector]), [chunk_id])
            print(f"[INDEX_REPO] ➕ Added vector for chunk {chunk_id[:8]}... to library {library_id}")
    
    def update_vector(self, library_id: UUID, chunk_id: str, embedding: List[float]) -> None:
        """Update a vector in a library's index.
        
        Args:
            library_id: UUID of the library
            chunk_id: String ID of the chunk
            embedding: Updated vector embedding as list of floats
            
        Raises:
            ValueError: If index not found for library
        """
        with self._lock.write_lock():
            index = self._indexes.get(library_id)
            if index is None:
                raise ValueError(f"No index found for library {library_id}")
            
            vector = np.array(embedding)
            index.update(chunk_id, vector)
            print(f"[INDEX_REPO] 📝 Updated vector for chunk {chunk_id[:8]}... in library {library_id}")
    
    def remove_vector(self, library_id: UUID, chunk_id: str) -> None:
        """Remove a vector from a library's index.
        
        Args:
            library_id: UUID of the library
            chunk_id: String ID of the chunk to remove
            
        Raises:
            ValueError: If index not found for library
        """
        with self._lock.write_lock():
            index = self._indexes.get(library_id)
            if index is None:
                raise ValueError(f"No index found for library {library_id}")
            
            index.remove(chunk_id)
            print(f"[INDEX_REPO] ➖ Removed vector for chunk {chunk_id[:8]}... from library {library_id}")
    
    def search_library(
        self, 
        library_id: UUID, 
        query_vector: np.ndarray, 
        k: int, 
        metric: str = "euclidean"
    ) -> List[Tuple[str, float]]:
        """Perform k-NN search in a library's index.
        
        Args:
            library_id: UUID of the library to search
            query_vector: Query vector as numpy array
            k: Number of nearest neighbors to return
            metric: Distance metric ("euclidean" or "cosine")
            
        Returns:
            List of (chunk_id, distance) tuples sorted by distance
            
        Raises:
            ValueError: If index not found for library
        """
        with self._lock.read_lock():
            index = self._indexes.get(library_id)
            if index is None:
                print(f"[INDEX_REPO] ❌ No index found for library {library_id}")
                return []
            
            print(f"[INDEX_REPO] 🔍 Searching library {library_id}: {type(index).__name__}, {len(index)} vectors")
            results = index.search(query_vector, k, metric)
            print(f"[INDEX_REPO] 📊 Found {len(results)} results")
            return results
    
    def rebuild_index(self, library_id: UUID, vectors: np.ndarray, chunk_ids: List[str]) -> None:
        """Rebuild an index with all vectors for a library.
        
        Useful after loading from disk or changing index type.
        
        Args:
            library_id: UUID of the library
            vectors: 2D numpy array of shape (n_vectors, dimension)
            chunk_ids: List of chunk ID strings matching vectors
            
        Raises:
            ValueError: If index not found or vectors/ids mismatch
        """
        with self._lock.write_lock():
            index = self._indexes.get(library_id)
            if index is None:
                raise ValueError(f"No index found for library {library_id}")
            
            if len(vectors) != len(chunk_ids):
                raise ValueError(f"Vectors and chunk_ids length mismatch: {len(vectors)} vs {len(chunk_ids)}")
            
            # Clear existing index
            index.clear()
            
            # Add all vectors
            if len(vectors) > 0:
                index.add(vectors, chunk_ids)
            
            print(f"[INDEX_REPO] 🔨 Rebuilt index for library {library_id}: {len(vectors)} vectors")
    
    def get_index_stats(self, library_id: UUID) -> Dict[str, any]:
        """Get statistics about a library's index.
        
        Args:
            library_id: UUID of the library
            
        Returns:
            Dictionary with index stats (type, size, etc.)
        """
        with self._lock.read_lock():
            index = self._indexes.get(library_id)
            if index is None:
                return {"error": "Index not found"}
            
            return {
                "type": type(index).__name__,
                "size": len(index),
                "library_id": str(library_id)
            }
