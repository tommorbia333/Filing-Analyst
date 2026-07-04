"""Run retrieval eval over data/qa/gold.jsonl. Usage: uv run python scripts/eval_retrieval.py"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

from rag.config import settings
from rag.embed.embedder import Embedder
from rag.eval.metrics import hit_rate_at_k, mrr_at_k
from rag.ingest.chunker import Chunk
from rag.retrieve.dense import DenseIndex
from rag.retrieve.pg_dense import PgDenseIndex


def load_gold(path: Path) -> list[dict]:
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        items.append(json.loads(line))
    if not items:
        raise FileNotFoundError(f"No gold items in {path}")
    return items


def is_relevant(chunk: Chunk, gold: dict) -> bool:
    if chunk.fiscal_year != gold["fiscal_year"]:
        return False
    if chunk.section != gold["section"]:
        return False
    needle = gold.get("match_text")
    if needle and needle.lower() not in chunk.text.lower():
        return False
    return True


def main() -> None:
    gold = load_gold(settings.qa_path)
    embedder = Embedder(settings.embed_model, settings.cache_dir)

    if settings.database_url:
        index = PgDenseIndex.from_dsn(settings.database_url)
        backend = "pgvector"
    else:
        emb = np.load(settings.cache_dir / "embeddings.npy")
        with open(settings.cache_dir / "chunks.pkl", "rb") as f:
            chunks = pickle.load(f)
        index = DenseIndex(emb, chunks)
        backend = "numpy"
    k = settings.top_k

    rankings: list[list[bool]] = []
    for item in gold:
        qvec = embedder.encode_query(item["question"])
        hits = index.search(qvec, k)
        rankings.append([is_relevant(chunk, item) for _, chunk in hits])

    hr = hit_rate_at_k(rankings, k)
    mrr = mrr_at_k(rankings, k)

    print(f"backend: {backend}")
    print(f"queries: {len(gold)}")
    print(f"hit_rate@{k}: {hr:.3f}")
    print(f"mrr@{k}:       {mrr:.3f}")

    print("\n-- per query --")
    for item, row in zip(gold, rankings, strict=True):
        hit = any(row)
        rank = next((i for i, ok in enumerate(row, start=1) if ok), None)
        status = f"hit@{rank}" if hit else "miss"
        print(f"[{status}] FY{item['fiscal_year']} {item['section']}: {item['question'][:70]}...")


if __name__ == "__main__":
    main()
