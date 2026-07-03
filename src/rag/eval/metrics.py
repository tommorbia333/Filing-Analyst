"""Retrieval metrics. Implement these yourself -- it's half of understanding eval.

hit_rate@k: fraction of queries where a relevant chunk appears in the top-k.
mrr@k:      mean of 1/rank of the FIRST relevant chunk (0 if none in top-k).

'relevant' is decided by your gold set. Start simple: a retrieved chunk counts as
relevant if it comes from the gold source doc (or contains the gold answer span).
"""
from __future__ import annotations


def hit_rate_at_k(rankings: list[list[bool]], k: int) -> float:
    """rankings[i] = booleans over retrieved results for query i (True = relevant)."""
    if not rankings:
        return 0.0

    hits = 0
    for row in rankings:
        top = row[:k]
        # BLANK A: does this query get a hit in top-k?
        if any(top):
            hits += 1

    return hits / len(rankings)


def mrr_at_k(rankings: list[list[bool]], k: int) -> float:
    """Mean reciprocal rank of the first relevant chunk in top-k."""
    if not rankings:
        return 0.0

    reciprocals: list[float] = []
    for row in rankings:
        top = row[:k]
        # BLANK B: rank of first True (1-indexed), or 0 if none
        for i, ok in enumerate(top, start=1):
            if ok:
                rank = i
                break
        else:
            rank = 0

        reciprocals.append(1.0 / rank if rank > 0 else 0.0)

    return sum(reciprocals) / len(reciprocals)