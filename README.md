# RAG over SEC 10-K Filings — an internal-document assistant, built from scratch

A retrieval-augmented generation pipeline over one company's SEC 10-K annual filings across several fiscal years. Ask a question, get an answer grounded in the correct filing — with the *right year*, not just the right topic.

No orchestration frameworks (LangChain, LlamaIndex, etc.). Every component — chunking, embedding, retrieval, generation, evaluation — is implemented explicitly.

## The core retrieval problem

10-K risk factors and MD&A recycle near-identical language year over year. A pure vector search ranks the FY2021 and FY2023 versions of a paragraph as near-ties — but only one answers a question about 2023. This project resolves that by combining semantic search with a structured `fiscal_year` / `section` filter over Postgres.

## Architecture

```
10-K filings → Loader (+ metadata: company, fiscal_year, section) → Chunker → Embedder
                                                                        |
                                                                   Vector store
                                                                        |
   Retriever (dense + keyword + fiscal_year/section filter) → Generator → Grounded answer
                                                                        ^
                                                                   Eval harness
                                                       (retrieval-gold + faithfulness)
```

## Evaluation

Retrieval is scored against a hand-authored gold set with **year-aware relevance** (a textually perfect chunk from the wrong year does not count as a hit), using hit-rate@k and MRR. Answer quality is scored by an LLM-as-judge for **faithfulness** to the retrieved filing.

## Stack

- **Python 3.11**, managed with `uv`
- **Ingest:** SEC 10-K filings → text, with section + fiscal-year metadata extraction
- **Embeddings:** `BAAI/bge-small-en-v1.5` (local, cached)
- **Retrieval:** brute-force cosine → Postgres + pgvector + full-text + metadata filter
- **Generator:** Claude Haiku 4.5 · **Judge:** Claude Sonnet 4.6
- **Linting:** ruff · **Testing:** pytest

## Quickstart

```bash
make install               # create venv + editable install
cp .env.example .env       # add your ANTHROPIC_API_KEY
make test                  # run the test suite
make index                 # ingest 10-Ks -> chunk (+metadata) -> embed -> persist
make ask                   # query the pipeline end-to-end
```

## Project structure

```
src/rag/
  ingest/      # filing loader (+ metadata), chunking
  embed/       # embedding with bge-small
  retrieve/    # dense, hybrid + metadata filter
  generate/    # Claude API client + prompt building
  eval/        # retrieval metrics + faithfulness judge
scripts/       # CLI entry points
data/          # corpus + gold Q/A set
tests/         # pytest suite
```
