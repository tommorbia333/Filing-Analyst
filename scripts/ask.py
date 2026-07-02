"""Query the index end-to-end. Run: uv run python scripts/ask.py "your question" """
from __future__ import annotations
import pickle
import sys
import numpy as np
from rag.config import settings
from rag.embed.embedder import Embedder
from rag.retrieve.dense import DenseIndex
from rag.generate.client import generate


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Question: ")
    emb = np.load(settings.cache_dir / "embeddings.npy")
    with open(settings.cache_dir / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    index = DenseIndex(emb, chunks)
    qvec = Embedder(settings.embed_model, settings.cache_dir).encode_query(question)
    hits = index.search(qvec, settings.top_k)

    print("\n-- retrieved --")
    for score, c in hits:
        print(f"[{score:.3f}] {c.source}: {c.text[:80]}...")

    print("\n-- answer --")
    print(generate(question, [c for _, c in hits]))


if __name__ == "__main__":
    main()
