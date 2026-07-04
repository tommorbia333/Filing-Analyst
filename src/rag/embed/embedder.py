"""Local embeddings via sentence-transformers, cached to disk.

bge-* models prepend a query instruction to queries (not passages).
Vectors are L2-normalized so cosine similarity equals a dot product.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class Embedder:
    def __init__(self, model_name: str, cache_dir: Path):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.cache = cache_dir / "embeddings"
        self.cache.mkdir(parents=True, exist_ok=True)

    def _key(self, text: str) -> Path:
        h = hashlib.sha1(f"{self.model_name}::{text}".encode()).hexdigest()
        return self.cache / f"{h}.npy"

    def _encode_one(self, text: str) -> np.ndarray:
        p = self._key(text)
        if p.exists():
            return np.load(p)
        vec = self.model.encode(text, normalize_embeddings=True).astype(np.float32)
        np.save(p, vec)
        return vec

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self._encode_one(t) for t in texts])

    def encode_query(self, query: str) -> np.ndarray:
        return self._encode_one(_BGE_QUERY_INSTRUCTION + query)
