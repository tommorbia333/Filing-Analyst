"""Claude Haiku generation with retry/backoff on rate limits and transient errors."""
from __future__ import annotations

import random
import time

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
from rag.generate.prompt import SYSTEM, build_user_prompt
from rag.ingest.chunker import Chunk

MAX_RETRIES = 5
BASE_DELAY = 1.0


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (
        RateLimitError,
        OverloadedError,
        APIConnectionError,
        APITimeoutError,
    ))


def generate(question: str, chunks: list[Chunk], model: str | None = None) -> str:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    user_prompt = build_user_prompt(question, chunks)
    model = model or settings.gen_model

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=SYSTEM,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text

        except (AuthenticationError, BadRequestError, PermissionDeniedError):
            raise

        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise

            delay = BASE_DELAY * 2 ** attempt + random.uniform(0, 1)
            time.sleep(delay)
