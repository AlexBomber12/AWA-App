import sys

import pytest

from services.llm_server.bin_runner import run_llm_binary
from services.llm_server.errors import LLMBinaryNonZeroExitError, LLMBinaryOSFailure, LLMBinaryTimeoutError


@pytest.mark.asyncio
async def test_run_llm_binary_success() -> None:
    output, truncated = await run_llm_binary(
        [sys.executable, "-c", "import sys; sys.stdout.write('hello')"],
        timeout_s=2.0,
        max_output_bytes=1024,
    )
    assert output == "hello"
    assert truncated is False


@pytest.mark.asyncio
async def test_run_llm_binary_timeout() -> None:
    with pytest.raises(LLMBinaryTimeoutError):
        await run_llm_binary(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            timeout_s=0.1,
            max_output_bytes=1024,
        )


@pytest.mark.asyncio
async def test_run_llm_binary_non_zero_exit() -> None:
    with pytest.raises(LLMBinaryNonZeroExitError):
        await run_llm_binary(
            [sys.executable, "-c", "import sys; sys.stderr.write('fail'); sys.exit(1)"],
            timeout_s=2.0,
            max_output_bytes=1024,
        )


@pytest.mark.asyncio
async def test_run_llm_binary_truncates_output() -> None:
    output, truncated = await run_llm_binary(
        [sys.executable, "-c", "import sys; sys.stdout.write('x'*5000)"],
        timeout_s=2.0,
        max_output_bytes=1000,
    )
    assert truncated is True
    assert output.endswith("[truncated]")
    assert len(output) < 1200


def test_decode_payload_truncates(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.llm_server import bin_runner

    text = bin_runner._decode_payload(b"a" * 10, truncated=False, max_bytes=5)
    assert text.endswith("[truncated]")


@pytest.mark.asyncio
async def test_run_llm_binary_oserror() -> None:
    with pytest.raises(LLMBinaryOSFailure):
        await run_llm_binary(["/nonexistent/binary"], timeout_s=0.1, max_output_bytes=10)
