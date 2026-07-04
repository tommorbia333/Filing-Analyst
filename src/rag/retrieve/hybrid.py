"""Hybrid retrieval: fuse dense + keyword rankings with Reciprocal Rank Fusion.

RRF score for a chunk = sum over rankings of 1 / (k_rrf + rank), rank 1-based.
Chunks are keyed by (source, section, chunk_index) so pgvector and pickle
rows identity-match despite different start_token/end_token placeholders.
"""
from __future__ import annotations

import numpy as np

from rag.ingest.chunker import Chunk
from rag.retrieve.keyword import KeywordIndex
from rag.retrieve.pg_dense import PgDenseIndex


def chunk_key(chunk: Chunk) -> tuple:
    return (chunk.source, chunk.section, chunk.chunk_index)


def rrf(
    rankings: list[list[tuple[float, Chunk]]],
    k_rrf: int = 60,
) -> list[tuple[float, Chunk]]:
    """Fuse ranked lists into (rrf_score, Chunk) pairs, high → low."""
    scores: dict[tuple, float] = {}
    chunks: dict[tuple, Chunk] = {}
    for ranking in rankings:
        for rank, (_, chunk) in enumerate(ranking, start=1):
            key = chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k_rrf + rank)
            chunks.setdefault(key, chunk)
    return sorted(
        [(score, chunks[key]) for key, score in scores.items()],
        key=lambda x: x[0],
        reverse=True,
    )


class HybridIndex:
    def __init__(self, dense: PgDenseIndex, keyword: KeywordIndex, k_rrf: int = 60):
        self.dense = dense
        self.keyword = keyword
        self.k_rrf = k_rrf

    def search(self, query, query_vec, k, fiscal_year=None, section=None):
        dense_results = self.dense.search(
            query_vec, 2 * k, fiscal_year=fiscal_year, section=section
        )
        keyword_results = self.keyword.search(
            query, 2 * k, fiscal_year=fiscal_year, section=section
        )
        return rrf([dense_results, keyword_results], self.k_rrf)[:k]
