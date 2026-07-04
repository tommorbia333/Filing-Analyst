"""Keyword / lexical retrieval via in-process BM25.

YOUR TASK: implement KeywordIndex.search().

Design choice (Station 7): rank-bm25 over chunk texts, not Postgres FTS.
Practice the classic lexical scorer; Station 9 can still pre-filter the corpus
in Python (or load a filtered subset from Postgres) before scoring.

Return shape must match PgDenseIndex: list[tuple[float, Chunk]], high score first.
"""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from rag.ingest.chunker import Chunk
import numpy as np

import re

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class KeywordIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        # BLANK A: build tokenized corpus and BM25Okapi index
        tokenized = [_tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    @classmethod
    def from_cache(cls, chunks: list[Chunk]) -> KeywordIndex:
        return cls(chunks)

    def search(self, query: str, k: int, fiscal_year: int | None = None,
           section: str | None = None) -> list[tuple[float, Chunk]]:
        """Return top-k (score, Chunk) pairs by BM25 rank.

        Hints:
          - query is a *string* (not a vector) — e.g. "Copilot" or a full gold question
          - tokenized_query = _tokenize(query)
          - scores = self.bm25.get_scores(tokenized_query)  # numpy array, one per chunk
          - take top-k indices (same pattern as DenseIndex: argpartition / argsort)
          - return [(float(scores[i]), self.chunks[i]), ...] high → low
          - if all scores are 0 (no term overlap), still return top-k zeros — or []
            (pick one and be ready to defend it)
        """
        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)  # one score per chunk

        # PRE-FILTER: if fiscal_year / section given, kill non-matching scores
        if fiscal_year is not None and section is not None:
            for i, chunk in enumerate(self.chunks):
                if chunk.fiscal_year != fiscal_year or chunk.section != section:
                    scores[i] = -1.0   # or -np.inf — anything below real BM25 scores

        top_k_indices = np.argsort(scores)[::-1][:k]
        return [(float(scores[i]), self.chunks[i]) for i in top_k_indices]