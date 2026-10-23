"""Flat (brute-force) vector index implementation."""
from typing import List, Tuple, Dict, Optional, Set
import numpy as np
from app.core.indexes.base import VectorIndex


class FlatIndex(VectorIndex):
    """Flat index using brute-force search. Best for small datasets (<10k). 100% accuracy."""
    
    def __init__(self) -> None:
        self._vectors: Dict[str, np.ndarray] = {}
        self._ids: List[str] = []
    
    @property
    def dimension(self) -> Optional[int]:
        """Dimension of the stored vectors, or None if the index is empty."""
        if not self._vectors:
            return None
        return int(next(iter(self._vectors.values())).shape[0])
    
    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")
        self._check_dimensions(vectors)
        
        for vector, id in zip(vectors, ids):
            # Dict lookup instead of list membership keeps inserts O(1)
            if id not in self._vectors:
                self._ids.append(id)
            self._vectors[id] = vector
    
    def search(
        self,
        query: np.ndarray,
        k: int,
        metric: str = "euclidean",
        allowed_ids: Optional[Set[str]] = None
    ) -> List[Tuple[str, float]]:
        if len(self._vectors) == 0:
            return []
        
        ids = self._ids
        if allowed_ids is not None:
            # Filter before ranking so a filtered search still returns up to k matches
            ids = [id for id in self._ids if id in allowed_ids]
        
        k = min(k, len(ids))
        
        distances = []
        for id in ids:
            vector = self._vectors[id]
            if metric == "cosine":
                similarity = self.cosine_similarity(query, vector)
                distance = 1.0 - similarity
            else:
                distance = self.euclidean_distance(query, vector)
            distances.append((id, distance))
        
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def remove(self, id: str) -> bool:
        if id not in self._vectors:
            return False
        
        del self._vectors[id]
        self._ids.remove(id)
        return True
    
    def update(self, id: str, vector: np.ndarray) -> bool:
        if id not in self._vectors:
            return False
        self.check_dimension(vector)

        self._vectors[id] = vector
        return True
    
    def clear(self) -> None:
        self._vectors.clear()
        self._ids.clear()
    
    def __len__(self) -> int:
        return len(self._vectors)
