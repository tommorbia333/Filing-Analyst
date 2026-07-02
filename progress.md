# RAG Capstone — Project Handbook

> This file is three things at once:
> 1. **A progress tracker** — what's done, what's active, what's sealed.
> 2. **An assignment handbook** — each station has tasks and *questions you answer yourself*. No answers are written here on purpose.
> 3. **A context handoff** — enough for a Cursor agent (or future-you) to pick up without re-explaining the project.
>
> Built end-to-end with **no orchestration frameworks** (no LangChain / LlamaIndex). Every component is explicit and defensible in an interview.

---

## How to use this handbook

- Work **top to bottom**. Do not open 🔒 sealed phases early — they're sealed so new terminology arrives only when you're ready for it.
- At each station: do the **Tasks**, then write your own answers to the **Questions** in the *Notes & answers* space. Fill the matching row in the **Design decisions log**.
- A station is done only when its **Definition of done** is met. Then advance.
- Use **Cursor** for implementation help and **this chat** for mentoring, quizzing, and unlocking the next phase. When a phase completes, the chat regenerates this README with the next phase expanded.

---

## For AI coding agents (Cursor) — read this first

**Project:** A local, scrappy, end-to-end RAG system over a judgment-&-decision-making corpus, with a quantitative evaluation harness. The human (Tom) is building this as a portfolio piece to defend in forward-deployed / solutions / applied-AI interviews.

**Hard rules — do not violate:**
1. **No high-level RAG frameworks.** No LangChain, no LlamaIndex, no framework that hides retrieval/chunking/orchestration. Thin libraries only (sentence-transformers, numpy, anthropic, psycopg, rank-bm25, typer).
2. **Low abstraction.** Prefer explicit, readable code the human can explain line-by-line over clever indirection.
3. **This is a learning project.** For the *precious* components below, **do not hand over finished solutions.** Review the human's code, point out bugs, ask leading questions, explain tradeoffs — but let them write it. You may write *plumbing* freely.
4. **Never answer the handbook Questions for the human.** If asked, coach toward the answer; don't state it.

**Precious (human implements, you coach):** `ingest/chunker.py`, `retrieve/dense.py`, `generate/client.py` (retry/backoff), `eval/metrics.py`.
**Plumbing (you may write freely):** `ingest/loader.py`, `embed/embedder.py`, `generate/prompt.py`, `scripts/`.

**Stack (locked):** Python 3.11 · `uv` · `ruff` (line length 100; rules E,F,I,UP,B) · `pytest` (`pythonpath=src`). Embeddings `BAAI/bge-small-en-v1.5` (local, cached, normalized). Retrieval: brute-force cosine (Week 1) → Postgres + pgvector + full-text search (Week 2). Generator: Claude Haiku 4.5. Judge: Claude Sonnet 4.6. Config lives in `src/rag/config.py`. One commit per component.

**Current state:** see the Progress tracker below. The active task is whatever is marked 📍.

---

## Project overview

**Goal:** ingest a corpus → chunk → embed → store → hybrid retrieve (dense + keyword) → answer with an LLM → expose a CLI/UI, with a held-out eval set and documented system-design tradeoffs.

**Learning objectives:** (1) implement and reason about each RAG component; (2) make and justify system-design tradeoffs; (3) design a quantitative evaluation; (4) produce a clean repo + README defensible in an FDE/solutions interview.

**Corpus:** ~30–50 Wikipedia articles on judgment & decision-making / cognitive biases. Chosen because the domain is familiar (fast, trustworthy gold Q/A) and full of *confusable* concepts that stress retrieval — good for error analysis and for motivating the hybrid upgrade.

---

## Stack (locked)

| Layer | Choice |
|---|---|
| Tooling | Python 3.11, uv, ruff, pytest |
| Ingest | plain text / markdown (+ optional pypdf) |
| Chunking | hand-written fixed-size **token** chunker with overlap |
| Embeddings | `BAAI/bge-small-en-v1.5`, local + disk-cached |
| Retrieval (wk1) | brute-force cosine |
| Retrieval (wk2) | Postgres + pgvector (dense) + FTS (keyword), hybrid |
| Generator | Claude Haiku 4.5 |
| Judge | Claude Sonnet 4.6 |
| Interface | typer CLI (wk1) → small UI (wk3) |

---

## Progress tracker

| Phase | Station | Status |
|---|---|---|
| Wk1 | 0 · Scaffold + tooling | ✅ done |
| Wk1 | 1 · Token chunker | 📍 **active** |
| Wk1 | 2 · Embedding | ⬜ |
| Wk1 | 3 · Dense retrieval (brute force) | ⬜ |
| Wk1 | 4 · Generation + rate limiting | ⬜ |
| Wk1 | 5 · Basic evaluation | ⬜ |
| Wk2 | Hybrid + storage + eval harness | 🔒 sealed |
| Wk3 | Polish, cost/latency, UI | 🔒 sealed |

---

## Design decisions log  *(you fill the last two columns)*

| Component | Choice | Why (your words) | Alternatives you considered |
|---|---|---|---|
| Chunking | fixed-size token + overlap | groups together text for quicker processing and better context retrieval | |
| Embedding model | bge-small-en-v1.5 | | |
| Retrieval (wk1) | brute-force cosine | | |
| Vector store (wk2) | Postgres + pgvector + FTS | | |
| Generator | Claude Haiku 4.5 | | |

---

# Phase 1 — Week 1: minimal end-to-end slice  *(CURRENT PHASE)*

