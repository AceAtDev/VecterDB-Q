"""Tests for vector indexes."""
import pytest
import numpy as np
from app.core.indexes import FlatIndex, IVFIndex


class TestFlatIndex:
    """Test suite for FlatIndex."""
    
    def test_add_and_search(self):
        """Test adding vectors and searching."""
        index = FlatIndex()
        
        # Create test vectors
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        ids = ["vec1", "vec2", "vec3"]
        
        # Add vectors
        index.add(vectors, ids)
        
        assert len(index) == 3
        
        # Search for nearest to [1.1, 0.1, 0.0]
        query = np.array([1.1, 0.1, 0.0])
        results = index.search(query, k=2)
        
        assert len(results) == 2
        assert results[0][0] == "vec1"  # Should be closest
    
    def test_remove(self):
        """Test removing a vector."""
        index = FlatIndex()
        vectors = np.array([[1.0, 0.0]])
        index.add(vectors, ["vec1"])
        
        assert len(index) == 1
        
        success = index.remove("vec1")
        assert success
        assert len(index) == 0
    
    def test_update(self):
        """Test updating a vector."""
        index = FlatIndex()
        vectors = np.array([[1.0, 0.0]])
        index.add(vectors, ["vec1"])
        
        new_vector = np.array([0.0, 1.0])
        success = index.update("vec1", new_vector)
        assert success
        
        # Search should reflect the update
        results = index.search(np.array([0.0, 1.0]), k=1)
        assert results[0][0] == "vec1"
        assert results[0][1] < 0.1  # Very close


class TestIVFIndex:
    """Test suite for IVFIndex."""
    
    def test_add_and_search(self):
        """Test adding vectors and searching with IVF."""
        index = IVFIndex(n_clusters=2, n_probe=1)
        
        # Create enough vectors to train
        np.random.seed(42)
        n_vectors = 100
        dim = 10
        vectors = np.random.randn(n_vectors, dim).astype(np.float32)
        ids = [f"vec{i}" for i in range(n_vectors)]
        
        # Add vectors
        index.add(vectors, ids)
        
        assert len(index) == n_vectors
        
        # Search
        query = vectors[0]  # Search for first vector
        results = index.search(query, k=5)
        
        assert len(results) > 0
        # First result should be the vector itself
        assert results[0][0] == "vec0"
    
    def test_clustering(self):
        """Test that IVF creates clusters."""
        index = IVFIndex(n_clusters=3, n_probe=2)
        
        # Create vectors in distinct clusters
        vectors = np.array([
            [10.0, 0.0],
            [10.1, 0.1],
            [0.0, 10.0],
            [0.1, 10.1],
            [-10.0, 0.0],
            [-10.1, 0.1],
        ])
        ids = [f"vec{i}" for i in range(6)]
        
        index.add(vectors, ids)
        
        # Should be trained
        assert index._is_trained
        assert len(index._centroids) == 3
