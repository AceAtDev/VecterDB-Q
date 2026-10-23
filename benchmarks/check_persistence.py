"""Persistence / crash-recovery check: write via HTTP, SIGKILL uvicorn (also mid-write), restart, compare.

Usage: python benchmarks/check_persistence.py --data /tmp/vdbq-data/agnews_minilm.npz --dir /tmp/vdbq-persist
"""
import argparse, os, shutil, signal, subprocess, sys, time, threading
from pathlib import Path
import numpy as np, requests

ROOT = Path(__file__).resolve().parent.parent

def start(port, path):
    env = dict(os.environ, PERSISTENCE_ENABLED="true", PERSISTENCE_PATH=path)
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
                         cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(300):
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=1).ok: return p
        except Exception: pass
        time.sleep(0.1)
    raise RuntimeError("no start")

def search(base, lib, q):
    r = requests.post(f"{base}/api/v1/libraries/{lib}/search", json={"embedding": q.tolist(), "k": 10, "metric": "cosine"})
    r.raise_for_status(); return [h["chunk"]["id"] for h in r.json()]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--dir", default="/tmp/vdbq-persist")
    ap.add_argument("--n", type=int, default=2000); ap.add_argument("--port", type=int, default=8780)
    a = ap.parse_args()
    shutil.rmtree(a.dir, ignore_errors=True); os.makedirs(a.dir)
    path = os.path.join(a.dir, "vectordb.pkl"); base = f"http://127.0.0.1:{a.port}"
    d = np.load(a.data, allow_pickle=True); X, Q = d["X"], d["Q"][:5]
    p = start(a.port, path)
    libs = {}
    for kind in ("flat", "ivf"):
        libs[kind] = requests.post(f"{base}/api/v1/libraries", json={"name": kind, "index_type": kind}).json()["id"]
    # ingestion rate with persistence on (each insert re-pickles the whole chunk store)
    lib = libs["flat"]; t0 = time.perf_counter(); marks = {}
    for i in range(a.n):
        r = requests.post(f"{base}/api/v1/libraries/{lib}/chunks", json={"text": f"t{i}", "embedding": X[i].tolist()}); assert r.status_code == 201
        if (i + 1) in (100, 500, 1000, 2000, 5000):
            marks[i + 1] = time.perf_counter()
    prev, pt = 0, t0
    for k, t in marks.items():
        print(f"persisted inserts {prev+1}-{k}: {(k-prev)/(t-pt):.0f} inserts/s  (chunks.pkl={os.path.getsize(os.path.join(a.dir,'vectordb','chunks.pkl'))/1e6:.1f} MB at end)")
        prev, pt = k, t
    for i in range(300):
        requests.post(f"{base}/api/v1/libraries/{libs['ivf']}/chunks", json={"text": f"t{i}", "embedding": X[i].tolist()})
    before = {k: [search(base, v, q) for q in Q] for k, v in libs.items()}
    os.kill(p.pid, signal.SIGKILL); p.wait()
    print("SIGKILL after quiescent writes; files:", sorted(os.listdir(os.path.join(a.dir, "vectordb"))))
    p = start(a.port, path)
    after = {k: [search(base, v, q) for q in Q] for k, v in libs.items()}
    dbg = requests.get(f"{base}/debug/indexes").json()
    for k, v in libs.items():
        info = dbg["libraries"][v]
        same = sum(b == c for b, c in zip(before[k], after[k]))
        print(f"after restart [{k}]: chunks={info['total_chunks']} index_size={info['index_size']} identical top-10 for {same}/{len(Q)} queries")
    # kill mid-write: concurrent writers, SIGKILL at random time
    stop = threading.Event(); acked = []
    def writer():
        i = 0
        while not stop.is_set():
            try:
                r = requests.post(f"{base}/api/v1/libraries/{libs['flat']}/chunks", json={"text": "mid", "embedding": X[i % len(X)].tolist()}, timeout=5)
                if r.status_code == 201: acked.append(r.json()["id"])
            except Exception: pass
            i += 1
    ths = [threading.Thread(target=writer) for _ in range(4)]; [t.start() for t in ths]
    time.sleep(3); os.kill(p.pid, signal.SIGKILL); p.wait(); stop.set(); [t.join() for t in ths]
    print("SIGKILL mid-write; files:", sorted(os.listdir(os.path.join(a.dir, "vectordb"))), f"acked writes={len(acked)}")
    p = start(a.port, path)
    ids = {c["id"] for c in requests.get(f"{base}/api/v1/libraries/{libs['flat']}/chunks").json()}
    lost = [x for x in acked if x not in ids]
    print(f"after mid-write crash restart: flat chunks={len(ids)}, acknowledged-but-lost={len(lost)}, search ok={len(search(base, libs['flat'], Q[0]))==10}")
    # orphan check: delete library, restart, are chunks still in chunks.pkl?
    requests.delete(f"{base}/api/v1/libraries/{libs['ivf']}")
    import pickle
    with open(os.path.join(a.dir, "vectordb", "chunks.pkl"), "rb") as f: data = pickle.load(f)
    from uuid import UUID
    print("after DELETE library ivf: its chunks still in chunks.pkl =", len(data["chunks"].get(UUID(libs["ivf"]), {})))
    p.terminate(); p.wait()

if __name__ == "__main__":
    main()