Goal of the week: a working `ingest → embed → retrieve → answer` pipeline on the corpus, dense-only, with a basic eval. Hybrid retrieval, the full eval harness, and the UI are deliberately **not** in this phase.

### Station 0 — Scaffold + tooling  ✅ done

**Reflection (write 2–3 sentences):**
- The repo splits modules into "precious" (you implement) and "plumbing" (provided). Which is which, and why might that boundary matter for what you can credibly claim in an interview?

---

### Station 1 — Token chunker  📍 YOU ARE HERE

**Objective:** turn raw documents into overlapping fixed-size token chunks.

**Tasks:**
1. Implement `chunk_document` in `src/rag/ingest/chunker.py`.
2. Make all five tests in `tests/test_chunker.py` pass (`make test`).
3. Fill the *Chunking* row of the Design decisions log.

**Questions to answer (no peeking — these are interview bait):**
1. Why chunk at all instead of embedding each article whole? There are two distinct reasons — one is a hard constraint, one is about retrieval quality. Name both.
    a. Chunking lets us break larger texts into more manageable pieces; by doing so, we bypass the max limit that a program is able to process and we are also able to include better context across the dataset, improving retrieval and generation.
2. `chunk_size` is set to 256 even though the embedder's window is 512. Why might going deliberately *smaller* than the max be the better choice — and what breaks if you go too small?
    a. Going smaller than the max is the better choice because it improves precision. Going too small, however, could lead to the chunks including too precise of information that doesn't generalize well across the dataset (and therefore has worse context retrieval).  
3. What concrete failure does `overlap=0` cause on this corpus? And what goes wrong if overlap is *too* large (e.g. 200 of 256)?
    a. If overlap=0, then there won't be any context across each chunk. If the overlap is too large, then the chunking would reiterate over the same chunk over and over, or fail because it can't pull information larger than the context window. 
4. You chunk using the embedding model's own tokenizer. What silently goes wrong if you instead chunk by character count or word count?
    a. Depending on the size of the corpus, the context could be totally different and the requirements also totally different. So, the tokens that it produces for a given set of text, character count, or word count could be too long and then truncated without the user knowing. 

**Definition of done:** tests green · all four questions answered in Notes · Design-log row filled · committed as `feat: token chunker`.

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
1. What does a dense embedding give you that keyword matching cannot? And what can keyword matching do that embeddings are bad at? (Hold onto the second half — it's the whole reason hybrid retrieval exists.)
2. Why `bge-small-en-v1.5` rather than a larger open model or a hosted API like `text-embedding-3-large`? List the axes of that tradeoff.
3. The embedder L2-normalizes vectors. What does that let you simplify at search time, and why?
4. The code prepends an instruction to *queries* but not *passages*. Why the asymmetry?

**Definition of done:** index builds · questions answered · log row filled · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 3 — Dense retrieval (brute force)

**Objective:** given a query vector, return the top-k chunks.

**Tasks:**
1. Implement `DenseIndex.search` in `src/rag/retrieve/dense.py`.
2. Sanity-check: ask 3–4 questions you know the answer to; do the right chunks surface?

**Questions to answer:**
1. What is cosine similarity measuring geometrically, and why is it the right choice for these (normalized) vectors?
2. Brute-force search is O(?) in the number of chunks. At what corpus size does that stop being acceptable, and what *family* of algorithm/structure replaces it? (You don't need to implement it — just name it and the tradeoff it makes.)
3. `top_k` is a knob. What goes wrong if it's too small? Too large? How does its best value interact with your chunk size?

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
2. Why exponential backoff *with jitter*, rather than a fixed delay or plain exponential? What specifically does jitter prevent?
3. What's the failure mode if you don't cap the number of retries?
4. Estimate your cost-per-query: take your typical input tokens (system + context + question) and output tokens, and compute the Haiku cost. Write the number and the assumptions. (This becomes a README section.)

**Definition of done:** end-to-end answer works · retries handle a forced failure · questions answered · log row filled · committed.

**Notes & answers:**
```
(write here)
```

---

### Station 5 — Basic evaluation

**Objective:** measure retrieval quality on a small gold set.

**Tasks:**
1. Author ~12–15 gold Q/A pairs over the corpus → `data/qa/gold.jsonl` (scales to ~25 in Week 2).
2. Implement `hit_rate_at_k` and `mrr_at_k` in `src/rag/eval/metrics.py`.
3. Run them over your gold set; record the numbers.

**Questions to answer:**
1. What's the difference between evaluating *retrieval* and evaluating *answer quality*? Why measure them separately rather than just grading final answers?
2. Define hit-rate@k and MRR in your own words. What does each one *fail* to capture?
3. How will you decide a retrieved chunk counts as "relevant" for a given gold question? What are the failure modes of that labeling rule?

**Definition of done:** gold set exists · metrics implemented and run · numbers recorded · questions answered · committed. **→ Week 1 complete; ask the chat to unlock Phase 2.**

**Notes & answers:**
```
(write here)
```

---

# Phase 2 — Week 2: hybrid retrieval + storage + eval harness  🔒 SEALED

Unlocks when Week 1 is complete. Preview only: move off brute-force into a real store, add keyword retrieval and fuse it with dense, and build the full evaluation harness (incl. LLM-as-judge). Detailed tasks and questions appear when you reach it.

# Phase 3 — Week 3: polish, cost/latency, UI  🔒 SEALED

Unlocks after Week 2. Preview only: small UI, measured latency and cost-per-query, finalized README + error analysis.

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

- *(date)* — Scaffolded repo + tooling; locked stack; corpus = JDM / cognitive biases. Active: Station 1 (chunker).
