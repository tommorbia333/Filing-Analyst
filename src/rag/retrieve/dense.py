"""Brute-force dense retrieval over L2-normalized embeddings (cosine == dot product)."""
from __future__ import annotations

import numpy as np

from rag.ingest.chunker import Chunk


class DenseIndex:
    def __init__(self, embeddings: np.ndarray, chunks: list[Chunk]):
        assert len(embeddings) == len(chunks)
        self.embeddings = embeddings
        self.chunks = chunks

    def search(self, query_vec: np.ndarray, k: int) -> list[tuple[float, Chunk]]:
        query_vec = query_vec.reshape(-1)
        scores = self.embeddings @ query_vec
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        return [(float(scores[i]), self.chunks[i]) for i in top_indices]
