CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    company     TEXT NOT NULL,
    fiscal_year INT  NOT NULL,
    section     TEXT NOT NULL,
    chunk_text  TEXT NOT NULL,
    embedding   vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_fiscal_year_idx ON chunks (fiscal_year);
CREATE INDEX IF NOT EXISTS chunks_section_idx ON chunks (section);
