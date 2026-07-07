# Filing Analyst: grounded, year-aware QA over SEC 10-Ks

Filing Analyst is a retrieval-augmented QA system over one company's SEC 10-K annual filings across several fiscal years. I built it as a stand-in for the real problem it models: answering questions over a private enterprise document store where the same templated language repeats year after year. SEC filings are public, so they make a good proxy. Microsoft's Risk Factors and MD&A sections reuse near-identical boilerplate across fiscal years, and that repetition is what breaks naive semantic search.

No orchestration frameworks (LangChain, LlamaIndex, etc.) were used; chunking, embedding, retrieval, generation, and evaluation are all implemented explicitly and can be walked through line by line.

The overview below covers the current state, complete through the Week 2 evaluation harness. The next major step (Phase 4) turns this pipeline into a small live service with an explicit agent loop. I've sketched that at the bottom.

## Overview

- **Corpus:** Microsoft 10-K filings, FY2019-FY2025 (fiscal year ends June 30), downloaded from EDGAR and parsed locally with edgar-crawler into per-item sections; I use Item 1A (Risk Factors) and Item 7 (MD&A)
- **Problem:** the same boilerplate recurs across years, so dense retrieval often finds the right *topic* from the wrong *fiscal year*
- **Approach:** hybrid retrieval (dense + BM25, fused with RRF) plus a `fiscal_year` / `section` metadata pre-filter over Postgres + pgvector
- **Eval:** hand-authored gold set with year-aware relevance; retrieval scored with hit-rate@k and MRR; answer quality scored separately with an LLM faithfulness judge (grounding, not finance-expert correctness)
- **Status:** Week 1 complete; Week 2 Stations 6-9 complete; Station 10 (faithfulness judge + scale gold) nearly done (judge wired, gold at 14/~25)

## Design decisions

- **Chunking:** 256 tokens, 32 overlap, using the embedding model's own tokenizer (not char/word count) so chunks stay inside the 512-token embed window. Chunking by character or word count silently drifts from the token count a subword tokenizer actually produces, so a chunk that looks in-bounds can get truncated without warning.
- **Chunk metadata:** every chunk carries `{company, fiscal_year, section}` from ingest. A chunk that loses its `fiscal_year` is unfilterable later, and the Week 2 filter keys on these fields.
- **Chunk IDs:** `{source}::{section}::{chunk_index}`. `chunk_index` resets per section, so `{source}:{chunk_index}` alone caused Postgres upsert collisions (Item 1A and Item 7 both had a chunk 0, 1, 2...). 692 chunks collapsed to 384 rows and metrics dropped to 0.231 before I caught it; the section-qualified ID fixed it back to 0.385.
- **Embeddings:** `BAAI/bge-small-en-v1.5`, local + disk-cached, L2-normalized (so cosine = dot product); the query instruction is prepended to queries only, not passages, so the passages stay in "index" mode.
- **Dense retrieval (wk1):** brute-force cosine over numpy; pgvector HNSW in wk2. At this corpus size the move isn't primarily a speed play; it's for metadata filtering, keyword fusion, and persistence.
- **Vector store:** Postgres + pgvector + btree indexes on `fiscal_year` and `section`. Vectors live next to the metadata so hybrid SQL filtering is one query, not two systems. This is the "deploy on the infra they already run" story: most teams already have Postgres.
- **Keyword retrieval:** in-process BM25 (`rank-bm25`). IDF is useful on a corpus where boilerplate terms repeat every year, so distinctive tokens (Copilot, COVID-19, GitHub) rank well while "economic conditions" stays mushy. One caveat I'm deliberate about: aggressive stemming or stopword handling can mangle the exact tokens BM25 exists to catch (`Item 7A`, four-digit years, ticker-like tokens), so tokenization here is conservative.
- **Tokenization fix:** `_tokenize` splits on non-alphanumerics so HTML-extracted `covid - 19` matches a query for `COVID-19`. Before the fix, COVID-19 scored all zeros; after it, the top chunks land in 2020-2022, the peak pandemic years.
- **Hybrid fusion:** Reciprocal Rank Fusion (k=60). Dense scores are cosine (~0-1) and BM25 scores are unbounded and corpus-dependent, so naively adding them biases toward whichever scale is larger; RRF sidesteps normalization by fusing on rank position instead of score.
- **Metadata filter:** pre-filter (`WHERE fiscal_year AND section` before ranking) cuts near-duplicate yearly boilerplate early. Post-filter (rank then drop) can silently under-return at a fixed top-k, because it selects k *before* filtering and hands back whatever survives.
- **Relevance rule:** a hit = `fiscal_year` + `section` match; `match_text` is optional and only used for distinctive tokens, since `match_text` alone doesn't pin anything in a boilerplate-heavy corpus. Hyphen and space normalization lives in the eval harness.
- **Generator:** Claude Haiku 4.5 with exponential backoff + jitter on transient errors, capped at 5 retries. Jitter avoids the thundering-herd retry storm; the cap avoids infinite hung requests and wasted spend. Roughly $0.003/query (~1500 input + ~250 output tokens).
- **Faithfulness judge:** Claude Sonnet 4.6 scores whether the answer is grounded in the retrieved context, not whether it's correct against the real filing. That lets me grade answers honestly without being a finance expert.
- **Filter-args gap (Phase 4):** the gold eval hands in `fiscal_year`/`section`; a real user query needs a query-understanding step to extract them. That's the gap the Phase 4 agent closes.

