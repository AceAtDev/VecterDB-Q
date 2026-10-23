"""Tests for IVFIndex: retraining, determinism, filtering and dimension checks."""
import numpy as np
import pytest

from app.core.indexes import FlatIndex, IVFIndex


def make_drifting_data(n=1500, d=16, n_centers=30, seed=0):
    """Clustered vectors ordered by cluster, so early inserts cover only a few clusters.

    This is the worst case for an index that trains once on its first vectors.
    """
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(n_centers, d))  # overlapping clusters, like real embeddings
    labels = np.sort(rng.integers(0, n_centers, size=n))
    X = centers[labels] + rng.normal(size=(n, d))
    Q = centers[rng.integers(0, n_centers, size=40)] + rng.normal(size=(40, d))
    return X, Q


def recall_at_k(index, exact, Q, k=10):
    hits = []
    for q, truth in zip(Q, exact):
        got = {i for i, _ in index.search(q, k)}
        hits.append(len(got & set(truth)) / k)
    return float(np.mean(hits))


class TestIVFRetraining:
    """An index filled one vector at a time should match a bulk-built index."""

    def test_incremental_recall_close_to_bulk(self):
        X, Q = make_drifting_data()
        ids = [str(i) for i in range(len(X))]

        flat = FlatIndex()
        flat.add(X, ids)
        exact = [[i for i, _ in flat.search(q, 10)] for q in Q]

        bulk = IVFIndex(n_clusters=20, n_probe=3)
        bulk.add(X, ids)

        incremental = IVFIndex(n_clusters=20, n_probe=3)
        for vector, id in zip(X, ids):
            incremental.add(np.array([vector]), [id])

        # Old behaviour (train once on the first 20 vectors) for comparison
        train_once = IVFIndex(n_clusters=20, n_probe=3, retrain_growth=0)
        for vector, id in zip(X, ids):
            train_once.add(np.array([vector]), [id])

        bulk_recall = recall_at_k(bulk, exact, Q)
        incremental_recall = recall_at_k(incremental, exact, Q)
        train_once_recall = recall_at_k(train_once, exact, Q)

        assert incremental_recall >= bulk_recall - 0.05
        assert incremental_recall > train_once_recall + 0.05

    def test_retrains_when_index_doubles(self):
        X, _ = make_drifting_data(n=400)
        index = IVFIndex(n_clusters=10, n_probe=2)
        sizes = []
        for i, vector in enumerate(X):
            index.add(np.array([vector]), [str(i)])
            sizes.append(index._trained_size)

        assert sizes[8] == 0          # 9 vectors: not trained yet
        assert sizes[9] == 10         # first training at n_clusters
        assert set(sizes) == {0, 10, 20, 40, 80, 160, 320}
        # Every vector is in exactly one inverted list
        listed = [id for ids in index._inverted_lists.values() for id in ids]
        assert sorted(listed) == sorted(str(i) for i in range(len(X)))


class TestIVFDeterminism:
    """k-means is seeded, so the same data gives the same index."""

    def test_same_seed_same_centroids_and_results(self):
        X, Q = make_drifting_data(n=600)
        ids = [str(i) for i in range(len(X))]

        a = IVFIndex(n_clusters=15, n_probe=2)
        b = IVFIndex(n_clusters=15, n_probe=2)
        a.add(X, ids)
        b.add(X, ids)

        assert np.array_equal(a._centroids, b._centroids)
        for q in Q:
            assert a.search(q, 10) == b.search(q, 10)

    def test_global_numpy_random_state_does_not_matter(self):
        X, _ = make_drifting_data(n=600)
        ids = [str(i) for i in range(len(X))]

        np.random.seed(1)
        a = IVFIndex(n_clusters=15)
        a.add(X, ids)
        np.random.seed(2)
        b = IVFIndex(n_clusters=15)
        b.add(X, ids)

        assert np.array_equal(a._centroids, b._centroids)

    def test_different_seed_changes_initialization(self):
        X, _ = make_drifting_data(n=600)
        ids = [str(i) for i in range(len(X))]

        a = IVFIndex(n_clusters=15, seed=0)
        b = IVFIndex(n_clusters=15, seed=1)
        a.add(X, ids)
        b.add(X, ids)

        assert not np.array_equal(a._centroids, b._centroids)


class TestIVFMaintenance:
    """Remove, update and re-add keep the inverted lists consistent."""

    def test_remove_update_and_readd(self):
        X, _ = make_drifting_data(n=200)
        ids = [str(i) for i in range(len(X))]
        index = IVFIndex(n_clusters=10, n_probe=10)
        index.add(X, ids)

        assert index.remove("0")
        assert not index.remove("0")
        assert index.update("1", X[150])
        index.add(np.array([X[5]]), ["2"])  # re-add existing id replaces it

        listed = [id for lst in index._inverted_lists.values() for id in lst]
        assert len(listed) == len(set(listed)) == len(index) == 199
        assert "0" not in listed

    def test_filtered_search_probes_more_clusters_until_k(self):
        X, Q = make_drifting_data(n=600)
        ids = [str(i) for i in range(len(X))]
        index = IVFIndex(n_clusters=20, n_probe=1)
        index.add(X, ids)

        # Allowed vectors are spread over many clusters, most far from the query
        allowed = {str(i) for i in range(0, 600, 37)}
        results = index.search(Q[0], 10, allowed_ids=allowed)

        assert len(results) == 10
        assert all(id in allowed for id, _ in results)


class TestDimensionChecks:
    """Wrong-dimension vectors are rejected before anything is stored."""

    @pytest.mark.parametrize("index_cls", [FlatIndex, IVFIndex])
    def test_add_rejects_wrong_dimension_atomically(self, index_cls):
        index = index_cls()
        index.add(np.ones((3, 4)), ["a", "b", "c"])

        with pytest.raises(ValueError):
            index.add(np.array([np.ones(4), np.ones(3)], dtype=object), ["d", "e"])

        assert len(index) == 3
        assert index.dimension == 4

    @pytest.mark.parametrize("index_cls", [FlatIndex, IVFIndex])
    def test_update_rejects_wrong_dimension(self, index_cls):
        index = index_cls()
        index.add(np.ones((2, 4)), ["a", "b"])

        with pytest.raises(ValueError):
            index.update("a", np.ones(5))
        assert index.search(np.ones(4), 2)  # still searchable
