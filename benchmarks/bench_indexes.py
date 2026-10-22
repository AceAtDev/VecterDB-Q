"""Benchmark Flat vs IVF search latency and IVF recall on synthetic vectors.

Usage:
    python benchmarks/bench_indexes.py --n 10000
    python benchmarks/bench_indexes.py --n 100000 --data random

Prints build time, median/p90 search latency for each index, and IVF recall@k
measured against exact (Flat) search. No API keys or network access needed.
"""
import argparse
import contextlib
import io
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.indexes.flat_index import FlatIndex  # noqa: E402
from app.core.indexes.ivf_index import IVFIndex  # noqa: E402


def make_data(kind: str, n: int, d: int, queries: int, seed: int):
    rng = np.random.default_rng(seed)
    if kind == "clustered":
        centers = rng.standard_normal((200, d)) * 3
        X = centers[rng.integers(0, 200, n)] + rng.standard_normal((n, d))
        Q = centers[rng.integers(0, 200, queries)] + rng.standard_normal((queries, d))
    else:
        X = rng.standard_normal((n, d))
        Q = rng.standard_normal((queries, d))
    return X.astype(np.float32), Q.astype(np.float32)


def run(index, name, X, ids, Q, k):
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        index.add(X, ids)
    build = time.perf_counter() - start

    times, results = [], []
    for q in Q:
        start = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            hits = index.search(q, k)
        times.append((time.perf_counter() - start) * 1000)
        results.append({i for i, _ in hits})

    print(f"{name:5} n={len(ids):>9,} build={build:7.1f}s  "
          f"search median={np.median(times):7.1f}ms  p90={np.percentile(times, 90):7.1f}ms")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=10_000, help="number of vectors")
    parser.add_argument("--dim", type=int, default=384, help="vector dimension")
    parser.add_argument("--queries", type=int, default=20)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--data", choices=["clustered", "random"], default="clustered")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    X, Q = make_data(args.data, args.n, args.dim, args.queries, args.seed)
    ids = [str(i) for i in range(args.n)]

    exact = run(FlatIndex(), "flat", X, ids, Q, args.k)
    approx = run(IVFIndex(), "ivf", X, ids, Q, args.k)
    recall = np.mean([len(a & b) / args.k for a, b in zip(exact, approx)])
    print(f"IVF recall@{args.k} vs flat ({args.data} data): {recall:.3f}")


if __name__ == "__main__":
    main()