## Retrieval results (gold set, k=5)

| Config | hit-rate@5 | MRR@5 |
| --- | --- | --- |
| Dense only (Week 1 baseline) | 0.385 | 0.179 |
| Hybrid RRF, no filter | 0.385 | 0.172 |
| **Hybrid RRF + metadata filter** | **0.846** | **0.769** |
| + eval-harness relevance-rule fix | 1.000 | n/a |

The headline is the third row. The metadata pre-filter is what actually fixed retrieval, taking hit-rate@5 from 0.385 to 0.846. RRF on its own did nothing for the wrong-year problem (0.385 to 0.385): fusing dense and keyword helps confusable *topics*, but boilerplate that repeats almost verbatim across years needs the `fiscal_year`/`section` filter, not better ranking. The dominant Week 1 failure was right topic, wrong fiscal year, and the filter is the thing that fixes it.

The last row (0.846 to 1.000) is a different kind of fix, and I'll be upfront about it: that wasn't the retriever getting better, it was my eval harness getting less wrong. COVID-19 was stored as `covid - 19` (spaces around the hyphen, an HTML-extraction artifact), so my `is_relevant` check kept failing to match chunks the retriever had already surfaced correctly. Once I normalized hyphen and space variants on both sides and stopped requiring `match_text` where `fiscal_year`+`section` already pin the answer, the last few gold items scored as the hits they always were. So read 0.846 as the retrieval result and 1.000 as the measurement finally agreeing with it.

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

Retrieval is scored against a hand-authored gold set with year-aware relevance: a textually perfect chunk from the wrong year does not count as a hit, because that's the failure the whole project is about. Answer quality is scored separately by an LLM-as-judge for faithfulness to the retrieved context (is the answer grounded in what was actually retrieved), not correctness against the real filing. Separating the two matters: retrieval catches whether the right passage surfaced, faithfulness catches whether the answer stayed grounded or invented a number the passage never gave.

The gold set also includes an absence case: asking about Copilot in FY2019, before it existed, where the correct answer is "not disclosed." It's a deliberate check that the system says nothing rather than fabricating content that isn't in the filing.

## Future direction: Phase 4, a live service with an explicit agent loop

Right now the retrieval filter values (`fiscal_year`, `section`) are handed in from the gold item. A real user doesn't do that. They just ask *"what did Microsoft say about supply-chain risk in 2023?"* and something has to turn that sentence into filter arguments. That's the seam between what I've built and where it's going: a query-understanding step that extracts the filter args before retrieval runs.

I'm closing that gap with a single explicit agent loop, not a multi-agent framework, and that's deliberate. The whole point of this project is that every component is defensible line by line, and reaching for LangGraph or CrewAI would throw that away. The loop is a plain Python state machine you can whiteboard:

```
plan     → extract fiscal_year / section / topic from the natural-language question
retrieve → hybrid search with those filter args
generate → Haiku answers from the retrieved context
check    → the Sonnet faithfulness judge verifies grounding
           → if unfaithful, retry with different args; else finish   (cap ~5 steps)
```

The generator and the judge are already a producer-critic pair, so Phase 4 just closes the loop between them. On top of that, a small tool registry (`search_filings(query, fiscal_year?, section?)`, `list_available_years()`, `compare_passages(year_a, year_b, topic)`) gives the loop real multi-step jobs: a true cross-*filing* comparison needs two retrievals and a synthesis, which is where an agent earns its keep over a single retrieve-then-generate call.

The rest of Phase 4 is a thin FastAPI wrapper (`POST /query` and `POST /agent/query`, the latter returning the answer plus a trace of which tools fired in what order) and one legacy-integration story: an ingest webhook or a mock ERP metadata adapter, built behind a small interface so the system depends on the interface, not the mock. That's the "deploy on the infrastructure a client already runs" story in miniature.

**Phase 5 (later):** async re-indexing when new filings arrive, auth/tenancy, cost and p95-latency instrumentation off the Phase 4 query logs, and a second adapter to show the integration pattern generalizes rather than being one-off.

## Stack

- **Python 3.11**, managed with `uv`
- **Ingest:** SEC 10-K filings → text, with section + fiscal-year metadata extraction (edgar-crawler)
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
