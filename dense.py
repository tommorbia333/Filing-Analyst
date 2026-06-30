"""Brute-force dense retrieval. Week 1 = understand the primitive before adopting a real store.

YOUR TASK: implement search().
Because embeddings are L2-normalized, cosine(q, d) == q . d.
So: scores = embeddings @ query_vec ; take the top-k indices.
Return (score, Chunk) pairs sorted high->low. numpy.argsort / argpartition are your friends.
"""
from __future__ import annotations
import numpy as np
from rag.ingest.chunker import Chunk


class DenseIndex:
    def __init__(self, embeddings: np.ndarray, chunks: list[Chunk]):
        assert len(embeddings) == len(chunks)
        self.embeddings = embeddings
        self.chunks = chunks

    def search(self, query_vec: np.ndarray, k: int) -> list[tuple[float, Chunk]]:
        raise NotImplementedError("Implement brute-force cosine top-k")
