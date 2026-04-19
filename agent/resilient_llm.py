"""
Broader retry policy for OpenAI-compatible endpoints.

smolagents.ApiModel only retries rate-limit errors. Gateways often return 502/503 or
non-JSON bodies that surface as JSON decode errors — those previously failed on the first try.
"""

from __future__ import annotations

import logging
from typing import Any

from smolagents import OpenAIServerModel
from smolagents.models import is_rate_limit_error
from smolagents.utils import Retrying

import config

logger = logging.getLogger(__name__)


def is_transient_llm_error(exc: BaseException) -> bool:
    """True when the failure is likely transient and worth retrying."""
    if is_rate_limit_error(exc):
        return True

    msg = str(exc).lower()

    # Bad gateway / overloaded / empty proxy responses (often break JSON parsing)
    if any(
        s in msg
        for s in (
            "502",
            "503",
            "504",
            "408",
            "bad gateway",
            "gateway timeout",
            "service unavailable",
            "expecting value",
            "json decode",
            "unexpected end of data",
            "unexpected eof",
            "connection reset",
            "broken pipe",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "try again",
            "overload",
        )
    ):
        return True

    try:
        import openai

        if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
            return True
        if isinstance(exc, openai.APIStatusError):
            code = getattr(exc, "status_code", None) or 0
            return code in (408, 429, 500, 502, 503, 504)
    except Exception:
        pass

    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                httpx.RemoteProtocolError,
            ),
        ):
            return True
    except ImportError:
        pass

    return False


class ResilientOpenAIServerModel(OpenAIServerModel):
    """
    Same as OpenAIServerModel but retries common transient HTTP and transport failures,
    not only 429 rate limits.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        attempts = getattr(config, "MODEL_RETRY_MAX_ATTEMPTS", 5)
        wait = getattr(config, "MODEL_RETRY_WAIT_SEC", 2.0)
        self.retryer = Retrying(
            max_attempts=int(attempts),
            wait_seconds=float(wait),
            exponential_base=2.0,
            jitter=True,
            retry_predicate=is_transient_llm_error,
            reraise=True,
            before_sleep_logger=(logger, logging.INFO),
            after_logger=(logger, logging.INFO),
        )
