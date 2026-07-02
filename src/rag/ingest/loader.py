"""Load a corpus of plain-text / markdown (and optionally PDF) documents."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    source: str   # filename, used as provenance in chunk metadata
    text: str


def load_corpus(corpus_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(corpus_dir.iterdir()):
        if path.suffix.lower() in {".txt", ".md"}:
            docs.append(Document(source=path.name, text=path.read_text(encoding="utf-8")))
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            docs.append(Document(source=path.name, text=text))
    if not docs:
        raise FileNotFoundError(f"No .txt/.md/.pdf files in {corpus_dir}")
    return docs
