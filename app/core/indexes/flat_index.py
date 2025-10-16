"""Flat (brute-force) vector index implementation."""
from typing import List, Tuple, Dict
import numpy as np
from app.core.indexes.base import VectorIndex


class FlatIndex(VectorIndex):
    """Flat index using brute-force search. Best for small datasets (<10k). 100% accuracy."""
    
    def __init__(self) -> None:
        self._vectors: Dict[str, np.ndarray] = {}
        self._ids: List[str] = []
        self._vector_matrix: np.ndarray = np.array([])
    
    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")
        
        for vector, id in zip(vectors, ids):
            self._vectors[id] = vector
            if id not in self._ids:
                self._ids.append(id)
        
        self._rebuild_matrix()
    
    def search(self, query: np.ndarray, k: int, metric: str = "euclidean") -> List[Tuple[str, float]]:
        if len(self._vectors) == 0:
            return []
        
        k = min(k, len(self._vectors))
        
        distances = []
        for id in self._ids:
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
        self._rebuild_matrix()
        return True
    
    def update(self, id: str, vector: np.ndarray) -> bool:
        if id not in self._vectors:
            return False
        
        self._vectors[id] = vector
        self._rebuild_matrix()
        return True
    
    def clear(self) -> None:
        self._vectors.clear()
        self._ids.clear()
        self._vector_matrix = np.array([])
    
    def __len__(self) -> int:
        return len(self._vectors)
    
    def _rebuild_matrix(self) -> None:
        if len(self._vectors) > 0:
            self._vector_matrix = np.array([self._vectors[id] for id in self._ids])
        else:
            self._vector_matrix = np.array([])
