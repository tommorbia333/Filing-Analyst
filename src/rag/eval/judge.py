"""Faithfulness LLM-as-judge (Claude Sonnet).

Scores whether the *generated answer* is grounded in the *retrieved context*
(not whether it matches the filing as a finance expert).
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

import anthropic
from anthropic import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OverloadedError,
    PermissionDeniedError,
    RateLimitError,
)

from rag.config import settings
from rag.ingest.chunker import Chunk

MAX_RETRIES = 5
BASE_DELAY = 1.0

JUDGE_SYSTEM = (
    "You are a strict faithfulness judge for a RAG system. "
    "Decide whether the ANSWER is fully supported by the CONTEXT. "
    "Ignore whether the answer is factually correct in the real world — "
    "only whether it is grounded in the provided context. "
    "If the answer correctly says the context does not contain the information, "
    "that is FAITHFUL. "
    "If the answer adds facts, numbers, or claims not present in the context, "
    "that is UNFAITHFUL. "
    "Respond with exactly two lines:\n"
    "LABEL: FAITHFUL|UNFAITHFUL\n"
    "REASON: <one short sentence>"
)


@dataclass(frozen=True)
class JudgeResult:
    faithful: bool
    reason: str
    raw: str


def _build_judge_prompt(question: str, answer: str, chunks: list[Chunk]) -> str:
    blocks = [f"[{i}] (FY{c.fiscal_year} {c.section})\n{c.text}" for i, c in enumerate(chunks, 1)]
    context = "\n\n".join(blocks)
    return (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER: {answer}\n\n"
        "Judge faithfulness."
    )


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (
        RateLimitError,
        OverloadedError,
        APIConnectionError,
        APITimeoutError,
    ))


def _parse_judge_response(raw: str) -> JudgeResult:
    label: str | None = None
    reason = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("LABEL:"):
            label = line.split(":", 1)[1].strip().upper()
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    if label not in ("FAITHFUL", "UNFAITHFUL"):
        return JudgeResult(faithful=False, reason="parse_error", raw=raw)
    return JudgeResult(faithful=(label == "FAITHFUL"), reason=reason or "no reason", raw=raw)


def judge_faithfulness(
    question: str,
    answer: str,
    chunks: list[Chunk],
    model: str | None = None,
) -> JudgeResult:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    user_prompt = _build_judge_prompt(question, answer, chunks)
    model = model or settings.judge_model

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=256,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text
            return _parse_judge_response(raw)

        except (AuthenticationError, BadRequestError, PermissionDeniedError):
            raise

        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise

            delay = BASE_DELAY * 2**attempt + random.uniform(0, 1)
            time.sleep(delay)

    raise RuntimeError("judge_faithfulness: exhausted retries without response")
