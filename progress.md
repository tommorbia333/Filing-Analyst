# RAG Capstone — Project Handbook

> This file is three things at once:
> 1. **A progress tracker** — what's done, what's active, what's sealed.
> 2. **An assignment handbook** — each station has tasks and *questions you answer yourself*. No answers are written here on purpose.
> 3. **A context handoff** — enough for a Cursor agent (or future-you) to pick up without re-explaining the project.
>
> Built end-to-end with **no orchestration frameworks** (no LangChain / LlamaIndex). Every component is explicit and defensible in an interview.

---

## How to use this handbook

- Work **top to bottom**. Do not open 🔒 sealed phases early — they're sealed so new terminology arrives only when you're ready for it. Phase 4 (API + agent) and Phase 5 (production) are sketched but locked until Weeks 1–3 (and Phase 4, for Phase 5) are complete.
- At each station: do the **Tasks**, then write your own answers to the **Questions** in the *Notes & answers* space. Fill the matching row in the **Design decisions log**.
- A station is done only when its **Definition of done** is met. Then advance.
- Use **Cursor** for implementation help and **this chat** for mentoring, quizzing, and unlocking the next phase. When a phase completes, the chat regenerates this handbook with the next phase expanded.

---

## For AI coding agents (Cursor) — read this first

**Project:** A local, scrappy, end-to-end RAG system over **one company's SEC 10-K filings across multiple fiscal years**, with a quantitative evaluation harness. The system is an internal-document-assistant archetype — SEC filings are a public stand-in for a private enterprise corpus. The human (Tom) is building this as a portfolio piece to defend in forward-deployed / solutions / applied-AI interviews.

**Hard rules — do not violate:**
1. **No high-level RAG frameworks.** No LangChain, no LlamaIndex, no framework that hides retrieval/chunking/orchestration. Thin libraries only (sentence-transformers, numpy, anthropic, psycopg, rank-bm25, typer).
2. **Low abstraction.** Prefer explicit, readable code the human can explain line-by-line over clever indirection.
3. **This is a learning project.** For the *precious* components below, **do not hand over finished solutions.** Review the human's code, point out bugs, ask leading questions, explain tradeoffs — but let them write it. You may write *plumbing* freely.
4. **Never answer the handbook Questions for the human.** If asked, coach toward the answer; don't state it.

**Precious (human implements, you coach):** `ingest/chunker.py`, `retrieve/dense.py`, `generate/client.py` (retry/backoff), `eval/metrics.py`.
**Plumbing (you may write freely):** `ingest/loader.py` (parses filings into sections + metadata), `embed/embedder.py`, `generate/prompt.py`, `scripts/`.

**Stack (locked):** Python 3.11 · `uv` · `ruff` (line length 100; rules E,F,I,UP,B) · `pytest` (`pythonpath=src`). Embeddings `BAAI/bge-small-en-v1.5` (local, cached, normalized). Retrieval: brute-force cosine (Week 1) → Postgres + pgvector + full-text search, metadata-filtered (Week 2). Generator: Claude Haiku 4.5. Judge: Claude Sonnet (faithfulness). Config lives in `src/rag/config.py`. One commit per component.

**Data note:** the corpus is a single company's 10-K filings, parsed into their standard sections with `{company, fiscal_year, section}` metadata per record. Prefer a pre-parsed EDGAR dataset (e.g. `eloukas/edgar-corpus`, which already splits filings into sections with `cik`/`year`) or `edgar-crawler` JSON output over writing a filing parser from scratch — parsing raw HTML filings is a time-sink and not the point of the project.

**Current state:** see the Progress tracker below. The active task is whatever is marked 📍. Phases 4–5 are sealed previews — do not implement or expand them until the human unlocks them after Week 3 / Phase 4 respectively.

---

## Project overview

**Goal:** ingest a company's filing history → chunk → embed → store → metadata-filtered hybrid retrieve (dense + keyword) → answer with an LLM → expose a CLI/UI, with a held-out eval set and documented system-design tradeoffs.

**Learning objectives:** (1) implement and reason about each RAG component; (2) make and justify system-design tradeoffs; (3) design a quantitative evaluation; (4) produce a clean repo + README defensible in an FDE/solutions interview.

