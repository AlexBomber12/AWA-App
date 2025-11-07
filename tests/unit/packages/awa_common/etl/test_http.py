from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import respx

from awa_common.etl import http


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)


def test_request_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(http.metrics, "record_etl_retry", lambda source, code: calls.append((source, code)))

    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/fees")
        route.mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        response = http.request("GET", "https://example.com/fees", source="etl", task_id="task-1")

    assert response.status_code == 200
    assert route.call_count == 2
    assert ("etl", "429") in calls


def test_request_recovers_from_multiple_500(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(http.metrics, "record_etl_retry", lambda source, code: calls.append((source, code)))

    with respx.mock(base_url="https://api.example.com") as mock:
        route = mock.get("/data")
        route.mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(500),
                httpx.Response(200, json={"value": 42}),
            ]
        )
        response = http.request("GET", "https://api.example.com/data", source="etl", task_id="task-2")

    assert response.json() == {"value": 42}
    assert route.call_count == 3
    assert calls.count(("etl", "500")) == 2


def test_request_handles_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(http.metrics, "record_etl_retry", lambda source, code: calls.append((source, code)))

    with respx.mock(base_url="https://net.example.com") as mock:
        route = mock.get("/data")

        def _side_effect(request: httpx.Request) -> httpx.Response:
            if route.call_count == 0:
                raise httpx.ConnectError("boom", request=request)
            return httpx.Response(200, json={"status": "ok"})

        route.mock(side_effect=_side_effect)
        response = http.request("GET", "https://net.example.com/data", source="etl", task_id="task-3")

    assert response.status_code == 200
    assert ("etl", "ConnectError") in calls


def test_request_raises_contextual_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http.metrics, "record_etl_retry", lambda *_args, **_kwargs: None)
    with respx.mock(base_url="https://fail.example.com") as mock:
        mock.get("/down").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(503),
                httpx.Response(503),
            ]
        )
        with pytest.raises(http.ETLHTTPError) as exc:
            http.request("GET", "https://fail.example.com/down", source="etl", task_id="task-4")
    error = exc.value
    assert error.source == "etl"
    assert error.task_id == "task-4"


def test_download_removes_partial_file_on_failure(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "payload.bin"
    dest.write_bytes(b"stale")

    def boom(*_args, **_kwargs):
        raise http.ETLHTTPError("boom", source="etl", url="https://files", task_id=None)

    monkeypatch.setattr(http, "_run_with_retries", boom)

    with pytest.raises(http.ETLHTTPError):
        http.download("https://files/data", dest_path=dest, source="etl")
    assert not dest.exists()


def test_retry_wait_honours_retry_after_header() -> None:
    response = httpx.Response(
        429,
        headers={"Retry-After": "5"},
        request=httpx.Request("GET", "https://example.com"),
    )
    exc = http.RetryableHTTPStatusError(response, retry_after=5.0)
    state = SimpleNamespace(
        outcome=SimpleNamespace(failed=True, exception=lambda: exc),
        next_action=SimpleNamespace(sleep=0.1),
    )
    wait = http._RetryWait(multiplier=0.01, max=10.0)
    assert wait(state) == 5.0
