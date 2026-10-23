"""Embed AG News passages with all-MiniLM-L6-v2 (384-d) for real-data benchmarks.

Usage: python benchmarks/embed_agnews.py --n 20000 --queries 100 --out /tmp/vdbq-data/agnews_minilm.npz
Corpus = first N train texts; queries = first Q test texts (held out).
"""
import argparse, time
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

p = argparse.ArgumentParser()
p.add_argument("--n", type=int, default=20000)
p.add_argument("--queries", type=int, default=100)
p.add_argument("--out", default="/tmp/vdbq-data/agnews_minilm.npz")
a = p.parse_args()

train = load_dataset("fancyzhx/ag_news", split="train")["text"][: a.n]
test = load_dataset("fancyzhx/ag_news", split="test")["text"][: a.queries]
m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
t = time.perf_counter()
X = m.encode(train, batch_size=128, normalize_embeddings=True, show_progress_bar=False)
Q = m.encode(test, batch_size=128, normalize_embeddings=True, show_progress_bar=False)
print(f"embedded {len(train)}+{len(test)} texts, dim={X.shape[1]}, {time.perf_counter()-t:.1f}s")
np.savez(a.out, X=X.astype(np.float32), Q=Q.astype(np.float32), texts=np.array(train, dtype=object))
