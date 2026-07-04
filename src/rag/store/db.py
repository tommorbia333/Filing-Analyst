"""Postgres connection + schema bootstrap."""
from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

from rag.config import ROOT, settings

SCHEMA_PATH = ROOT / "scripts" / "schema.sql"


def _dsn(dsn: str | None = None) -> str:
    url = dsn or settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL not set. Copy .env.example -> .env")
    return url


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = psycopg.connect(_dsn(dsn))
    register_vector(conn)
    return conn


def init_schema(dsn: str | None = None) -> None:
    """Run schema.sql. Connects without register_vector — extension must exist first."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with psycopg.connect(_dsn(dsn)) as conn:
        conn.execute(sql)
        conn.commit()
