"""In-process concurrency: N Python threads calling SearchService.search directly (no HTTP), plus mixed
read/write threads hammering the RWLock-protected repositories. Checks for exceptions, deadlocks
(join timeout), and index/chunk-store consistency.

Usage: python benchmarks/bench_thread_concurrency.py --data /tmp/vdbq-data/agnews_minilm.npz --n 10000 --index flat
"""
import argparse, contextlib, io, sys, threading, time, random
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.repositories.library_repository import LibraryRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.index_repository import IndexRepository
from app.services.library_service import LibraryService
from app.services.chunk_service import ChunkService
from app.services.search_service import SearchService
from app.domain.models import LibraryCreate, ChunkCreate, ChunkUpdate, SearchQuery

class Null(io.TextIOBase):
    def write(self, s): return len(s)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--index", default="flat"); ap.add_argument("--levels", type=int, nargs="+", default=[1, 10, 100, 1000])
    ap.add_argument("--per-thread", type=int, default=0, help="searches per thread (default: total 1000/level)")
    a = ap.parse_args()
    d = np.load(a.data, allow_pickle=True); X, Q = d["X"][: a.n], d["Q"]
    sys.stdout = Null()
    lr, cr, ir = LibraryRepository(None), ChunkRepository(None), IndexRepository()
    ls = LibraryService(lr, ir, cr); cs = ChunkService(cr, ls, ir); ss = SearchService(ls, cr, ir)
    lib = ls.create_library(LibraryCreate(name="b", index_type=a.index)).id
    ids = [cs.create_chunk(lib, ChunkCreate(text="t", embedding=v.tolist())).id for v in X]
    queries = [SearchQuery(embedding=q.tolist(), k=10, metric="cosine") for q in Q]
    out = []
    for c in a.levels:
        per = a.per_thread or max(1, 1000 // c)
        errs, lat = [], []
        def worker(j):
            for i in range(per):
                t = time.perf_counter()
                try:
                    r = ss.search(lib, queries[(j * per + i) % len(queries)]); assert len(r) == 10
                except Exception as e: errs.append(repr(e))
                lat.append((time.perf_counter() - t) * 1000)
        ths = [threading.Thread(target=worker, args=(j,)) for j in range(c)]
        t0 = time.perf_counter(); [t.start() for t in ths]; [t.join(600) for t in ths]
        wall = time.perf_counter() - t0; hung = sum(t.is_alive() for t in ths)
        L = np.array(lat)
        out.append(f"[threads {a.index} n={a.n}] threads={c:5d} searches={len(L)} thrpt={len(L)/wall:.1f}/s p50={np.percentile(L,50):.0f}ms "
                   f"p99={np.percentile(L,99):.0f}ms errors={len(errs)} hung={hung}")
    # mixed read/write
    stop = time.perf_counter() + 20; errs = []; live = list(ids); lock = threading.Lock(); counts = {"r": 0, "w": 0}
    def reader(j):
        i = j
        while time.perf_counter() < stop:
            try: ss.search(lib, queries[i % len(queries)]); counts["r"] += 1
            except Exception as e: errs.append(repr(e))
            i += 1
    def writer(j):
        rng = random.Random(j)
        while time.perf_counter() < stop:
            op = rng.choice("cud")
            try:
                if op == "c":
                    ch = cs.create_chunk(lib, ChunkCreate(text="n", embedding=X[rng.randrange(len(X))].tolist()))
                    with lock: live.append(ch.id)
                elif op == "u":
                    with lock: cid = rng.choice(live)
                    cs.update_chunk(lib, cid, ChunkUpdate(embedding=X[rng.randrange(len(X))].tolist()))
                else:
                    with lock: cid = live.pop(rng.randrange(len(live)))
                    cs.delete_chunk(lib, cid)
                counts["w"] += 1
            except Exception as e: errs.append(repr(e))
    ths = [threading.Thread(target=reader, args=(j,)) for j in range(200)] + [threading.Thread(target=writer, args=(j,)) for j in range(20)]
    [t.start() for t in ths]; [t.join(120) for t in ths]
    hung = sum(t.is_alive() for t in ths)
    idx = ir.get_index(lib); store = len(cs.list_chunks(lib))
    docs = sum(len(dd.chunks) for dd in cr.get_documents_for_library(lib))
    out.append(f"[mixed 200 readers + 20 writers, 20 s] reads={counts['r']} writes={counts['w']} errors={len(errs)} {errs[:3]} hung={hung} "
               f"index_size={len(idx)} chunk_store={store} documents_chunks={docs} client_live={len(live)}")
    sys.stdout = sys.__stdout__
    print("\n".join(out))

if __name__ == "__main__":
    main()
