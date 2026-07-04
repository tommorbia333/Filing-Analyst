"""Central config. Keep magic numbers here so the README can cite exact settings."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    corpus_dir: Path = ROOT / "data" / "corpus"
    qa_path: Path = ROOT / "data" / "qa" / "gold.jsonl"
    cache_dir: Path = ROOT / ".cache"

    embed_model: str = "BAAI/bge-small-en-v1.5"  # 384-dim, ~512-token window
    chunk_size: int = 256    # tokens; must stay under the embedder's 512 window
    chunk_overlap: int = 32  # tokens

    top_k: int = 5

    gen_model: str = "claude-haiku-4-5"    # verify exact string when we wire the SDK
    judge_model: str = "claude-sonnet-4-6"

    @property
    def database_url(self) -> str | None:
        return os.environ.get("DATABASE_URL")

    @property
    def anthropic_api_key(self) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set. Copy .env.example -> .env")
        return key


settings = Settings()
