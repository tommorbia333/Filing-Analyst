# Current: ETL & RAG over SEC 10-K Filings built from scratch

The current status of this project stands as a RAG over one company's SEC 10-K annual filings across several fiscal years. Steps & general architecture have been outlined below, as well as the current state and future direction of the project. 

No orchestration frameworks (LangChain, LlamaIndex, etc.) were used; chunking, embedding, retrieval, generation, evaluation are all implemented explicitly.

## Overview

- **Corpus:** Microsoft 10-K filings, FY2019–FY2025 (fiscal year ends June 30), parsed via edgar-crawler into Item 1A (Risk Factors) and Item 7 (MD&A)
- **Problem:** same boilerplate recurs across years — dense retrieval often finds the right *topic* from the wrong *fiscal year*
- **Approach:** hybrid retrieval (dense + BM25, fused with RRF) plus a `fiscal_year` / `section` metadata pre-filter over Postgres + pgvector
- **Eval:** hand-authored gold set with year-aware relevance; retrieval scored with hit-rate@k and MRR; answer quality scored with an LLM faithfulness judge (not finance-expert correctness)
- **Status:** Week 1 complete; Week 2 Stations 6–9 complete; Station 10 (faithfulness judge + scale gold) nearly done — judge wired, gold at 14/~25

## Design decisions

- **Chunking:** 256 tokens, 32 overlap, using the embedding model's tokenizer (not char/word count) so chunks stay within the 512-token embed window
- **Chunk metadata:** every chunk carries `{company, fiscal_year, section}` from ingest — required for the Week 2 filter
- **Chunk IDs:** `{source}::{section}::{chunk_index}` — `chunk_index` resets per section, so source alone caused Postgres upsert collisions (692 chunks → 384 rows, metrics dropped to 0.231)
- **Embeddings:** `BAAI/bge-small-en-v1.5`, local + disk-cached, L2-normalized (cosine = dot product); query instruction prepended to queries only
- **Dense retrieval (wk1):** brute-force cosine over numpy; pgvector HNSW in wk2 (parity check, not primarily a speed play at this corpus size)
- **Vector store:** Postgres + pgvector + btree indexes on `fiscal_year` and `section` — vectors live next to metadata for hybrid SQL filtering
- **Keyword retrieval:** in-process BM25 (`rank-bm25`) over Postgres FTS — IDF helps on a corpus where boilerplate terms repeat every year; distinctive tokens (Copilot, COVID-19, GitHub) rank well
- **Tokenization fix:** `_tokenize` splits on non-alphanumerics so HTML-extracted `covid - 19` matches query `COVID-19`
- **Hybrid fusion:** Reciprocal Rank Fusion (k=60) — avoids normalizing incompatible dense/BM25 score scales
- **Metadata filter:** pre-filter (`WHERE fiscal_year AND section` before ranking) — cuts near-duplicate yearly boilerplate early; post-filter can silently under-return at fixed top-k
- **Relevance rule:** hit = `fiscal_year` + `section` match; optional `match_text` only for distinctive tokens; hyphen/space normalization in eval harness
- **Generator:** Claude Haiku 4.5 with exponential backoff + jitter on transient errors (max 5 retries); ~$0.003/query (~1500 input + ~250 output tokens)
- **Faithfulness judge:** Claude Sonnet scores whether the answer is grounded in retrieved context (not whether it's correct against the real filing)
- **Filter gap (future):** gold eval hands in `fiscal_year`/`section`; a real user query needs query understanding (agent/LLM tool args or regex) — Phase 4

## Retrieval results (gold set, k=5)

| Config | hit-rate@5 | MRR@5 |
|---|---|---|
| Dense only (wk1 baseline) | 0.385 | 0.179 |
| Hybrid RRF, no filter | 0.385 | 0.172 |
| Hybrid RRF + metadata filter | 0.846 | 0.769 |
| Hybrid + filter + relevance-rule fixes | **1.000** | — |

Dominant wk1 failure mode: right topic, wrong fiscal year. RRF alone did not fix wrong-year boilerplate; the metadata filter did.

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
- **Retrieval:** brute-force cosine → Postgres + pgvector + BM25 + RRF + metadata filter
- **Generator:** Claude Haiku 4.5 · **Judge:** Claude Sonnet 4.6
- **Linting:** ruff · **Testing:** pytest

## Quickstart

```bash
make install               # create venv + editable install
cp .env.example .env       # add ANTHROPIC_API_KEY and DATABASE_URL
make test                  # run the test suite
make index                 # ingest 10-Ks -> chunk (+metadata) -> embed -> persist
make db-up && make db-load # Postgres + load vectors
make ask                   # query the pipeline end-to-end
make eval                  # retrieval eval
make eval-faithful         # retrieval + generation + faithfulness judge
```

## Project structure

```
src/rag/
  ingest/      # filing loader (+ metadata), chunking
  embed/       # embedding with bge-small
  retrieve/    # dense, keyword, hybrid, pgvector
  generate/    # Claude API client + prompt building
  eval/        # retrieval metrics + faithfulness judge
scripts/       # CLI entry points
data/          # corpus + gold Q/A set
tests/         # pytest suite
```
