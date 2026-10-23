"""Tests for FlatIndex."""
import numpy as np

from app.core.indexes import FlatIndex


class TestFlatIndex:

    def test_exact_order_and_k(self):
        index = FlatIndex()
        index.add(np.array([[0.0], [3.0], [1.0], [2.0]]), ["a", "d", "b", "c"])

        assert [id for id, _ in index.search(np.array([0.0]), 3)] == ["a", "b", "c"]

    def test_readd_does_not_duplicate(self):
        index = FlatIndex()
        index.add(np.array([[0.0], [1.0]]), ["a", "b"])
        index.add(np.array([[5.0]]), ["a"])

        assert len(index) == 2
        assert len(index._ids) == 2
        assert index.search(np.array([5.0]), 1)[0][0] == "a"

    def test_allowed_ids_filters_before_top_k(self):
        index = FlatIndex()
        vectors = np.arange(20, dtype=float).reshape(-1, 1)
        index.add(vectors, [str(i) for i in range(20)])

        # The allowed ids are the farthest from the query; all of them still come back
        allowed = {"15", "16", "17", "18", "19"}
        results = index.search(np.array([0.0]), 5, allowed_ids=allowed)

        assert [id for id, _ in results] == ["15", "16", "17", "18", "19"]
