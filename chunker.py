"""Fixed-size token chunker with overlap.

DESIGN DECISION (defend this in the README):
We chunk using the *embedding model's own tokenizer* so a chunk can never exceed
the model's context window (bge-small-en = 512 tokens). Chunking by characters or
naive whitespace risks silently truncating chunks at embed time -> lost information.

YOUR TASK: implement chunk_document so tests/test_chunker.py passes.
Algorithm (sliding window over token ids):
  1. token_ids = tokenizer.encode(text, add_special_tokens=False)
  2. step = chunk_size - overlap   (assert step > 0)
  3. for start in range(0, len(token_ids), step):
        window = token_ids[start : start + chunk_size]
        text   = tokenizer.decode(window)
        -> emit a Chunk(...) ; stop when the window reaches the end
  4. carry source + a running chunk_index into each Chunk.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    chunk_index: int
    start_token: int
    end_token: int


def chunk_document(text: str, tokenizer, chunk_size: int, overlap: int) -> list[Chunk]:
    raise NotImplementedError("Implement me to pass tests/test_chunker.py")
