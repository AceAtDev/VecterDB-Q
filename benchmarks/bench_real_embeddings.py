"""Flat vs IVF on real sentence embeddings (AG News, all-MiniLM-L6-v2, 384-d, L2-normalized).

Usage: python benchmarks/bench_real_embeddings.py --data /tmp/vdbq-data/agnews_minilm.npz --sizes 5000 10000 20000
Reports build time, median/p90 latency, recall@10 vs Flat for:
  - IVF bulk build (one add() call -> k-means on all vectors; this is what app startup rebuild does)
  - IVF incremental (one add() per vector, as POST /chunks does -> k-means trains once on first 100 vectors)
Also a vectorized NumPy brute-force reference for context.
"""
import argparse, contextlib, io, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.indexes.flat_index import FlatIndex
from app.core.indexes.ivf_index import IVFIndex

def quiet():
    return contextlib.redirect_stdout(io.StringIO())

def timed_search(index, Q, k, metric):
    times, res = [], []
    for q in Q:
        t = time.perf_counter()
        with quiet():
            hits = index.search(q, k, metric)
        times.append((time.perf_counter() - t) * 1000)
        res.append([h[0] for h in hits])
    return np.median(times), np.percentile(times, 90), res

def recall(exact, approx, k):
    return float(np.mean([len(set(a) & set(b)) / k for a, b in zip(exact, approx)]))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--sizes", type=int, nargs="+", default=[5000, 10000, 20000])
    p.add_argument("--queries", type=int, default=50)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--metric", default="cosine")
    p.add_argument("--skip-incremental", action="store_true")
    a = p.parse_args()
    d = np.load(a.data, allow_pickle=True)
    Xall, Q = d["X"], d["Q"][: a.queries]
    np.random.seed(0)
    for n in a.sizes:
        X = Xall[:n]; ids = [str(i) for i in range(n)]
        # numpy reference
        t = time.perf_counter()
        for q in Q:
            s = X @ q; np.argpartition(-s, a.k)[: a.k]
        np_ms = (time.perf_counter() - t) * 1000 / len(Q)

        flat = FlatIndex(); t = time.perf_counter()
        with quiet(): flat.add(X, ids)
        fb = time.perf_counter() - t
        fm, fp, exact = timed_search(flat, Q, a.k, a.metric)
        print(f"n={n} numpy-ref {np_ms:.2f}ms | flat build {fb:.1f}s median {fm:.1f}ms p90 {fp:.1f}ms", flush=True)

        ivf = IVFIndex(); t = time.perf_counter()
        with quiet(): ivf.add(X, ids)
        ib = time.perf_counter() - t
        im, ip, approx = timed_search(ivf, Q, a.k, a.metric)
        sizes = [len(v) for v in ivf._inverted_lists.values()]
        print(f"n={n} ivf-bulk build {ib:.1f}s median {im:.1f}ms p90 {ip:.1f}ms recall@{a.k} {recall(exact, approx, a.k):.3f} "
              f"(clusters={len(sizes)}, max list={max(sizes)}, mean={np.mean(sizes):.0f})", flush=True)

        if not a.skip_incremental:
            inc = IVFIndex(); t = time.perf_counter()
            with quiet():
                for v, i in zip(X, ids): inc.add(np.array([v]), [i])
            ib2 = time.perf_counter() - t
            im2, ip2, approx2 = timed_search(inc, Q, a.k, a.metric)
            sizes2 = [len(v) for v in inc._inverted_lists.values()]
            print(f"n={n} ivf-incremental build {ib2:.1f}s median {im2:.1f}ms p90 {ip2:.1f}ms recall@{a.k} {recall(exact, approx2, a.k):.3f} "
                  f"(trained on first {inc.n_clusters} vectors only; max list={max(sizes2)}, mean={np.mean(sizes2):.0f})", flush=True)

if __name__ == "__main__":
    main()
