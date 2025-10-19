"""Inverted File (IVF) index implementation."""
from typing import List, Tuple, Dict
import numpy as np
from app.core.indexes.base import VectorIndex


class IVFIndex(VectorIndex):
    """
    Inverted File (IVF) index using k-means clustering.
    
    Characteristics:
    - Time Complexity: O(k*d + m*d) for search, O(d*log(n)) for insert
    - Space Complexity: O(n*d + k*d) where k is number of clusters
    - Accuracy: 95-98% (approximate)
    
    Algorithm:
    1. Cluster vectors using k-means
    2. Store vectors in inverted lists by cluster
    3. Search: Find nearest clusters, search within those clusters
    
    Use Case:
    - Medium to large datasets (10k-1M vectors)
    - When slight accuracy loss is acceptable for speed
    - Memory-constrained environments
    
    Trade-offs:
    - Pros: Much faster than flat index, reasonable memory usage
    - Cons: Requires training, approximate results, cluster maintenance
    """
    
    def __init__(self, n_clusters: int = 100, n_probe: int = 10) -> None:
        """
        Initialize IVF index.
        
        Args:
            n_clusters: Number of clusters (cells) to create
            n_probe: Number of clusters to search during query
        """
        self.n_clusters = n_clusters
        self.n_probe = n_probe
        
        self._vectors: Dict[str, np.ndarray] = {}
        self._ids: List[str] = []
        self._centroids: np.ndarray = np.array([])
        self._inverted_lists: Dict[int, List[str]] = {}
        self._is_trained = False
    
    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        Add vectors to the index.
        
        Time Complexity: O(n*k*d) for assignment to clusters
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")
        
        # Store vectors
        for vector, id in zip(vectors, ids):
            self._vectors[id] = vector
            if id not in self._ids:
                self._ids.append(id)
        
        # Train if not trained and have enough vectors
        if not self._is_trained and len(self._vectors) >= self.n_clusters:
            self._train()
        
        # Assign to clusters if trained
        if self._is_trained:
            for vector, id in zip(vectors, ids):
                cluster_id = self._assign_to_cluster(vector)
                if cluster_id not in self._inverted_lists:
                    self._inverted_lists[cluster_id] = []
                if id not in self._inverted_lists[cluster_id]:
                    self._inverted_lists[cluster_id].append(id)
    
    def search(self, query: np.ndarray, k: int, metric: str = "euclidean") -> List[Tuple[str, float]]:
        print(f"[IVF DEBUG] search called: len(_vectors)={len(self._vectors)}, is_trained={self._is_trained}, k={k}")
        
        if len(self._vectors) == 0:
            print("[IVF DEBUG] No vectors, returning empty")
            return []
        
        k = min(k, len(self._vectors))
        
        # If not trained (few vectors), fall back to brute force search
        if not self._is_trained:
            print(f"[IVF DEBUG] Not trained, using brute force on {len(self._vectors)} vectors")
            try:
                candidates = []
                for id, vector in self._vectors.items():
                    try:
                        if metric == "cosine":
                            similarity = self.cosine_similarity(query, vector)
                            distance = 1.0 - similarity
                        else:
                            distance = self.euclidean_distance(query, vector)
                        candidates.append((id, float(distance)))
                        print(f"[IVF DEBUG] Added candidate: id={id[:8]}, distance={distance}")
                    except Exception as e:
                        print(f"[IVF ERROR] Failed to calculate distance for {id[:8]}: {e}")
                        continue
                
                candidates.sort(key=lambda x: x[1])
                print(f"[IVF DEBUG] Returning {len(candidates[:k])} results")
                return candidates[:k]
            except Exception as e:
                print(f"[IVF ERROR] Brute force search failed: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Trained: use cluster-based search
        nearest_clusters = self._find_nearest_clusters(query, self.n_probe)
        
        candidates = []
        for cluster_id in nearest_clusters:
            if cluster_id in self._inverted_lists:
                for id in self._inverted_lists[cluster_id]:
                    vector = self._vectors[id]
                    if metric == "cosine":
                        similarity = self.cosine_similarity(query, vector)
                        distance = 1.0 - similarity
                    else:
                        distance = self.euclidean_distance(query, vector)
                    candidates.append((id, distance))
        
        candidates.sort(key=lambda x: x[1])
        return candidates[:k]
    
    def remove(self, id: str) -> bool:
        """Remove a vector from the index."""
        if id not in self._vectors:
            return False
        
        del self._vectors[id]
        self._ids.remove(id)
        
        # Remove from inverted lists
        for cluster_id, vector_ids in self._inverted_lists.items():
            if id in vector_ids:
                vector_ids.remove(id)
        
        return True
    
    def update(self, id: str, vector: np.ndarray) -> bool:
        """Update a vector in the index."""
        if id not in self._vectors:
            return False
        
        # Remove from old cluster
        self.remove(id)
        
        # Add to new cluster
        self._vectors[id] = vector
        self._ids.append(id)
        
        if self._is_trained:
            cluster_id = self._assign_to_cluster(vector)
            if cluster_id not in self._inverted_lists:
                self._inverted_lists[cluster_id] = []
            self._inverted_lists[cluster_id].append(id)
        
        return True
    
    def clear(self) -> None:
        """Clear all vectors from the index."""
        self._vectors.clear()
        self._ids.clear()
        self._centroids = np.array([])
        self._inverted_lists.clear()
        self._is_trained = False
    
    def __len__(self) -> int:
        """Return the number of vectors in the index."""
        return len(self._vectors)
    
    def _train(self) -> None:
        """
        Train the index using k-means clustering.
        
        Time Complexity: O(n*k*d*iterations) where iterations ≈ 10-20
        """
        if len(self._vectors) < self.n_clusters:
            return
        
        # Convert to matrix
        vectors_matrix = np.array([self._vectors[id] for id in self._ids])
        
        # K-means clustering
        self._centroids = self._kmeans(vectors_matrix, self.n_clusters)
        self._is_trained = True
        
        # Build inverted lists
        self._inverted_lists.clear()
        for id in self._ids:
            vector = self._vectors[id]
            cluster_id = self._assign_to_cluster(vector)
            if cluster_id not in self._inverted_lists:
                self._inverted_lists[cluster_id] = []
            self._inverted_lists[cluster_id].append(id)
    
    def _kmeans(self, vectors: np.ndarray, k: int, max_iterations: int = 20) -> np.ndarray:
        """
        Simple k-means clustering implementation.
        
        Args:
            vectors: Matrix of vectors (n, d)
            k: Number of clusters
            max_iterations: Maximum iterations
            
        Returns:
            Centroids matrix (k, d)
        """
        n, d = vectors.shape
        
        # Initialize centroids randomly
        indices = np.random.choice(n, k, replace=False)
        centroids = vectors[indices].copy()
        
        for _ in range(max_iterations):
            # Assign vectors to nearest centroid
            assignments = np.zeros(n, dtype=int)
            for i, vector in enumerate(vectors):
                distances = [self.euclidean_distance(vector, centroid) for centroid in centroids]
                assignments[i] = int(np.argmin(distances))
            
            # Update centroids
            new_centroids = np.zeros_like(centroids)
            for cluster_id in range(k):
                cluster_vectors = vectors[assignments == cluster_id]
                if len(cluster_vectors) > 0:
                    new_centroids[cluster_id] = cluster_vectors.mean(axis=0)
                else:
                    new_centroids[cluster_id] = centroids[cluster_id]
            
            # Check convergence
            if np.allclose(centroids, new_centroids):
                break
            
            centroids = new_centroids
        
        return centroids
    
    def _assign_to_cluster(self, vector: np.ndarray) -> int:
        """Assign a vector to the nearest cluster."""
        distances = [self.euclidean_distance(vector, centroid) for centroid in self._centroids]
        return int(np.argmin(distances))
    
    def _find_nearest_clusters(self, query: np.ndarray, n_probe: int) -> List[int]:
        """Find the n_probe nearest clusters to the query."""
        distances = [(i, self.euclidean_distance(query, centroid)) 
                    for i, centroid in enumerate(self._centroids)]
        distances.sort(key=lambda x: x[1])
        return [cluster_id for cluster_id, _ in distances[:n_probe]]
