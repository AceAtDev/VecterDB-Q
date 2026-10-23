"""HTTP concurrency load test against the real FastAPI app (uvicorn, 1 worker).

Usage:
  python benchmarks/bench_http_concurrency.py --data /tmp/vdbq-data/agnews_minilm.npz --n 1000 --index flat \
      --levels 10 100 1000 --requests 2000 [--mixed]
Starts uvicorn as a subprocess (PERSISTENCE_ENABLED=false, stdout discarded), seeds one library with N real
embeddings via POST /chunks, then fires searches with C requests in flight (aiohttp). Reports throughput,
latency percentiles, error counts. --mixed also runs searches concurrently with create/update/delete writers
and checks index/chunk-store consistency afterwards via /debug/indexes.
"""
import argparse, asyncio, os, random, subprocess, sys, time
from pathlib import Path
import aiohttp, numpy as np

ROOT = Path(__file__).resolve().parent.parent

async def wait_up(base):
    for _ in range(200):
        try:
            async with aiohttp.ClientSession() as s, s.get(base + "/health") as r:
                if r.status == 200: return
        except Exception: pass
        await asyncio.sleep(0.1)
    raise RuntimeError("server did not start")

async def seed(base, X, index, conc=32):
    conn = aiohttp.TCPConnector(limit=conc)
    async with aiohttp.ClientSession(connector=conn) as s:
        async with s.post(base + "/api/v1/libraries", json={"name": "bench", "index_type": index}) as r:
            lib = (await r.json())["id"]
        sem = asyncio.Semaphore(conc); ids = []
        async def one(i):
            async with sem:
                async with s.post(f"{base}/api/v1/libraries/{lib}/chunks",
                                  json={"text": f"t{i}", "embedding": X[i].tolist(), "metadata": {"source": "bench"}}) as r:
                    assert r.status == 201, (r.status, await r.text())
                    ids.append((await r.json())["id"])
        t = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(len(X))))
        return lib, ids, time.perf_counter() - t

async def load(base, lib, Q, conc, total, metric="cosine"):
    conn = aiohttp.TCPConnector(limit=0)
    timeout = aiohttp.ClientTimeout(total=600)
    lat, codes, errs = [], {}, []
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as s:
        sem = asyncio.Semaphore(conc)
        async def one(i):
            async with sem:
                t = time.perf_counter()
                try:
                    async with s.post(f"{base}/api/v1/libraries/{lib}/search",
                                      json={"embedding": Q[i % len(Q)].tolist(), "k": 10, "metric": metric}) as r:
                        body = await r.json()
                        codes[r.status] = codes.get(r.status, 0) + 1
                        if r.status == 200 and len(body) == 0: errs.append("empty")
                except Exception as e:
                    errs.append(type(e).__name__)
                lat.append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(total)))
        wall = time.perf_counter() - t
    lat = np.array(lat)
    return dict(conc=conc, total=total, wall=wall, rps=total / wall, p50=np.percentile(lat, 50),
                p90=np.percentile(lat, 90), p99=np.percentile(lat, 99), max=lat.max(), codes=codes,
                errors={e: errs.count(e) for e in set(errs)})

async def mixed(base, lib, ids, X, Q, readers, seconds):
    """Readers search continuously while 8 writers create/update/delete chunks."""
    stop = time.perf_counter() + seconds
    stats = {"search": {}, "create": {}, "update": {}, "delete": {}, "exc": []}
    live = list(ids); rng = random.Random(0)
    def bump(op, code): stats[op][code] = stats[op].get(code, 0) + 1
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0), timeout=aiohttp.ClientTimeout(total=600)) as s:
        async def reader(j):
            i = j
            while time.perf_counter() < stop:
                try:
                    async with s.post(f"{base}/api/v1/libraries/{lib}/search",
                                      json={"embedding": Q[i % len(Q)].tolist(), "k": 10, "metric": "cosine"}) as r:
                        await r.read(); bump("search", r.status)
                except Exception as e: stats["exc"].append(repr(e))
                i += 1
        async def writer(j):
            while time.perf_counter() < stop:
                op = rng.choice(["create", "update", "delete"])
                try:
                    if op == "create":
                        v = X[rng.randrange(len(X))]
                        async with s.post(f"{base}/api/v1/libraries/{lib}/chunks", json={"text": "new", "embedding": v.tolist()}) as r:
                            if r.status == 201: live.append((await r.json())["id"])
                            bump(op, r.status)
                    elif op == "update" and live:
                        cid = rng.choice(live); v = X[rng.randrange(len(X))]
                        async with s.put(f"{base}/api/v1/libraries/{lib}/chunks/{cid}", json={"embedding": v.tolist(), "text": "upd"}) as r:
                            await r.read(); bump(op, r.status)
                    elif op == "delete" and live:
                        cid = live.pop(rng.randrange(len(live)))
                        async with s.delete(f"{base}/api/v1/libraries/{lib}/chunks/{cid}") as r:
                            await r.read(); bump(op, r.status)
                except Exception as e: stats["exc"].append(repr(e))
        await asyncio.gather(*(reader(j) for j in range(readers)), *(writer(j) for j in range(8)))
        async with s.get(base + "/debug/indexes") as r:
            dbg = await r.json()
        async with s.get(f"{base}/api/v1/libraries/{lib}/chunks") as r:
            chunks = await r.json()
    info = dbg["libraries"][lib]
    return stats, info, len(chunks), len(live)

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True); p.add_argument("--n", type=int, default=1000)
    p.add_argument("--index", default="flat"); p.add_argument("--levels", type=int, nargs="+", default=[10, 100, 1000])
    p.add_argument("--requests", type=int, default=2000); p.add_argument("--port", type=int, default=8765)
    p.add_argument("--mixed", action="store_true"); p.add_argument("--mixed-seconds", type=int, default=30)
    a = p.parse_args()
    d = np.load(a.data, allow_pickle=True); X, Q = d["X"][: a.n], d["Q"]
    env = dict(os.environ, PERSISTENCE_ENABLED="false")
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(a.port), "--log-level", "warning",
                            "--backlog", "4096"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base = f"http://127.0.0.1:{a.port}"
    try:
        await wait_up(base)
        lib, ids, st = await seed(base, X, a.index)
        print(f"seeded {a.n} chunks ({a.index}) via HTTP in {st:.1f}s ({a.n/st:.0f} inserts/s)", flush=True)
        for c in a.levels:
            r = await load(base, lib, Q, c, a.requests)
            print(f"[{a.index} n={a.n}] conc={c:5d} req={r['total']} wall={r['wall']:.1f}s thrpt={r['rps']:.1f} req/s "
                  f"p50={r['p50']:.0f}ms p90={r['p90']:.0f}ms p99={r['p99']:.0f}ms max={r['max']:.0f}ms codes={r['codes']} errors={r['errors']}", flush=True)
        if a.mixed:
            stats, info, nchunks, nlive = await mixed(base, lib, ids, X, Q, readers=100, seconds=a.mixed_seconds)
            print(f"mixed: {stats['search']=} {stats['create']=} {stats['update']=} {stats['delete']=} exceptions={len(stats['exc'])} {stats['exc'][:3]}")
            print(f"mixed consistency: index_size={info['index_size']} chunk_store={info['total_chunks']} list_chunks={nchunks} client_live={nlive}")
        print("server alive:", srv.poll() is None)
    finally:
        srv.terminate(); _, err = srv.communicate(timeout=20)
        tail = err.decode()[-1500:]
        if "Traceback" in tail or "ERROR" in tail: print("server stderr tail:\n", tail)

asyncio.run(main())
