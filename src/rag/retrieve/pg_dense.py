"""Dense retrieval via pgvector."""
from __future__ import annotations

import numpy as np
import psycopg

from rag.ingest.chunker import Chunk
from rag.store.db import connect


def row_to_chunk(row: tuple) -> Chunk:
    """Map a DB row to Chunk."""
    _id, company, fiscal_year, section, chunk_text = row[:5]
    source, _section, chunk_index_str = _id.split("::", 2)
    return Chunk(
        text=chunk_text,
        source=source,
        chunk_index=int(chunk_index_str),
        start_token=0,
        end_token=0,
        company=company,
        fiscal_year=fiscal_year,
        section=section,
    )


class PgDenseIndex:
    def __init__(self, conn: psycopg.Connection):
        self.conn = conn

    @classmethod
    def from_dsn(cls, dsn: str) -> PgDenseIndex:
        return cls(connect(dsn))

    def search(self, query_vec: np.ndarray, k: int) -> list[tuple[float, Chunk]]:
        query_vec = query_vec.reshape(-1)

        sql = """
            SELECT id, company, fiscal_year, section, chunk_text,
                1 - (embedding <=> %s::vector) AS score
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (query_vec, query_vec, k))
            rows = cur.fetchall()

        return [(float(row[-1]), row_to_chunk(row[:-1])) for row in rows]
