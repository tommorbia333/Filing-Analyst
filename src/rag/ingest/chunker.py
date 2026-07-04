"""Fixed-size token chunker with overlap, using the embedding model's tokenizer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    chunk_index: int
    start_token: int
    end_token: int
    company: str
    fiscal_year: int
    section: str


def chunk_document(
    text: str,
    tokenizer,
    chunk_size: int,
    overlap: int,
    *,
    company: str,
    fiscal_year: int,
    section: str,
    source: str = "",
) -> list[Chunk]:
    token_ids = tokenizer.encode(text, add_special_tokens=False)

    if overlap >= chunk_size:
        raise ValueError(f"Overlap must be smaller than chunk size: {overlap} >= {chunk_size}")
    step = chunk_size - overlap

    chunks: list[Chunk] = []
    for start in range(0, len(token_ids), step):
        window = token_ids[start : start + chunk_size]
        actual_start = start

        while window and tokenizer.convert_ids_to_tokens(window)[0].startswith("##"):
            window = window[1:]
            actual_start += 1

        chunks.append(
            Chunk(
                text=tokenizer.decode(window),
                source=source,
                chunk_index=len(chunks),
                start_token=actual_start,
                end_token=actual_start + len(window),
                company=company,
                fiscal_year=fiscal_year,
                section=section,
            )
        )
    return chunks
