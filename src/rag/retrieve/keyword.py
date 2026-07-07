"""Keyword retrieval via in-process BM25."""
from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Okapi

from rag.ingest.chunker import Chunk


def _tokenize(text: str) -> list[str]:
    # Split on non-alphanumerics so "covid - 19" and "covid-19" tokenize the same.
    return re.findall(r"[a-z0-9]+", text.lower())


class KeywordIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        tokenized = [_tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    @classmethod
    def from_cache(cls, chunks: list[Chunk]) -> KeywordIndex:
        return cls(chunks)

    def search(
        self,
        query: str,
        k: int,
        fiscal_year: int | None = None,
        section: str | None = None,
    ) -> list[tuple[float, Chunk]]:
        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        if fiscal_year is not None and section is not None:
            for i, chunk in enumerate(self.chunks):
                if chunk.fiscal_year != fiscal_year or chunk.section != section:
                    scores[i] = -1.0

        top_k_indices = np.argsort(scores)[::-1][:k]
        return [(float(scores[i]), self.chunks[i]) for i in top_k_indices]
