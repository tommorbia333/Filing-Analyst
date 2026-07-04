"""Load .cache/ embeddings + chunks into Postgres. Run: make db-load"""
from __future__ import annotations

import pickle

import numpy as np

from rag.config import settings
from rag.ingest.chunker import Chunk
from rag.store.db import connect, init_schema


def chunk_id(chunk: Chunk) -> str:
    return f"{chunk.source}::{chunk.section}::{chunk.chunk_index}"


def main() -> None:
    emb_path = settings.cache_dir / "embeddings.npy"
    chunks_path = settings.cache_dir / "chunks.pkl"
    if not emb_path.is_file() or not chunks_path.is_file():
        raise FileNotFoundError("Run make index first — .cache/ is missing embeddings or chunks")

    embeddings = np.load(emb_path)
    with open(chunks_path, "rb") as f:
        chunks: list[Chunk] = pickle.load(f)

    if len(embeddings) != len(chunks):
        raise ValueError(f"length mismatch: {len(embeddings)} embeddings vs {len(chunks)} chunks")

    init_schema()

    upsert = """
        INSERT INTO chunks (id, company, fiscal_year, section, chunk_text, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            company = EXCLUDED.company,
            fiscal_year = EXCLUDED.fiscal_year,
            section = EXCLUDED.section,
            chunk_text = EXCLUDED.chunk_text,
            embedding = EXCLUDED.embedding
    """

    rows = [
        (
            chunk_id(chunk),
            chunk.company,
            chunk.fiscal_year,
            chunk.section,
            chunk.text,
            embeddings[i],
        )
        for i, chunk in enumerate(chunks)
    ]

    with connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(upsert, rows)
        conn.commit()

    print(f"loaded {len(rows)} chunks -> postgres")


if __name__ == "__main__":
    main()
