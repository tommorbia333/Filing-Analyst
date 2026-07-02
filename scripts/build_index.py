"""Ingest -> chunk -> embed -> persist. Run: uv run python scripts/build_index.py"""
from __future__ import annotations
import pickle
import numpy as np
from transformers import AutoTokenizer
from rag.config import settings
from rag.ingest.loader import load_corpus
from rag.ingest.chunker import chunk_document
from rag.embed.embedder import Embedder


def main() -> None:
    settings.cache_dir.mkdir(exist_ok=True)
    tok = AutoTokenizer.from_pretrained(settings.embed_model)

    docs = load_corpus(settings.corpus_dir)
    print(f"{len(docs)} section documents")

    chunks = []
    for doc in docs:
        chunks.extend(
            chunk_document(
                doc.text,
                tok,
                settings.chunk_size,
                settings.chunk_overlap,
                company=doc.company,
                fiscal_year=doc.fiscal_year,
                section=doc.section,
                source=doc.source,
            )
        )
    print(f"{len(chunks)} chunks")

    emb = Embedder(settings.embed_model, settings.cache_dir).encode_passages([c.text for c in chunks])
    np.save(settings.cache_dir / "embeddings.npy", emb)
    with open(settings.cache_dir / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
    print(f"index built -> {settings.cache_dir}")


if __name__ == "__main__":
    main()
