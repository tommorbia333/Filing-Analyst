"""Load edgar-crawler extracted 10-K sections as Documents with metadata."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SECTIONS: dict[str, str] = {
    "item_1A": "Item 1A",
    "item_7": "Item 7",
}


@dataclass(frozen=True)
class Document:
    text: str
    company: str
    fiscal_year: int
    section: str
    source: str


def _fiscal_year(period_of_report: str) -> int:
    """'2024-06-30' → 2024."""
    return int(period_of_report[:4])


def _extracted_dir(corpus_dir: Path) -> Path:
    return corpus_dir / "EXTRACTED_FILINGS" / "10-K"


def load_corpus(corpus_dir: Path) -> list[Document]:
    filings_dir = _extracted_dir(corpus_dir)
    if not filings_dir.is_dir():
        raise FileNotFoundError(
            f"Expected edgar-crawler output at {filings_dir}. "
            "Run the extractor or point corpus_dir at data/corpus."
        )

    docs: list[Document] = []
    for path in sorted(filings_dir.glob("*.json")):
        filing = json.loads(path.read_text(encoding="utf-8"))
        company = filing["company"]
        fiscal_year = _fiscal_year(filing["period_of_report"])

        for json_key, section_label in SECTIONS.items():
            text = (filing.get(json_key) or "").strip()
            if not text:
                continue
            docs.append(
                Document(
                    text=text,
                    company=company,
                    fiscal_year=fiscal_year,
                    section=section_label,
                    source=path.name,
                )
            )

    if not docs:
        raise FileNotFoundError(f"No section documents found in {filings_dir}")
    return docs
