"""Retrieval metrics. Implement these yourself -- it's half of understanding eval.

hit_rate@k: fraction of queries where a relevant chunk appears in the top-k.
mrr@k:      mean of 1/rank of the FIRST relevant chunk (0 if none in top-k).

'relevant' is decided by your gold set. Start simple: a retrieved chunk counts as
relevant if it comes from the gold source doc (or contains the gold answer span).
"""
from __future__ import annotations


def hit_rate_at_k(rankings: list[list[bool]], k: int) -> float:
    """rankings[i] = booleans over the top-k for query i (True = relevant)."""
    raise NotImplementedError


def mrr_at_k(rankings: list[list[bool]], k: int) -> float:
    raise NotImplementedError
