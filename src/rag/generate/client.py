"""Claude Haiku 4.5 generation with retry/backoff.

YOUR TASK: implement generate().
Rate-limit reality (a stated learning objective): the API can return 429
(rate limit) and 529 (overloaded). Wrap the call in exponential backoff with
jitter, cap retries (~5), and re-raise on non-retryable errors (e.g. 400/401).
We'll confirm the exact SDK call + error types against the *current* Anthropic
SDK when we implement this together, so it doesn't go stale.
"""
from __future__ import annotations
from rag.config import settings
from rag.generate.prompt import SYSTEM, build_user_prompt
from rag.ingest.chunker import Chunk


def generate(question: str, chunks: list[Chunk], model: str | None = None) -> str:
    raise NotImplementedError("Implement Anthropic call + retry/backoff")
