from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Iterable
from typing import Any

import structlog

from .errors import LLMBinaryNonZeroExitError, LLMBinaryOSFailure, LLMBinaryTimeoutError

logger = structlog.get_logger(__name__).bind(component="llm_bin")

_STDERR_MAX_BYTES = 2048
_READ_CHUNK_SIZE = 2048


async def _drain_stream(stream: asyncio.StreamReader, limit: int) -> tuple[bytes, bool]:
    collected: list[bytes] = []
    stored = 0
    truncated = False
    while True:
        chunk = await stream.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        available = max(limit - stored, 0)
        if available > 0:
            take = min(len(chunk), available)
            collected.append(chunk[:take])
            stored += take
        if stored >= limit and len(chunk) > available:
            truncated = True
    return b"".join(collected), truncated


def _decode_payload(payload: bytes, *, truncated: bool, max_bytes: int) -> str:
    if len(payload) > max_bytes:
        payload = payload[:max_bytes]
        truncated = True
    text = payload.decode("utf-8", errors="replace")
    return f"{text} [truncated]" if truncated else text


async def _collect_output(
    proc: asyncio.subprocess.Process, *, stdout_limit: int, stderr_limit: int
) -> tuple[bytes, bool, bytes, bool]:
    assert proc.stdout is not None
    assert proc.stderr is not None
    stdout_task = asyncio.create_task(_drain_stream(proc.stdout, stdout_limit))
    stderr_task = asyncio.create_task(_drain_stream(proc.stderr, stderr_limit))
    await proc.wait()
    stdout, stdout_truncated = await stdout_task
    stderr, stderr_truncated = await stderr_task
    return stdout, stdout_truncated, stderr, stderr_truncated


async def run_llm_binary(
    command: Iterable[str],
    *,
    timeout_s: float,
    max_output_bytes: int,
    log_context: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    """Execute the local LLM binary with bounded output and timeout."""

    cmd = list(command)
    bin_name = cmd[0] if cmd else "<unknown>"
    ctx = dict(log_context or {})
    ctx.setdefault("bin", bin_name)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        logger.warning(
            "llm.bin.spawn_failed",
            error=str(exc),
            error_type=exc.__class__.__name__,
            **ctx,
        )
        raise LLMBinaryOSFailure(str(exc)) from exc

    try:
        stdout, stdout_truncated, stderr, stderr_truncated = await asyncio.wait_for(
            _collect_output(proc, stdout_limit=max_output_bytes, stderr_limit=min(_STDERR_MAX_BYTES, max_output_bytes)),
            timeout=timeout_s,
        )
    except TimeoutError as exc:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
        with contextlib.suppress(Exception):
            await proc.communicate()
        logger.warning(
            "llm.bin.timeout",
            timeout_s=timeout_s,
            **ctx,
        )
        raise LLMBinaryTimeoutError(timeout_s=timeout_s) from exc

    exit_code = proc.returncode
    stderr_text = _decode_payload(stderr, truncated=stderr_truncated, max_bytes=_STDERR_MAX_BYTES)
    if exit_code:
        logger.warning(
            "llm.bin.non_zero_exit",
            exit_code=exit_code,
            stderr=stderr_text,
            **ctx,
        )
        raise LLMBinaryNonZeroExitError(exit_code=exit_code, stderr=stderr_text)

    output = _decode_payload(stdout, truncated=stdout_truncated, max_bytes=max_output_bytes)
    logger.info(
        "llm.bin.completed",
        truncated=stdout_truncated,
        output_bytes=len(output.encode("utf-8", errors="replace")),
        **ctx,
    )
    return output, stdout_truncated
