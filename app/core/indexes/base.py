"""Base index interface."""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set
import numpy as np


class VectorIndex(ABC):
    """
    Abstract base class for vector indexes.
    
    All concrete index implementations must implement these methods.
    """
    
    @abstractmethod
    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Add vectors to the index.
        
        Args:
            vectors: Array of shape (n, d) where n is number of vectors
            ids: List of identifiers for the vectors
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: np.ndarray,
        k: int,
        metric: str = "euclidean",
        allowed_ids: Optional[Set[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for k nearest neighbors.
        
        Args:
            query: Query vector of shape (d,)
            k: Number of neighbors to return
            metric: Distance metric ("euclidean" or "cosine")
            allowed_ids: If given, only these IDs are considered (filtering
                happens before the top-k is chosen)
            
        Returns:
            List of (id, distance) tuples sorted by distance
        """
        pass
    
    @abstractmethod
    def remove(self, id: str) -> bool:
        """
        Remove a vector from the index.
        
        Args:
            id: Identifier of the vector to remove
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    @abstractmethod
    def update(self, id: str, vector: np.ndarray) -> bool:
        """
        Update a vector in the index.
        
        Args:
            id: Identifier of the vector to update
            vector: New vector values
            
        Returns:
            True if updated, False if not found
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors from the index."""
        pass
    
    @abstractmethod
    def __len__(self) -> int:
        """Return the number of vectors in the index."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> Optional[int]:
        """Return the dimension of stored vectors, or None if the index is empty."""
        pass
    
    def check_dimension(self, vector: np.ndarray) -> None:
        """
        Raise ValueError if a vector does not match the index dimension.
        
        An empty index accepts any dimension.
        """
        vector = np.asarray(vector)
        if vector.ndim != 1:
            raise ValueError(f"Expected a 1-D vector, got shape {vector.shape}")
        expected = self.dimension
        if expected is not None and vector.shape[0] != expected:
            raise ValueError(
                f"Embedding dimension {vector.shape[0]} does not match index dimension {expected}"
            )
    
    def _check_dimensions(self, vectors: np.ndarray) -> None:
        """Validate a batch of vectors against the index and each other before storing any."""
        expected = self.dimension
        for vector in vectors:
            vector = np.asarray(vector)
            if vector.ndim != 1:
                raise ValueError(f"Expected 1-D vectors, got shape {vector.shape}")
            if expected is None:
                expected = vector.shape[0]
            elif vector.shape[0] != expected:
                raise ValueError(
                    f"Embedding dimension {vector.shape[0]} does not match index dimension {expected}"
                )
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity in range [-1, 1]
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    @staticmethod
    def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Euclidean distance
        """
        return float(np.linalg.norm(a - b))