**Corpus:** one company's 10-K annual reports across ~5–10 fiscal years. Chosen because it is a **public proxy for a private enterprise document store**, and because the documents are *templated and self-similar across time*: risk factors and MD&A reuse near-identical language year over year. That self-similarity is the point — it's a confusability that semantic search alone **cannot** resolve, which is what motivates the hybrid (metadata-filtered) upgrade and makes error analysis honest.

**The confusability axis (temporal):** same company, same section, adjacent fiscal years → near-duplicate passages. A dense-only retriever asked "what did they say about X in FY2021?" will happily return the FY2019 or FY2022 version, because they read almost the same. The disambiguating signal lives in the `fiscal_year` / `section` metadata, not the embedding.

---

## Open design questions — resolve before Station 5 (gold authoring)

These are *yours to produce* — they're interview bait and they shape the gold set. Not answered here on purpose.

1. **Three queries that genuinely need a metadata filter AND a semantic match** — where dense-only returns the right *kind* of passage from the *wrong* year/section. Aim for at least one where the filter and the semantic top-hit disagree on candidates.
   - *Shape (not one of your three):* "In FY2021, what supply-chain risks did the company identify?" → filter `fiscal_year=2021 AND section=Item1A`; semantic "supply-chain risks." Filter alone = all of 2021's risks (too broad). Semantic alone = supply-chain language from every year (wrong year).
2. **Confirm the confusable clusters for your chosen company.** The temporal axis (same section across adjacent years) is handed to you by the domain — verify it's real in your actual filings and note any second axis (e.g. sections that bleed into each other, like Risk Factors vs. MD&A forward-looking statements).

**Notes & answers:**
```
(write here)
```

---

## Stack (locked)

| Layer | Choice |
|---|---|
| Tooling | Python 3.11, uv, ruff, pytest |
| Ingest | 10-K filings → sections + `{company, fiscal_year, section}` metadata (pre-parsed EDGAR dataset / `edgar-crawler`) |
| Chunking | hand-written fixed-size **token** chunker with overlap; carries source metadata onto every chunk |
| Embeddings | `BAAI/bge-small-en-v1.5`, local + disk-cached |
| Retrieval (wk1) | brute-force cosine |
| Retrieval (wk2) | Postgres + pgvector (dense) + FTS (keyword), metadata-filtered hybrid |
| Generator | Claude Haiku 4.5 |
| Judge | Claude Sonnet (faithfulness) |
| Interface | typer CLI (wk1) → small UI (wk3) → FastAPI (phase 4) |

---

## Progress tracker

| Phase | Station | Status |
|---|---|---|
| Wk1 | 0 · Scaffold + tooling | ✅ done |
| Wk1 | 1 · Token chunker | 📍 **active** |
| Wk1 | 2 · Embedding | ⬜ |
| Wk1 | 3 · Dense retrieval (brute force) | ⬜ |
| Wk1 | 4 · Generation + rate limiting | ⬜ |
| Wk1 | 5 · Basic evaluation (retrieval gold) | ⬜ |
| Wk2 | Hybrid + storage + eval harness | 🔒 sealed |
| Wk3 | Polish, cost/latency, UI | 🔒 sealed |
| Phase 4 | API + agent loop + one legacy hook | 🔒 sealed |
| Phase 5 | Production slice + second integration | 🔒 sealed |

---

## Design decisions log  *(you fill the last two columns)*

| Component | Choice | Why (your words) | Alternatives you considered |
|---|---|---|---|
| Chunking | fixed-size token + overlap | groups together text for quicker processing and better context retrieval | |
| Chunk metadata | `{company, fiscal_year, section}` per chunk | chunked data after it was crawled/scraped by EDGAR, used the keywords and prepared for embedding | |
| Embedding model | bge-small-en-v1.5 | Smaller size, free, API stays simple | larger models, considered other small models such as BAAI/bge-base-en-v1.5 and text-embedding-3-small (which would have required an API) |
| Retrieval (wk1) | brute-force cosine | practices checking all of the chunks rather than only looking at ANN algorithms | alternative (and will be implemented down stream) would be ANN, more efficient |
| Vector store (wk2) | Postgres + pgvector + FTS | | |
| Generator | Claude Haiku 4.5 | Strong, legacy model to implement, easy to use, lower cost than implementing Opus or a more expensive model especially since we just need a quick generator | |

