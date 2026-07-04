"""Assemble the RAG prompt."""
from __future__ import annotations

from rag.ingest.chunker import Chunk

SYSTEM = (
    "You answer strictly from the provided context. If the answer is not in the "
    "context, say 'I don't know based on the provided context.' Cite the chunk "
    "numbers you used, e.g. [2]."
)


def build_user_prompt(question: str, chunks: list[Chunk]) -> str:
    blocks = [f"[{i}] (source: {c.source})\n{c.text}" for i, c in enumerate(chunks, 1)]
    context = "\n\n".join(blocks)
    return f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
