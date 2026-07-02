"""Claude Haiku 4.5 generation with retry/backoff.

YOUR TASK: implement generate().
Rate-limit reality (a stated learning objective): the API can return 429
(rate limit) and 529 (overloaded). Wrap the call in exponential backoff with
jitter, cap retries (~5), and re-raise on non-retryable errors (e.g. 400/401).
We'll confirm the exact SDK call + error types against the *current* Anthropic
SDK when we implement this together, so it doesn't go stale.
"""

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
BASE_DELAY = 1.0  # seconds


def _is_retryable(exc: Exception) -> bool:
    # BLANK A: which exception types get retried?
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
            # print(response.usage)  # remove after testing   
            # BLANK B: extract text from response
            return response.content[0].text

        except (AuthenticationError, BadRequestError, PermissionDeniedError):
            raise  # fail fast — bad key, bad request, no permission

        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise

            # BLANK C: exponential backoff with jitter
            delay = BASE_DELAY * 2 ** attempt + random.uniform(0, 1)    
            time.sleep(delay)