---

# Phase 1 — Week 1: minimal end-to-end slice  *(CURRENT PHASE)*

Goal of the week: a working `ingest → embed → retrieve → answer` pipeline on the corpus, dense-only, with a basic retrieval eval. Hybrid retrieval, the metadata filter, the faithfulness judge, and the UI are deliberately **not** in this phase.

### Station 0 — Scaffold + tooling  ✅ done

**Reflection (write 2–3 sentences):**
- The repo splits modules into "precious" (you implement) and "plumbing" (provided). Which is which, and why might that boundary matter for what you can credibly claim in an interview?

---

### Station 1 — Token chunker  📍 YOU ARE HERE

**Objective:** turn raw filing sections into overlapping fixed-size token chunks that carry their source metadata.

**Tasks:**
1. Implement `chunk_document` in `src/rag/ingest/chunker.py`.
2. Make all five tests in `tests/test_chunker.py` pass (`make test`).
3. Ensure each emitted chunk carries its `{company, fiscal_year, section}` metadata through unchanged — Week 2's hybrid filter keys on exactly these fields, so a chunk that loses its `fiscal_year` is unfilterable later.
4. Fill the *Chunking* row of the Design decisions log.

**Questions to answer (no peeking — these are interview bait):**
1. Why chunk at all instead of embedding each article whole? There are two distinct reasons — one is a hard constraint, one is about retrieval quality. Name both.
   
   a. Chunking lets us break larger texts into more manageable pieces; by doing so, we bypass the max limit that a program is able to process and we are also able to include better context across the dataset, improving retrieval and generation.
   b. When we input a corpus as one singular vector, that vector becomes the average of all of the values across the text/corpus. This means that a query about one specific fact in a given paragraph might get diluted or twisted by attention given to other facts in other paragraphs; not having a clean-cut difference between vectors therefore can reduce retrieval accuracy. 
   
2. `chunk_size` is set to 256 even though the embedder's window is 512. Why might going deliberately *smaller* than the max be the better choice — and what breaks if you go too small?

    a. Going smaller than the max is the better choice because it improves precision. Going too small, however, could lead to information being cutoff during retrieval, leading to retrieval that may not have all of the relevant information (and therefore has worse context retrieval).
   
3. What concrete failure does `overlap=0` cause on this corpus? And what goes wrong if overlap is *too* large (e.g. 200 of 256)?
   
    a. If overlap=0, then there won't be any context across each chunk; if a fact is spread across both chunks, it will be cutoff, leading to issues when retrieving certain facts. If the overlap is too large, then the chunking produce chunks with similar or near-identical information, which causes problems when retrieving information as it can bloat storage/slow retrieval but also skew results if the same content reappears over and over again.
   
4. You chunk using the embedding model's own tokenizer. What silently goes wrong if you instead chunk by character count or word count?
   
    a. Depending on the size of the corpus, the context could be totally different and the requirements also totally different. So, the tokens that it produces for a given set of text, character count, or word count could be too long and then truncated without the user knowing. 

**Definition of done:** tests green · all four questions answered in Notes · metadata propagates onto every chunk · Design-log row filled · committed as `feat: token chunker`.

**Notes & answers:**
```
(write here)
```

---

### Station 2 — Embedding

**Objective:** turn chunks into vectors, cached to disk.

**Tasks:**
1. Read `src/rag/embed/embedder.py` (provided). Run `make index` once the chunker works — confirm vectors land in `.cache/`.
2. Fill the *Embedding model* row of the Design decisions log.

