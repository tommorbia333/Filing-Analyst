"""Target spec for chunk_document. Run: uv run pytest -q (red until you implement it)."""
import pytest
from transformers import AutoTokenizer
from rag.ingest.chunker import chunk_document

TOK = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
TEXT = " ".join(f"word{i}" for i in range(400))  # ~hundreds of tokens


_META = {"company": "TEST", "fiscal_year": 2024, "section": "Item 1A"}


def _chunks(size=100, overlap=20):
    return chunk_document(TEXT, TOK, chunk_size=size, overlap=overlap, **_META)


def test_produces_chunks():
    assert len(_chunks()) > 1


def test_no_chunk_exceeds_size():
    for c in _chunks(size=100, overlap=20):
        assert len(TOK.encode(c.text, add_special_tokens=False)) <= 100


def test_chunks_overlap():
    cs = _chunks(size=100, overlap=20)
    # consecutive chunks should share ~`overlap` tokens at the seam
    a = TOK.encode(cs[0].text, add_special_tokens=False)
    b = TOK.encode(cs[1].text, add_special_tokens=False)
    assert a[-20:] == b[:20]


def test_full_coverage():
    cs = _chunks(size=100, overlap=20)
    assert cs[0].start_token == 0
    assert cs[-1].end_token >= 390  # reached the end of the document


def test_overlap_must_be_smaller_than_size():
    with pytest.raises((ValueError, AssertionError)):
        chunk_document(TEXT, TOK, chunk_size=50, overlap=50, **_META)
