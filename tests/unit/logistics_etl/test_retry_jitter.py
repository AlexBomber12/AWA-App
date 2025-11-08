from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest


@pytest.mark.anyio
async def test_download_with_retries_logs_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.logistics_etl import client

    attempts = {"count": 0}
    request = httpx.Request("GET", "https://example.com")

    async def flaky_once(url: str, timeout_s: int):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise httpx.HTTPStatusError("boom", request=request, response=httpx.Response(500, request=request))
        return b"ok", {"content_type": "text/csv"}

    monkeypatch.setattr(client, "_download_once", flaky_once, raising=False)

    monkeypatch.setattr(
        client,
        "Settings",
        lambda: SimpleNamespace(
            ETL_RETRY_ATTEMPTS=3,
            ETL_RETRY_BASE_S=0.01,
            ETL_RETRY_MIN_S=0.01,
            ETL_RETRY_MAX_S=0.02,
            ETL_RETRY_JITTER_S=0.0,
        ),
        raising=False,
    )

    logs: list[tuple[str, tuple, dict]] = []

    monkeypatch.setattr(
        client,
        "logger",
        SimpleNamespace(
            warning=lambda msg, *args, **kwargs: logs.append((msg, args, kwargs)),
            exception=lambda *args, **kwargs: None,
        ),
        raising=False,
    )

    body, meta = await client._download_with_retries("https://example.com", timeout_s=1, retries=1)

    assert body == b"ok"
    assert meta["content_type"] == "text/csv"
    assert any("Retrying download" in entry[0] for entry in logs)