**Questions to answer:**
1. What does a dense embedding give you that keyword matching cannot? And what can keyword matching do that embeddings are bad at? (Hold onto the second half — it's the whole reason hybrid retrieval exists. On this corpus, think about exact tokens like a specific fiscal year, a dollar figure, or a form-item number.)

    a. A dense embedding gives us better context retrieval than keyword matching. It allows us to see the nearest neighbors to a query, understanding the surrounding geometry rather than just the singular answer, letting us build a better response. This is beneficial for answering more complex questions that require a broader understanding of the data rather than fetching specific answers; on the other hand, using keyword matching is beneficial for finding specific points in the data that might appear near identical across the KB.

2. Why `bge-small-en-v1.5` rather than a larger open model or a hosted API like `text-embedding-3-large`? List the axes of that tradeoff.

    a. For cost and latency reasons. This can also be run locally; however, the plan is to expand to a larger model to practice later on. The other benefit here is that there is no API dependency. A larger, legacy model would require tokens to be purchased as well as an API to be configured. The downside is that this smaller model may cause some temporal confusion on these near-duplicate yearly filings; however, for this small-scale project, we will assume this won't be a major issue and will revisit this if necessary.

3. The embedder L2-normalizes vectors. What does that let you simplify at search time, and why?

    a. By normalizing the vector, all of the values get fitted into the same unit length (norm=1). This allows for quicker comparison between values. 

4. The code prepends an instruction to *queries* but not *passages*. Why the asymmetry?

    a. If we prepend the instruction to passages, it will convolute the results. By putting the instruction to query, it puts the model in query mode before searching through indexed passages. 

**Definition of done:** index builds · questions answered · log row filled · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 3 — Dense retrieval (brute force)

**Objective:** given a query vector, return the top-k chunks. (Dense-only this week — the metadata filter arrives properly in Week 2.)

**Tasks:**
1. Implement `DenseIndex.search` in `src/rag/retrieve/dense.py`.
2. Sanity-check: ask 3–4 questions you know the answer to; do the right chunks surface? Try one question whose answer differs by year (e.g. a figure that changes annually) and watch whether dense-only grabs the wrong year — this is the failure the Week 2 filter fixes, and worth seeing with your own eyes now.

**Questions to answer:**
1. What is cosine similarity measuring geometrically, and why is it the right choice for these (normalized) vectors?

    a. Cosine similarity is measuring the similarity of direction between two vectorized chunks in a geometric space. This is the right choice for normalized vectors because it tells the model what context is relevant when pulling data to produce a response. 

2. Brute-force search is O(?) in the number of chunks. At what corpus size does that stop being acceptable, and what *family* of algorithm/structure replaces it? (You don't need to implement it — just name it and the tradeoff it makes.) Note: for a single company's filings the corpus is modest, so the Week 2 move to pgvector is motivated less by raw speed and more by metadata filtering, keyword fusion, and persistence — be ready to say that out loud.

    a. Brute-force search stops being acceptable when the corpus size scales to a significantly large size because it takes too long to run. Approximate nearest neighbor and semantic vector search could both replace brute-force search, which only explore the nearest neighbors to the found semantic vector index rather than searching through the entire corpus. 

3. `top_k` is a knob. What goes wrong if it's too small? Too large? How does its best value interact with your chunk size?

    a. If top_k is too small, then the retrieval could miss some relevant information that is just outside of the scope of the top_k set by us; if it's too large, it could retrieve information that isn't contextually relevant and impact the generated response. Its best value interacts with chunk size depending on what our goal is; if we want higher precision, we would have a larger top_k, meaning we retrieve more chunks, with each chunk being smaller so that they're each more specific to the query being asked. A larger chunk size and smaller top_k would be better for a more summarization-based approach, allowing us to have a broader part of the text pulled but less specific information. 

**Definition of done:** retrieval returns sensible chunks · questions answered · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 4 — Generation + rate limiting

**Objective:** pass retrieved context to Claude Haiku 4.5 and return a grounded answer, with robust retries. *(Confirm the current Anthropic SDK call + error types with the chat before implementing — don't let it go stale.)*

**Tasks:**
1. Implement `generate` in `src/rag/generate/client.py`: build the prompt (provided builder), call the API, retry on transient failures.
2. Run `make ask` end-to-end.
3. Fill the *Generator* row of the Design decisions log.

**Questions to answer:**
1. Which API failures are worth *retrying* and which should fail fast? Why retry some and not others?

    a. API failures that are worth retrying are RateLimitError, 
        APIConnectionError,
        APITimeoutError, 
        OverloadedError,
        because they are not necessarily the fault of the user; however, a bad authentication should fail fast rather than retrying since that just means the user is not authenticated to use the platform. 

2. Why exponential backoff *with jitter*, rather than a fixed delay or plain exponential? What specifically does jitter prevent?

    a. Using jitter prevents the thundering herd problem, which means when multiple users are timed out but retry again and again at the same time since they are spaced out equally. When we implement jitter, it spaces out the retries, stressing the system less. 

3. What's the failure mode if you don't cap the number of retries?

    a. A cascading architectural crises; a single issue can cascade and break the entire system by overloading it. We are avoiding infiite retries which would lead to hung requests, wasted spend from tokens, and amplified load on a struggling API. 

4. Estimate your cost-per-query: take your typical input tokens (system + context + question) and output tokens, and compute the Haiku cost. Write the number and the assumptions. (This becomes a README section.)

    a. $0.003/query. Each input is roughly ~1500 tokens, the output is roughly ~250 tokens. The math would be: cost ≈ (1500/1e6)*1 + (250/1e6)*5 ≈ $0.0015 + $0.00125 ≈ $0.003/query

**Definition of done:** end-to-end answer works · retries handle a forced failure · questions answered · log row filled · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 5 — Basic evaluation (retrieval gold)

**Objective:** measure *retrieval* quality on a small gold set. (Faithfulness scoring is Week 2 — this week is retrieval only.)

**Tasks:**
1. Author ~12–15 gold Q/A pairs over the corpus → `data/qa/gold.jsonl`. Each item records the **question** and its **gold context**: the `(fiscal_year, section, chunk_id(s))` that answers it. You verify the gold by *reading the filing* — no domain expertise required, which is the whole reason this eval model works in an unfamiliar corpus. (Scales to ~25 in Week 2.)
2. Implement `hit_rate_at_k` and `mrr_at_k` in `src/rag/eval/metrics.py`.
3. Run them over your gold set; record the numbers.

    a. After running over the gold set, the hit_rate@5 is 0.385 (5/13 queries). The mrr@5 is 0.179. Often, the right topic was selected but from the wrong year; what this means is that the current RAG is struggling with the similar data in the corpus since over each year the data changes slightly. This is relevant for our next step, which would be implementing a hybrid search.

**Questions to answer:**
1. What's the difference between evaluating *retrieval* (did the right passage surface?) and *faithfulness* (did the answer stay grounded in what surfaced?)? Why measure them separately rather than just grading final answers for correctness?

    a. The difference between evaluating retrieval and faithfulness is that retrieval is can be measured directly by a value, meaning whether or not it is correct is binary: it's either yes or no. Meanwhile, faithfulness is something that is a bit harder to evaluate as it is more content based, meaning you need some sort of a 'judge' to determine its correctness (either through a human or an LLM-as-judge). 

2. Define hit-rate@k and MRR in your own words. What does each one *fail* to capture?

    a. Hit-rate@k refers to whether or not the pulled chunks have a relevant item given the query. It essentially asks, out of the number of queries, how many resulted in a relevant document being pulled; one thing that this fails to capture is whether the system fails to capture the relevant information because of insufficient data or because it is a faulty model. It also doesn't provide any kind of ranking.
    b. MRR measures the average position of the first relevant item. If the first relevant item shows up in rank position 3, then it is given a score of 0.333. This tells us how quickly relevant items are picked up, telling us the speed of the program and is useful when a search tool needs to find one specific piece of information rather than a broader context.

3. How will you decide a retrieved chunk counts as "relevant" for a given gold question? On this corpus the sharp case is the year: if the right passage exists in three fiscal years, does retrieving the *wrong* year's near-identical passage count as a hit? What's the failure mode of whichever rule you pick?

    a. I will decide if a retrieved chunk counts as 'relevant' by its content and closeness to the desired year. If it contains relevant keywords, and fits the given year, then it can be deemed relevant; additionally, depending on the query, the question might ask for adjacent years in order to make a relevant comparison. This convolutes things but demonstrates the importance of having an evaluation harness that measures nearest neighbor strength and not just direct, uniform binary comparison of 'correct' or 'incorrect'. The failure mode would be dependent on the importance of the query; however, it would revolve around the fetched top_k results not containing close enough years, relevant keywords, etc.

4. What makes a *good* gold question here? (Hint: one where asking the same thing about a different fiscal year yields a different answer, so retrieval is forced to use the year — a question any year could answer tests nothing.)

    a. A good gold question here would have to do with specific yearly reports, such as quantities that fluctuate year-over-year, or anything that might appear structurally similar across years but differ in valuable content. 

**Definition of done:** gold set exists · metrics implemented and run · numbers recorded · questions answered · committed. **→ Week 1 complete; ask the chat to unlock Phase 2.**

**Notes & answers:**
```
(write here)
```

---

# Phase 2 — Week 2: hybrid retrieval + storage + eval harness  🔒 SEALED

Unlocks when Week 1 is complete. Preview only: move off brute-force into Postgres + pgvector; promote the chunk metadata to indexed SQL columns; add keyword retrieval (FTS) and fuse it with dense; and — the headline — add the **metadata filter** (`WHERE fiscal_year = … AND section = …`) that resolves the temporal confusability dense search can't. Then build the full evaluation harness, including the **faithfulness LLM-judge**. Detailed tasks and questions appear when you reach it.

# Phase 3 — Week 3: polish, cost/latency, UI  🔒 SEALED

Unlocks after Week 2. Preview only: small UI, measured latency and cost-per-query, finalized README + error analysis.

---

# Phase 4 — API + agent loop + one legacy hook  🔒 SEALED

Unlocks when Week 3 is complete. **Do not start early** — this phase assumes hybrid retrieval, faithfulness eval, and a working UI/CLI are already defensible.

**North star:** turn the RAG pipeline into a thin **live service** with an **explicit, framework-free agent loop** and **one** legacy integration story you can demo end-to-end in an interview. Deliberately small — no generic agent platform, no second vector DB, no auth layer yet.

**Hard rules carry forward:**
1. **No orchestration frameworks.** No LangGraph, CrewAI, AutoGen, LangChain agents. The loop is a plain Python `while` / state machine you can whiteboard.
2. **Thin API.** FastAPI routes call existing `rag` modules — no business logic duplicated in route handlers.
3. **One integration.** Pick a single legacy touchpoint (see Station 2). A mocked backend is fine if the adapter interface is real.

**Stack additions (phase 4 only):** FastAPI · `uvicorn` · optional `httpx` for the legacy adapter. Postgres from Week 2 remains the store — do not introduce a separate vector DB here.

### Station 0 — FastAPI wrapper

**Objective:** expose the existing ask pipeline over HTTP without changing retrieval or generation behavior.

**Tasks:**
1. Add `src/rag/api/` (or `scripts/serve.py` + thin router module) with `POST /query` (question in → grounded answer + cited chunks out) and `GET /health`.
2. Wire routes to the same code path `make ask` uses — one implementation, two entry points.
3. Log each query to Postgres (question, retrieved chunk ids, latency ms, model) — reuse the Week 2 DB connection pattern.
4. Add `make serve` to run locally.

**Questions to answer:**
1. Why keep the API layer thin instead of putting retrieval logic in route handlers?
2. What belongs in the response body vs. what should stay server-side only (e.g. full prompt, raw embeddings)?
3. What breaks if CLI and API drift to two different code paths?

**Definition of done:** `curl POST /query` returns the same answer as `make ask` for the same question · queries logged · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 1 — Explicit agent loop + tool registry

**Objective:** a minimal multi-step workflow — plan → tool call(s) → generate — with no hidden framework magic.

**Tasks:**
1. Define 2–3 tools as plain Python callables with typed inputs/outputs, e.g. `search_filings(query, fiscal_year?, section?)`, `list_available_years()`, `compare_passages(year_a, year_b, topic)` — each wraps existing retrieval/SQL, not new logic.
2. Implement a simple loop in `src/rag/agent/loop.py`: LLM receives tool schemas → emits structured JSON (tool name + args) → you execute → feed results back → repeat until `finish` or max steps (cap at ~5).
3. Add `POST /agent/query` that runs the loop and returns the final answer plus a **trace** (which tools fired, in what order).
4. Sanity-check: one question that needs a metadata filter *and* a semantic search should route through `search_filings` with the right args — not brute-force retrieve everything.

**Questions to answer:**
1. Why cap max agent steps, and what failure mode does an uncapped loop have?
2. When is a deterministic router (if year in question → always filter) better than letting the LLM choose tools every time?
3. What goes in the trace for debugging vs. what you would never expose to an end user?

**Definition of done:** agent endpoint completes at least one multi-step query · trace is inspectable · no orchestration framework in `pyproject.toml` · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 2 — One legacy hook

**Objective:** one credible "connects to the outside world" story — ingest trigger or metadata enrichment from a system that isn't your corpus files.

**Tasks:**
1. Pick **one** integration (choose before coding — write the choice in the Design decisions log):
   - **Ingest webhook:** `POST /ingest/filing` accepts a new filing payload (or file path) → runs existing ingest → chunk → embed → upsert into Postgres. Simulates SFTP drop or EDGAR poll.
   - **Metadata adapter:** a read-only client to a mock ERP that returns `{company, fiscal_year, active_sections}` the agent uses to disambiguate before retrieval. Simulates SAP/Oracle master data.
2. Implement the adapter behind a small interface (`LegacySource` or similar) so the rest of the system depends on the interface, not the mock.
3. Demo path: external event → adapter/webhook → index update (or metadata fetch) → agent query returns answer using fresh data.

**Questions to answer:**
1. Why interface + mock rather than hard-coding the mock behavior into the agent loop?
2. What idempotency concern does the ingest webhook have (same filing submitted twice)?
3. How would you swap the mock for a real system without rewriting the agent or API?

**Definition of done:** one end-to-end demo script or README section · adapter interface exists · Design-log row filled · committed. **→ Phase 4 complete; ask the chat to unlock Phase 5.**

**Notes & answers:**
```
(write here)
```

---

# Phase 5 — Production slice + second integration  🔒 SEALED

Unlocks when Phase 4 is complete. **Preview only** — detail expands when you reach it. This is the longer-horizon goal; do not scope-creep into it during Weeks 1–3 or Phase 4.

**Intent:** move from "portfolio demo" to "something you could plausibly deploy for a small internal team" — still one repo, still explicit code, still no agent framework.

Likely themes (pick a subset when unlocked — not all at once):
- **Async indexing:** background job queue for re-index when filings arrive (e.g. `arq` or a simple Postgres-backed job table — avoid Celery unless you have a reason).
- **Auth + tenancy:** API key or JWT; separate corpora per tenant if you want a stronger enterprise story.
- **Observability:** structured logs, query/error dashboards, cost-per-query aggregation from Phase 4 logs.
- **Second legacy adapter:** a different system type (e.g. ticket queue, CRM note) to show the adapter pattern generalizes — reuses Phase 4's interface, not a rewrite.
- **Deployment story:** Docker Compose (Postgres + API + optional UI) or a single-cloud deploy doc with measured cold-start and p95 latency.
- **Optional vector-store comparison:** benchmark pgvector vs. one managed store (Pinecone/Qdrant) on *your* eval set — document when you'd switch and when you wouldn't.

**Explicit non-goals for Phase 5:** multi-region HA, custom embedding fine-tuning, a general-purpose agent SDK, or supporting every legacy protocol. Stop when one deployment + one second integration is demoable.

---

## Run

```bash
make install            # uv venv + editable install (.[dev])
cp .env.example .env     # add ANTHROPIC_API_KEY
make test                # run tests (red until you implement the stubs)
make index               # ingest -> chunk -> embed -> persist
make ask                 # query end-to-end
```

## Progress log

- *(date)* — Scaffolded repo + tooling; locked stack. Active: Station 1 (chunker).
- *(date)* — Pivoted corpus: JDM / cognitive biases → **one company's SEC 10-K filings across fiscal years** (internal-document-assistant archetype; SEC as public proxy for a private corpus). Eval model set to **retrieval-gold + faithfulness**. Confusability axis is now temporal (same section, adjacent years). Chunker work (Station 1) carries over unchanged; ingestion gains section/metadata parsing; Station 5 reframed to retrieval gold.
