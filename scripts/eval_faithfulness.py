"""Retrieval + generation + faithfulness judge. Usage: make eval-faithful

For each gold item: hybrid retrieve (with metadata filter) → Haiku answer → Sonnet judge.
Absence items (gold["absence"] == true) still run; a good system says "not in context"
and the judge should mark that FAITHFUL when the context lacks the topic.
"""
from __future__ import annotations

import pickle

from rag.config import settings
from rag.embed.embedder import Embedder
from rag.eval.judge import judge_faithfulness
from rag.generate.client import generate
from rag.retrieve.hybrid import HybridIndex
from rag.retrieve.keyword import KeywordIndex
from rag.retrieve.pg_dense import PgDenseIndex
from eval_retrieval import load_gold


def main() -> None:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL required for hybrid+filter eval")

    gold = load_gold(settings.qa_path)
    with open(settings.cache_dir / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    hybrid = HybridIndex(
        PgDenseIndex.from_dsn(settings.database_url),
        KeywordIndex(chunks),
    )
    embedder = Embedder(settings.embed_model, settings.cache_dir)
    k = settings.top_k

    n_faithful = 0
    print(f"gold items: {len(gold)}\n")

    for item in gold:
        question = item["question"]
        qvec = embedder.encode_query(question)
        hits = hybrid.search(
            question,
            qvec,
            k,
            fiscal_year=item["fiscal_year"],
            section=item["section"],
        )
        ctx = [c for _, c in hits]
        answer = generate(question, ctx)
        result = judge_faithfulness(question, answer, ctx)

        n_faithful += int(result.faithful)
        label = "FAITHFUL" if result.faithful else "UNFAITHFUL"
        absence = " [absence]" if item.get("absence") else ""
        print(f"--- FY{item['fiscal_year']} {item['section']}{absence} ---")
        print(f"Q: {question}")
        print(f"A: {answer[:200]}{'...' if len(answer) > 200 else ''}")
        print(f"Judge: {label} — {result.reason}")
        print()

    rate = n_faithful / len(gold) if gold else 0.0
    print(f"faithfulness: {n_faithful}/{len(gold)} = {rate:.3f}")


if __name__ == "__main__":
    main()
