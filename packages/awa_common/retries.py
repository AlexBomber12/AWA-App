from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import structlog
from structlog import contextvars as structlog_contextvars
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_exponential_jitter,
)
from typing_extensions import ParamSpec

from awa_common.metrics import record_retry_attempt, record_retry_sleep

logger = structlog.get_logger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class RetryConfig:
    stop_after: int = 5
    base_wait_s: float = 0.5
    max_wait_s: float = 10.0
    jitter: bool = True
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError, OSError)
    operation: str = "retry"
    wait: Any | None = None
    before_sleep: Callable[[RetryCallState], None] | None = None


def _wait_strategy(cfg: RetryConfig) -> Any:
    if cfg.wait is not None:
        return cfg.wait
    base = max(cfg.base_wait_s, 0.01)
    maximum = max(cfg.max_wait_s, base)
    if cfg.jitter:
        return wait_exponential_jitter(exp_base=base, max=maximum)
    return wait_exponential(multiplier=base, max=maximum)


def _before_sleep(cfg: RetryConfig, retry_state: RetryCallState) -> None:
    sleep = float(retry_state.next_action.sleep) if retry_state.next_action else 0.0
    error_type: str | None = None
    if retry_state.outcome is not None and retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        if exc is not None:
            error_type = exc.__class__.__name__
    ctx = structlog_contextvars.get_contextvars()
    request_id = ctx.get("request_id")
    logger.warning(
        "retry.scheduled",
        operation=cfg.operation,
        attempt=retry_state.attempt_number,
        sleep=sleep,
        error_type=error_type,
        request_id=request_id,
    )
    record_retry_attempt(cfg.operation)
    record_retry_sleep(cfg.operation, sleep)
    if cfg.before_sleep is not None:
        cfg.before_sleep(retry_state)


def aretry(cfg: RetryConfig) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Return a decorator that wraps async callables with a shared retry policy."""

    def _decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            retrying = AsyncRetrying(
                stop=stop_after_attempt(max(1, cfg.stop_after)),
                wait=_wait_strategy(cfg),
                retry=retry_if_exception_type(cfg.retry_on),
                reraise=True,
                before_sleep=lambda state: _before_sleep(cfg, state),
            )
            async for attempt in retrying:
                with attempt:
                    return await func(*args, **kwargs)
            raise RuntimeError("retry exhausted")

        return _wrapper

    return _decorator


def retry(cfg: RetryConfig) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Return a decorator that wraps sync callables with a shared retry policy."""

    def _decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            retrying = Retrying(
                stop=stop_after_attempt(max(1, cfg.stop_after)),
                wait=_wait_strategy(cfg),
                retry=retry_if_exception_type(cfg.retry_on),
                reraise=True,
                before_sleep=lambda state: _before_sleep(cfg, state),
            )
            for attempt in retrying:
                with attempt:
                    return func(*args, **kwargs)
            raise RuntimeError("retry exhausted")

        return _wrapper

    return _decorator


__all__ = ["RetryConfig", "aretry", "retry"]
